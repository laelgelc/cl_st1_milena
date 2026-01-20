import os
import json
import time
import random
import logging
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
GECKODRIVER_PATH = '/home/ubuntu/geckodriver/geckodriver'

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
    service = Service(executable_path=GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver

def handle_consent(driver):
    try:
        # Wait a moment for any potential overlays
        time.sleep(2)
        tos_prompt = driver.find_elements(By.ID, 'tos_prompt')
        if tos_prompt and tos_prompt[0].is_displayed():
            logging.info("Consent prompt detected. Accepting terms...")
            driver.find_element(By.ID, 'tos_agree').click()
            driver.find_element(By.ID, 'data_processing_agree').click()
            driver.find_element(By.ID, 'accept_tos').click()
            # Wait for overlay to fade out
            WebDriverWait(driver, 10).until(EC.invisibility_of_element((By.ID, 'tos_prompt')))
    except Exception as e:
        logging.warning(f"Error handling consent: {e}")

def scrape_page_content(html, year):
    soup = BeautifulSoup(html, 'lxml')
    works_data = []

    ol_tag = soup.find('ol', class_='work index group')
    if not ol_tag:
        return works_data

    for li in ol_tag.find_all('li', class_='work blurb'):
        try:
            # Fandom Filter (Strict)
            fandom_tags = li.find('h5', class_='fandoms').find_all('a', class_='tag')
            fandom_names = [t.get_text(strip=True) for t in fandom_tags]
            if len(fandom_names) != 1 or fandom_names[0] != 'Original Work':
                continue # Skip crossovers

            # Extraction
            title_tag = li.find('h4', class_='heading').find('a', recursive=False)
            author_tag = li.find('a', rel='author')

            # Helper to get dd stats
            def get_stat(class_name):
                tag = li.find('dd', class_=class_name)
                return tag.get_text(strip=True) if tag else None

            work = {
                'Year': year,
                'Title': title_tag.get_text(strip=True) if title_tag else "Anonymous",
                'Author': author_tag.get_text(strip=True) if author_tag else "Anonymous",
                'Fandom': ", ".join(fandom_names),
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
            logging.error(f"Error extracting metadata from list item: {e}")

    return works_data

def process_lists(test_mode=True):
    with open(INPUT_JSON, 'r') as f:
        year_configs = json.load(f)

    driver = setup_driver()
    all_metadata = []

    try:
        for config in year_configs:
            year = config['year']
            base_url = config['list_url']
            end_page = 5 if test_mode else config['end_page']

            year_dir = os.path.join(LISTS_DIR, str(year))
            os.makedirs(year_dir, exist_ok=True)

            logging.info(f"Starting Year {year} (Target: {end_page} pages)")

            for page_num in range(1, end_page + 1):
                file_name = f"{year}_{str(page_num).zfill(4)}.html"
                file_path = os.path.join(year_dir, file_name)

                # Checkpoint: Skip if exists and not empty
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logging.info(f"Skipping {file_name} (already exists)")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_metadata.extend(scrape_page_content(f.read(), year))
                    continue

                # Navigate and Scrape
                url = f"{base_url}{page_num}"
                logging.info(f"Fetching: {url}")
                driver.get(url)

                # Check for Consent on first load or periodically
                handle_consent(driver)

                # Wait for content
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'work')))

                # Capture and Save HTML
                page_source = driver.page_source
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)

                # Extract metadata
                all_metadata.extend(scrape_page_content(page_source, year))

                # Polite Throttling
                time.sleep(random.uniform(3, 6))

                # Batch restart logic (prevent memory leaks every 50 pages)
                if page_num % 50 == 0:
                    logging.info("Restarting WebDriver session to maintain stability...")
                    driver.quit()
                    driver = setup_driver()

    finally:
        driver.quit()

    # Save Results
    if all_metadata:
        df = pd.DataFrame(all_metadata)
        df.to_json(JSONL_OUT, orient='records', lines=True)
        df.to_excel(EXCEL_OUT, index=False)
        logging.info(f"Successfully saved {len(all_metadata)} records to JSONL and Excel.")

if __name__ == "__main__":
    # Change to False for full production run
    process_lists(test_mode=True)