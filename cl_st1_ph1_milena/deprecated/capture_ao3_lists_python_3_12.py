import os
import json
import time
import random
import logging
import argparse
import sys
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
INPUT_JSON = "ao3_original_work_lists.json"
OUTPUT_ROOT = "corpus/00_sources"
LISTS_DIR = os.path.join(OUTPUT_ROOT, "00_lists")
JSONL_OUT = os.path.join(OUTPUT_ROOT, "lists.jsonl")
EXCEL_OUT = os.path.join(OUTPUT_ROOT, "lists.xlsx")
LOG_FILE = "capture_ao3_lists.log"
DEBUG_DIR = "debug"

# Selenium / runtime safety
PAGE_LOAD_TIMEOUT_S_DEFAULT = 120
SCRIPT_TIMEOUT_S = 60
WAIT_FOR_WORKS_S = 20

# Polite throttling
SLEEP_MIN_S = 3.5
SLEEP_MAX_S = 6.5

# Recycle browser session periodically (helps long runs)
RECYCLE_EVERY_N_PAGES = 50


def setup_driver(username: str = "ubuntu", page_load_timeout_s: int = PAGE_LOAD_TIMEOUT_S_DEFAULT) -> webdriver.Firefox:
    """Initializes a headless Firefox WebDriver with custom settings."""
    options = Options()
    options.add_argument("--headless")

    # Ensure desktop rendering (AO3 can be picky with bot-like UAs)
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    )

    # Reduce some long-hang cases (network stalls etc.)
    options.set_preference("network.http.response.timeout", 120)
    options.set_preference("network.dns.disableIPv6", True)

    geckodriver_path = f"/home/{username}/geckodriver/geckodriver"
    service = Service(executable_path=geckodriver_path)

    driver = webdriver.Firefox(service=service, options=options)
    driver.set_window_size(1920, 1080)

    # Hard timeouts to reduce “infinite hang” scenarios
    driver.set_page_load_timeout(page_load_timeout_s)
    driver.set_script_timeout(SCRIPT_TIMEOUT_S)

    return driver


def handle_consent(driver: webdriver.Firefox) -> None:
    """Detects and clicks the AO3 Terms of Service consent prompt if present."""
    try:
        # Brief pause to allow overlays to trigger
        time.sleep(2)
        tos_prompt = driver.find_elements(By.ID, "tos_prompt")
        if tos_prompt and tos_prompt[0].is_displayed():
            logging.info("Consent prompt detected. Accepting AO3 Terms...")
            driver.find_element(By.ID, "tos_agree").click()
            driver.find_element(By.ID, "data_processing_agree").click()
            driver.find_element(By.ID, "accept_tos").click()
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "tos_prompt")))
            logging.info("Terms accepted successfully.")
    except Exception:
        # Prompt may already be accepted or not present (or AO3 changed markup)
        pass


