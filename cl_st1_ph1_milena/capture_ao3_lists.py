import os
import json
import time
import random
import logging
import argparse
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
INPUT_JSON = 'ao3_original_work_lists.json'
OUTPUT_ROOT = 'corpus/00_sources'
LISTS_DIR = os.path.join(OUTPUT_ROOT, '00_lists')
JSONL_OUT = os.path.join(OUTPUT_ROOT, 'lists.jsonl')
EXCEL_OUT = os.path.join(OUTPUT_ROOT, 'lists.xlsx')
LOG_FILE = 'capture_ao3_lists.log'

def setup_driver(username='ubuntu'):
    """Initializes a headless Firefox WebDriver with custom settings."""
    options = Options()
    options.add_argument('--headless')
    # Set custom User-Agent to ensure desktop rendering
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0")

    geckodriver_path = f'/home/{username}/geckodriver/geckodriver'
    service = Service(executable_path=geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver

def handle_consent(driver):
    """Detects and clicks the AO3 Terms of Service consent prompt if present."""
    try:
        # Brief pause to allow JavaScript overlays to trigger
        time.sleep(2)
        tos_prompt = driver.find_elements(By.ID, 'tos_prompt')
        if tos_prompt and tos_prompt[0].is_displayed():
            logging.info("Consent prompt detected. Accepting AO3 Terms...")
            driver.find_element(By.ID, 'tos_agree').click()
            driver.find_element(By.ID, 'data_processing_agree').click()
            driver.find_element(By.ID, 'accept_tos').click()
            # Wait for the prompt to disappear
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'tos_prompt')))
            logging.info("Terms accepted successfully.")
    except Exception as e:
        logging.warning(f"Note: Consent handling logic did not find/click prompt (may already be accepted): {e}")

def scrape_page_content(html, year):
    """Parses AO3 list HTML and extracts metadata for work entries."""
    soup = BeautifulSoup(html, 'lxml')
    works_data = []

    ol_tag = soup.find('ol', class_='work index group')
    if not ol_tag:
        return works_data

    for li in ol_tag.find_all('li', class_='work blurb'):
        try:
            # Strict Fandom Filter: Exclude if more than one fandom or not 'Original Work'
            fandom_tags = li.find('h5', class_='fandoms').find_all('a', class_='tag')
            fandom_names = [t.get_text(strip=True) for t in fandom_tags]
            if len(fandom_names) != 1 or fandom_names[0] != 'Original Work':
                continue

                # Primary Metadata
            title_tag = li.find('h4', class_='heading').find('a', recursive=False)
            author_tag = li.find('a', rel='author')

            # Helper to safely extract stats from <dd> tags
            def get_stat(class_name):
                tag = li.find('dd', class_=class_name)
                return tag.get_text(strip=True) if tag else "0"

            work = {
                'Year': year,
                'Title': title_tag.get_text(strip=True) if title_tag else "Anonymous",
                'Author': author_tag.get_text(strip=True) if author_tag else "Anonymous",
                'Fandom': fandom_names[0],
                'Date_Updated': li.find('p', class_='datetime').get_text(strip=True),
                'Language': get_stat('language'),
                'Words': get_stat('words'),
                'Chapters': get_stat('chapters'),
                'Collections': get_stat('collections'),
                'Comments': get_stat('comments'),
                'Kudos': get_stat('kudos'),
                'Bookmarks': get_stat('bookmarks'),
                'Hits': get_stat('hits'),
                'URL': f"https://archiveofourown.org{title_tag['href']}?view_adult=true&view_full_work=true"
            }
            works_data.append(work)
        except Exception as e:
            logging.error(f"Error parsing metadata for an entry in year {year}: {e}")

    return works_data

def main():
    parser = argparse.ArgumentParser(description="Capture AO3 work lists and extract metadata.")
    parser.add_argument('--test', '-t', action='store_true', help="Run in test mode (limited pages)")
    parser.add_argument('--pages', '-p', type=int, default=5, help="Pages to capture per year in test mode (default: 5)")
    parser.add_argument('--user', '-u', type=str, default='ubuntu', help="System username for geckodriver path (default: ubuntu)")
    args = parser.parse_args()

    # Logging Setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
    )

    if not os.path.exists(INPUT_JSON):
        logging.error(f"Input file {INPUT_JSON} not found. Execution aborted.")
        return

    with open(INPUT_JSON, 'r') as f:
        year_configs = json.load(f)

    driver = setup_driver(username=args.user)
    all_metadata = []

    try:
        for config in year_configs:
            year = config['year']
            base_url = config['list_url']
            end_page = args.pages if args.test else config['end_page']

            year_dir = os.path.join(LISTS_DIR, str(year))
            os.makedirs(year_dir, exist_ok=True)

            logging.info(f">>> Processing Year {year} (Total Pages: {end_page})")

            for page_num in range(1, end_page + 1):
                file_name = f"{year}_{str(page_num).zfill(4)}.html"
                file_path = os.path.join(year_dir, file_name)

                # Checkpoint: Resume logic
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logging.info(f"Skipping download for {file_name} (already exists). Parsing existing file...")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_metadata.extend(scrape_page_content(f.read(), year))
                    continue

                # Browser Action
                url = f"{base_url}{page_num}"
                logging.info(f"Fetching Page {page_num}: {url}")
                driver.get(url)

                # Check for Consent on every page (in case cookie is cleared)
                handle_consent(driver)

                # Explicit Wait for content to render
                try:
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'work')))
                except Exception:
                    logging.error(f"Timeout or 429 error potentially hit on page {page_num}. Check AO3 status.")
                    break

                # Save Source
                page_source = driver.page_source
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)

                # Extract and aggregate metadata
                page_works = scrape_page_content(page_source, year)
                all_metadata.extend(page_works)
                logging.info(f"Captured {len(page_works)} valid Original Works from page {page_num}.")

                # Polite Throttling: Human-like delay
                time.sleep(random.uniform(3.5, 7.0))

                # Periodic Session Refresh: Prevent Firefox memory bloat
                if page_num % 50 == 0:
                    logging.info("Restarting browser session for stability...")
                    driver.quit()
                    driver = setup_driver(username=args.user)

    except Exception as e:
        logging.critical(f"Critical error during execution: {e}")
    finally:
        driver.quit()

    # Save aggregated data to JSONL and Excel
    if all_metadata:
        os.makedirs(OUTPUT_ROOT, exist_ok=True)
        df = pd.DataFrame(all_metadata)
        df.to_json(JSONL_OUT, orient='records', lines=True)
        df.to_excel(EXCEL_OUT, index=False)
        logging.info(f"SUCCESS: Captured {len(all_metadata)} total records.")
        logging.info(f"Files saved: {JSONL_OUT} and {EXCEL_OUT}")
    else:
        logging.warning("No data was captured. Check logs for errors.")

if __name__ == "__main__":
    main()