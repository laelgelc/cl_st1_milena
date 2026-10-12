"""
Capture a web page with Selenium and save both its rendered HTML and extracted text.

This utility opens a URL in a real browser, waits for the page to load, saves the
rendered HTML to ``<file_id>.html``, and extracts readable text from common content
elements such as headings, paragraphs, unordered lists, and ordered lists into
``<file_id>.txt``.

By default, the programme uses Chrome in headless mode. Firefox can be selected
with the ``--browser`` option. Selenium Manager is used automatically by Selenium
to locate, download, and cache the appropriate browser driver, so no explicit
driver path is required.

Usage:
    python getwebpageselenium.py FILE_ID URL
    python getwebpageselenium.py FILE_ID URL --browser firefox
    python getwebpageselenium.py FILE_ID URL --timeout 45

Examples:
    python getwebpageselenium.py wwf_index_sample "https://www.worldwildlife.org/stories?page=1&threat_id=effects-of-climate-change"
    python getwebpageselenium.py example_page "https://example.com" --browser firefox
"""

import argparse
import time

import validators
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_driver(browser):
    """Create a headless Selenium WebDriver for the requested browser."""

    if browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=options)

    if browser == "firefox":
        options = FirefoxOptions()
        options.add_argument("--headless")
        return webdriver.Firefox(options=options)

    raise ValueError(f"Unsupported browser: {browser}")


def wait_for_page_load(driver, timeout=30, stable_period=2, poll_frequency=0.5):
    """
    Wait until the page appears loaded and stable.

    The checks are deliberately generic:
    1. Wait for the browser to report document.readyState == "complete".
    2. Wait for the body element to be present.
    3. Wait for the page URL and DOM size to remain unchanged for a short period.

    This is not a guarantee that every asynchronous request has finished, because
    modern pages may continue updating indefinitely, but it is more reliable than
    checking only for body presence or sleeping for a fixed duration.
    """

    wait = WebDriverWait(driver, timeout)
    wait.until(lambda current_driver: current_driver.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    deadline = time.monotonic() + timeout
    stable_since = None
    previous_state = None

    while time.monotonic() < deadline:
        current_state = driver.execute_script(
            """
            return {
                url: window.location.href,
                bodyTextLength: document.body ? document.body.innerText.length : 0,
                htmlLength: document.documentElement ? document.documentElement.outerHTML.length : 0
            };
            """
        )

        if current_state == previous_state:
            if stable_since is None:
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= stable_period:
                return
        else:
            stable_since = None
            previous_state = current_state

        time.sleep(poll_frequency)

    raise TimeoutException("Timed out waiting for the page to become stable.")


def main(file_id, url, browser="chrome", timeout=30):
    """Fetch a web page, save rendered HTML, and extract selected text content."""

    if not validators.url(url):
        print("Invalid URL. Please provide a valid URL.")
        return

    driver = create_driver(browser)

    try:
        driver.get(url)

        try:
            wait_for_page_load(driver, timeout=timeout)
        except TimeoutException as error:
            print(f"Warning: {error} Continuing with the current page state.")

        page_source = driver.page_source

        html_file_path = f"{file_id}.html"
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(page_source)
        print(f"Successfully saved HTML to {html_file_path}")

        soup = BeautifulSoup(page_source, "lxml")
        text_content = [
            tag.get_text(strip=True)
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol"])
        ]

        text_file_path = f"{file_id}.txt"
        with open(text_file_path, "w", encoding="utf-8") as text_file:
            text_file.write("\n".join(text_content))
        print(f"Successfully saved extracted text to {text_file_path}")

    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Capture a rendered web page with Selenium, save its HTML, "
            "and extract text from headings, paragraphs, and lists."
        )
    )
    parser.add_argument("file_id", type=str, help="Output filename prefix, without extension.")
    parser.add_argument("url", type=str, help="Web page URL to capture.")
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default="chrome",
        help="Browser to use for capture. Defaults to chrome.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Maximum number of seconds to wait for page load and stability. Defaults to 30.",
    )

    args = parser.parse_args()
    main(args.file_id, args.url, browser=args.browser, timeout=args.timeout)