def dump_debug_artifacts(driver: webdriver.Firefox, *, year: int, page_num: int, stage: str) -> None:
    """Best-effort debug dump (HTML + screenshot) to diagnose EC2-only failures."""
    try:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        prefix = f"{DEBUG_DIR}/year{year}_page{page_num:04d}_{stage}_{ts}"
        try:
            driver.save_screenshot(f"{prefix}.png")
        except Exception:
            pass
        try:
            with open(f"{prefix}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source or "")
        except Exception:
            pass
        logging.info(f"Saved debug artifacts: {prefix}.(html/png)")
    except Exception:
        pass


def safe_get(
        driver: webdriver.Firefox,
        url: str,
        *,
        year: int,
        page_num: int,
        attempts: int = 3,
) -> bool:
    """
    Navigate with retries/backoff.
    EC2 can experience intermittent slow loads / throttling; this makes the run robust.
    """
    for attempt in range(1, attempts + 1):
        try:
            driver.get(url)
            return True
        except TimeoutException:
            logging.warning(
                f"Navigation timed out (attempt {attempt}/{attempts}) for year={year}, page={page_num}, url={url}"
            )
            # Stop loading so we can retry without a stuck tab
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
        except WebDriverException:
            logging.exception(
                f"WebDriver error during navigation (attempt {attempt}/{attempts}) "
                f"for year={year}, page={page_num}, url={url}"
            )

        if attempt < attempts:
            backoff_s = 10 * attempt + random.uniform(0, 3)
            logging.info(f"Retrying after {backoff_s:.1f}s...")
            time.sleep(backoff_s)

    dump_debug_artifacts(driver, year=year, page_num=page_num, stage="nav_failed")
    return False


def scrape_page_content(html: str, year: int):
    """Parses AO3 list HTML and extracts metadata for work entries."""
    soup = BeautifulSoup(html, "lxml")
    works_data = []

    ol_tag = soup.find("ol", class_="work index group")
    if not ol_tag:
        return works_data, False

    # Pagination “Next”
    next_button = soup.find("li", class_="next")
    has_next = next_button is not None and next_button.find("a") is not None

    for li in ol_tag.select("li.work"):
        try:
            fandom_h5 = li.find("h5", class_="fandoms")
            if not fandom_h5:
                continue

            fandom_tags = fandom_h5.find_all("a", class_="tag")
            fandom_names = [t.get_text(strip=True) for t in fandom_tags]

            # Strict filter: only exactly one fandom and it must be “Original Work”
            if len(fandom_names) != 1 or fandom_names[0] != "Original Work":
                continue

            title_tag = li.find("h4", class_="heading").find("a", recursive=False)
            author_tag = li.find("a", rel="author")

            def get_stat(class_name: str) -> str:
                tag = li.find("dd", class_=class_name)
                return tag.get_text(strip=True) if tag else "0"

            datetime_tag = li.find("p", class_="datetime")

            if title_tag and title_tag.get("href"):
                url = f"https://archiveofourown.org{title_tag['href']}?view_adult=true&view_full_work=true"
            else:
                url = ""

            work = {
                "Year": year,
                "Title": title_tag.get_text(strip=True) if title_tag else "Anonymous",
                "Author": author_tag.get_text(strip=True) if author_tag else "Anonymous",
                "Fandom": fandom_names[0],
                "Date_Updated": datetime_tag.get_text(strip=True) if datetime_tag else "",
                "Language": get_stat("language"),
                "Words": get_stat("words"),
                "Chapters": get_stat("chapters"),
                "Collections": get_stat("collections"),
                "Comments": get_stat("comments"),
                "Kudos": get_stat("kudos"),
                "Bookmarks": get_stat("bookmarks"),
                "Hits": get_stat("hits"),
                "URL": url,
            }
            works_data.append(work)
        except Exception:
            # Keep going: one malformed work item shouldn’t break the whole page
            pass

    return works_data, has_next


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture AO3 work lists and extract metadata.")
    parser.add_argument("--test", "-t", action="store_true", help="Run in test mode (limited pages)")
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=5,
        help="Pages to capture per year in test mode (default: 5)",
    )
    parser.add_argument(
        "--user",
        "-u",
        type=str,
        default="ubuntu",
        help="System username for geckodriver path (default: ubuntu)",
    )
    parser.add_argument(
        "--page-load-timeout",
        type=int,
        default=PAGE_LOAD_TIMEOUT_S_DEFAULT,
        help=f"Selenium page load timeout (seconds, default: {PAGE_LOAD_TIMEOUT_S_DEFAULT})",
    )
    parser.add_argument(
        "--nav-attempts",
        type=int,
        default=3,
        help="Retries for driver.get() navigation timeouts (default: 3)",
    )
    args = parser.parse_args()

    # Logging Setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    )

    if not os.path.exists(INPUT_JSON):
        logging.error(f"Input file {INPUT_JSON} not found.")
        sys.exit(2)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        year_configs = json.load(f)

    driver = setup_driver(username=args.user, page_load_timeout_s=args.page_load_timeout)
    all_metadata = []

    try:
        for config in year_configs:
            year = config["year"]
            base_url = config["list_url"]

            start_page = config.get("start_page", 1)
            end_page = args.pages if args.test else config["end_page"]

            year_dir = os.path.join(LISTS_DIR, str(year))
            os.makedirs(year_dir, exist_ok=True)

            logging.info(f">>> Processing Year {year} (Range: {start_page} to {end_page})")

            for page_num in range(start_page, end_page + 1):
                file_name = f"{year}_{str(page_num).zfill(4)}.html"
                file_path = os.path.join(year_dir, file_name)

                # Checkpointing: if file exists and is non-empty, parse it and keep going
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logging.info(f"Skipping {file_name} (exists). Parsing content...")
                    with open(file_path, "r", encoding="utf-8") as f:
                        works, has_next = scrape_page_content(f.read(), year)
                        all_metadata.extend(works)

                    if not has_next:
                        logging.info(f"End of results reached at page {page_num} (no 'Next' button).")
                        break
                    continue

                url = f"{base_url}{page_num}"
                logging.info(f"Fetching Page {page_num}: {url}")

                ok = safe_get(
                    driver,
                    url,
                    year=year,
                    page_num=page_num,
                    attempts=args.nav_attempts,
                )
                if not ok:
                    logging.error(f"driver.get() failed for page {page_num}. Stopping year {year}.")
                    break

                handle_consent(driver)

                try:
                    WebDriverWait(driver, WAIT_FOR_WORKS_S).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "work"))
                    )
                except Exception:
                    logging.error(f"Page {page_num} timed out or is empty. Stopping year {year}.")
                    dump_debug_artifacts(driver, year=year, page_num=page_num, stage="no_works_timeout")
                    break

                page_source = driver.page_source
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(page_source)

                page_works, has_next = scrape_page_content(page_source, year)
                all_metadata.extend(page_works)
                logging.info(f"Captured {len(page_works)} Original Works from page {page_num}.")

                if not has_next:
                    logging.info(f"Reached the definitive end of results for {year} at page {page_num}.")
                    break

                time.sleep(random.uniform(SLEEP_MIN_S, SLEEP_MAX_S))

                if page_num % RECYCLE_EVERY_N_PAGES == 0:
                    logging.info("Cycling browser session...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = setup_driver(username=args.user, page_load_timeout_s=args.page_load_timeout)

    except Exception:
        logging.exception("Critical Error")
        sys.exit(1)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    if not all_metadata:
        logging.error("No metadata collected; treating as failure.")
        sys.exit(1)

    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    df = pd.DataFrame(all_metadata)

    # Drop duplicates based on URL
    if "URL" in df.columns:
        df = df.drop_duplicates(subset=["URL"])

    df.to_json(JSONL_OUT, orient="records", lines=True)
    df.to_excel(EXCEL_OUT, index=False)
    logging.info(f"SUCCESS: {len(df)} total records saved.")


if __name__ == "__main__":
    main()