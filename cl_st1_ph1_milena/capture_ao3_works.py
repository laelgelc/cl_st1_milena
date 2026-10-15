"""
Capture AO3 work pages for Phase 1 corpus data collection.

This script reads an AO3 work collection plan from NDJSON and captures each
selected full-work page as a rendered HTML file using Selenium.

The work collection plan is produced upstream from the AO3 works metadata and
contains one JSON object per selected work. The required fields are work_id,
full_work_url, and date_updated. The programme uses full_work_url directly and
saves each captured HTML page under corpus/02_ao3_work_pages/<year>/<work_id>.html,
where year is derived from date_updated.

By default, the script runs in test mode and attempts only the first 5 planned
missing works. Existing HTML files are skipped unless --reprocess is provided,
making the script safe to re-run.

The script handles AO3's Terms of Service prompt when it appears, waits for
AO3 work-page content, saves rendered HTML, and records work-level validation
information in a JSON manifest.

Example:
    python capture_ao3_works.py

Full run:
    python capture_ao3_works.py --no-test-mode

Resume from a specific work:
    python capture_ao3_works.py --no-test-mode --start-work-id 85198816

The script writes an append-only log file and JSON manifests describing
run-level metadata and per-work capture status.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from selenium import webdriver
from selenium.common.exceptions import (
    JavascriptException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import ReadTimeoutError


TOOL_NAME = "capture_ao3_works.py"
TOOL_VERSION = "v1"

DEFAULT_COLLECTION_PLAN_PATH = "corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson"
DEFAULT_OUTPUT_DIR = "corpus/02_ao3_work_pages"
DEFAULT_LOG_FILE = "corpus/02_ao3_work_pages/capture_ao3_works.log"
DEFAULT_MANIFEST_FILE = "corpus/02_ao3_work_pages/capture_ao3_works_manifest.json"

DEFAULT_BROWSER = "chrome"
DEFAULT_HEADLESS = True
DEFAULT_CHROME_SERVER_FLAGS = True

DEFAULT_TEST_MODE = True
DEFAULT_TEST_LIMIT = 5
DEFAULT_WORKERS = 1

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_DELAY_SECONDS = 10.0

DEFAULT_REQUEST_DELAY_SECONDS = 3.0
DEFAULT_REQUEST_JITTER_SECONDS = 1.0

AO3_ALLOWED_HOSTS = {
    "archiveofourown.org",
    "www.archiveofourown.org",
    "ao3.org",
    "www.ao3.org",
    "archiveofourown.com",
    "www.archiveofourown.com",
    "archiveofourown.net",
    "www.archiveofourown.net",
    "archiveofourown.gay",
    "secure.archiveofourown.org",
    "insecure.archiveofourown.org",
}

AO3_WORK_MAIN_SELECTOR = "#main.works-show"
AO3_WORK_READY_SELECTOR = "#workskin"
AO3_WORK_CHAPTERS_SELECTOR = "#chapters"
AO3_WORK_CHAPTER_SELECTOR = "#chapters .chapter"
AO3_WORK_TITLE_SELECTOR = "h2.title.heading"
AO3_WORK_BYLINE_SELECTOR = "h3.byline.heading"
AO3_WORK_METADATA_SELECTOR = "dl.work.meta"

AO3_TOS_PROMPT_SELECTOR = "#tos_prompt"
AO3_TOS_CHECKBOX_SELECTOR = "#tos_agree"
AO3_DATA_PROCESSING_CHECKBOX_SELECTOR = "#data_processing_agree"
AO3_TOS_ACCEPT_BUTTON_SELECTOR = "#accept_tos"

DATE_UPDATED_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_WORK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

EXIT_SUCCESS = 0
EXIT_CAPTURE_FAILURE = 1
EXIT_CONFIGURATION_ERROR = 2
EXIT_INTERRUPTED = 130


class ConfigurationError(Exception):
    """Raised when command-line arguments or runtime configuration are invalid."""


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(UTC)


def utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def make_run_id() -> str:
    """Create a UTC run identifier safe for filenames."""
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the AO3 work capture programme.

    Returns:
        An argparse namespace containing command-line values. Semantic validation
        is performed separately by validate_args().
    """
    parser = argparse.ArgumentParser(
        description="Capture selected AO3 full-work pages as rendered HTML files using Selenium."
    )

    parser.add_argument(
        "--collection-plan",
        type=Path,
        default=Path(DEFAULT_COLLECTION_PLAN_PATH),
        help=f"Path to the NDJSON work collection plan. Default: {DEFAULT_COLLECTION_PLAN_PATH}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(DEFAULT_OUTPUT_DIR),
        help=f"Directory where captured HTML files are saved. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default=DEFAULT_BROWSER,
        help=f"Browser to use for capture. Default: {DEFAULT_BROWSER}",
    )
    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=DEFAULT_HEADLESS,
        help="Run browser in headless mode. This is the default.",
    )
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Run browser with a visible window.",
    )
    parser.add_argument(
        "--chrome-server-flags",
        dest="chrome_server_flags",
        action="store_true",
        default=DEFAULT_CHROME_SERVER_FLAGS,
        help="Use Chrome flags suitable for headless Linux/EC2. This is the default.",
    )
    parser.add_argument(
        "--no-chrome-server-flags",
        dest="chrome_server_flags",
        action="store_false",
        help="Disable Chrome server flags.",
    )
    parser.add_argument(
        "--test-mode",
        dest="test_mode",
        action="store_true",
        default=DEFAULT_TEST_MODE,
        help="Enable test mode. This is the default.",
    )
    parser.add_argument(
        "--no-test-mode",
        dest="test_mode",
        action="store_false",
        help="Disable test mode and process all planned captures.",
    )
    parser.add_argument(
        "--test-limit",
        type=int,
        default=DEFAULT_TEST_LIMIT,
        help=f"Maximum works to attempt in test mode. Default: {DEFAULT_TEST_LIMIT}",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Capture works even when output HTML files already exist.",
    )
    parser.add_argument(
        "--start-work-id",
        type=str,
        default=None,
        help="Optional work ID from which to start planning, e.g. 85198816.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path(DEFAULT_LOG_FILE),
        help=f"Append-only log file path. Default: {DEFAULT_LOG_FILE}",
    )
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=Path(DEFAULT_MANIFEST_FILE),
        help=f"Latest manifest file path. Default: {DEFAULT_MANIFEST_FILE}",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of workers. Current implementation requires 1. Default: {DEFAULT_WORKERS}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Maximum seconds to wait for one work. Default: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Retries after a failed capture. Default: {DEFAULT_MAX_RETRIES}",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY_SECONDS,
        help=f"Delay in seconds between failed attempts. Default: {DEFAULT_RETRY_DELAY_SECONDS}",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=DEFAULT_REQUEST_DELAY_SECONDS,
        help=f"Delay in seconds between work requests. Default: {DEFAULT_REQUEST_DELAY_SECONDS}",
    )
    parser.add_argument(
        "--request-jitter",
        type=float,
        default=DEFAULT_REQUEST_JITTER_SECONDS,
        help=f"Maximum random extra delay between requests. Default: {DEFAULT_REQUEST_JITTER_SECONDS}",
    )

    return parser.parse_args()


def setup_logging(log_file: Path) -> logging.Logger:
    """Configure append-only file logging and console logging.

    This function performs filesystem I/O.

    Args:
        log_file: Path where log messages should be appended.

    Returns:
        A configured logger for this programme.

    Raises:
        ConfigurationError: If the log directory cannot be created.
    """
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Could not create log directory {log_file.parent}: {exc}") from exc

    logger = logging.getLogger(TOOL_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments before processing.

    This function performs filesystem checks and creates required directories.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ConfigurationError: If an argument or path is invalid.
    """
    if not args.collection_plan.exists():
        raise ConfigurationError(f"Collection plan does not exist: {args.collection_plan}")
    if not args.collection_plan.is_file():
        raise ConfigurationError(f"Collection plan path is not a file: {args.collection_plan}")

    if args.test_limit <= 0:
        raise ConfigurationError("--test-limit must be greater than 0")
    if args.workers <= 0:
        raise ConfigurationError("--workers must be greater than 0")
    if args.workers != 1:
        raise ConfigurationError("Parallel execution is not implemented; please use --workers 1")
    if args.timeout <= 0:
        raise ConfigurationError("--timeout must be greater than 0")
    if args.max_retries < 0:
        raise ConfigurationError("--max-retries must be 0 or greater")
    if args.retry_delay < 0:
        raise ConfigurationError("--retry-delay must be 0 or greater")
    if args.request_delay < 0:
        raise ConfigurationError("--request-delay must be 0 or greater")
    if args.request_jitter < 0:
        raise ConfigurationError("--request-jitter must be 0 or greater")
    if args.start_work_id is not None and not args.start_work_id.strip():
        raise ConfigurationError("--start-work-id must not be empty when provided")

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Could not create required output directories: {exc}") from exc


def normalise_work_id(work_id: Any, line_number: int) -> str:
    """Normalise and validate a work ID from a plan record.

    Args:
        work_id: Raw work ID value from the NDJSON record.
        line_number: Source NDJSON line number for error reporting.

    Returns:
        A stripped string work ID.

    Raises:
        ConfigurationError: If the work ID is missing or unsafe for filenames.
    """
    if work_id is None:
        raise ConfigurationError(f"Line {line_number}: work_id is missing")

    clean_work_id = str(work_id).strip()
    if not clean_work_id:
        raise ConfigurationError(f"Line {line_number}: work_id must not be empty")
    if not SAFE_WORK_ID_PATTERN.fullmatch(clean_work_id):
        raise ConfigurationError(
            f"Line {line_number}: work_id contains unsafe filename characters: {clean_work_id!r}"
        )

    return clean_work_id


def derive_year_from_date_updated(date_updated: str) -> int:
    """Derive the four-digit year from an ISO-style date_updated value.

    Args:
        date_updated: Date string expected in YYYY-MM-DD format.

    Returns:
        Four-digit year as an integer.

    Raises:
        ConfigurationError: If the date is malformed or impossible.
    """
    if not isinstance(date_updated, str) or not date_updated.strip():
        raise ConfigurationError("date_updated must be a non-empty string")

    clean_date = date_updated.strip()
    if not DATE_UPDATED_PATTERN.fullmatch(clean_date):
        raise ConfigurationError(f"date_updated must use YYYY-MM-DD format: {date_updated!r}")

    try:
        parsed_date = datetime.strptime(clean_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ConfigurationError(f"date_updated is not a valid calendar date: {date_updated!r}") from exc

    return parsed_date.year


def validate_full_work_url(url: Any, line_number: int) -> str:
    """Validate and normalise an AO3 full-work URL.

    Args:
        url: Raw full_work_url value.
        line_number: Source NDJSON line number for error reporting.

    Returns:
        The stripped URL string.

    Raises:
        ConfigurationError: If the URL is missing or not an accepted AO3 work URL.
    """
    if not isinstance(url, str) or not url.strip():
        raise ConfigurationError(f"Line {line_number}: full_work_url must be a non-empty string")

    clean_url = url.strip()
    parsed_url = urlparse(clean_url)

    if parsed_url.scheme not in {"http", "https"}:
        raise ConfigurationError(f"Line {line_number}: full_work_url must be HTTP or HTTPS: {clean_url}")
    if parsed_url.netloc not in AO3_ALLOWED_HOSTS:
        raise ConfigurationError(f"Line {line_number}: full_work_url host is not an accepted AO3 host: {clean_url}")
    if not re.fullmatch(r"/works/\d+/?", parsed_url.path):
        raise ConfigurationError(f"Line {line_number}: full_work_url does not look like an AO3 work URL: {clean_url}")

    return clean_url


def make_output_path(output_dir: Path, work_id: str, date_updated: str) -> Path:
    """Create the target HTML path for a planned work.

    Args:
        output_dir: Base output directory.
        work_id: Normalised work ID.
        date_updated: ISO-style date string.

    Returns:
        Target HTML output path.

    Raises:
        ConfigurationError: If the year cannot be derived.
    """
    year = derive_year_from_date_updated(date_updated)
    return output_dir / str(year) / f"{work_id}.html"


def load_collection_plan(plan_path: Path) -> list[dict[str, Any]]:
    """Load and validate the AO3 work collection plan from NDJSON.

    This function performs file I/O.

    Args:
        plan_path: Path to the NDJSON work collection plan.

    Returns:
        Ordered list of validated work item dictionaries.

    Raises:
        ConfigurationError: If the file cannot be read, contains invalid NDJSON,
            misses required fields, contains duplicate work IDs, or has malformed
            values.
    """
    work_plan: list[dict[str, Any]] = []
    seen_work_ids: dict[str, int] = {}

    try:
        with plan_path.open("r", encoding="utf-8") as input_file:
            for line_number, line in enumerate(input_file, start=1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    record = json.loads(stripped_line)
                except json.JSONDecodeError as exc:
                    raise ConfigurationError(f"Line {line_number}: invalid JSON: {exc}") from exc

                if not isinstance(record, dict):
                    raise ConfigurationError(f"Line {line_number}: each NDJSON record must be a JSON object")

                for field in ["work_id", "full_work_url", "date_updated"]:
                    if field not in record:
                        raise ConfigurationError(f"Line {line_number}: missing required field {field!r}")

                work_id = normalise_work_id(record["work_id"], line_number)
                if work_id in seen_work_ids:
                    raise ConfigurationError(
                        "Duplicate work_id found: "
                        f"{work_id!r} first appears on line {seen_work_ids[work_id]}, "
                        f"again on line {line_number}"
                    )

                full_work_url = validate_full_work_url(record["full_work_url"], line_number)
                date_updated = str(record["date_updated"]).strip()
                year = derive_year_from_date_updated(date_updated)

                parsed_query = parse_qs(urlparse(full_work_url).query)
                url_warnings: list[str] = []
                if parsed_query.get("view_adult", [""])[0] != "true":
                    url_warnings.append("full_work_url does not include view_adult=true")
                if parsed_query.get("view_full_work", [""])[0] != "true":
                    url_warnings.append("full_work_url does not include view_full_work=true")

                clean_record = dict(record)
                clean_record["work_id"] = work_id
                clean_record["full_work_url"] = full_work_url
                clean_record["date_updated"] = date_updated
                clean_record["year"] = year
                clean_record["source_plan_line"] = line_number
                clean_record["url_warnings"] = url_warnings

                seen_work_ids[work_id] = line_number
                work_plan.append(clean_record)

    except OSError as exc:
        raise ConfigurationError(f"Could not read collection plan {plan_path}: {exc}") from exc

    if not work_plan:
        raise ConfigurationError(f"Collection plan is empty: {plan_path}")

    return work_plan


def make_manifest_metadata(work_item: dict[str, Any]) -> dict[str, Any]:
    """Create optional manifest metadata copied from the input plan.

    Args:
        work_item: Planned work metadata.

    Returns:
        A dictionary containing selected optional provenance fields.
    """
    optional_fields = [
        "title",
        "author_name",
        "work_url",
        "collection_year",
        "language",
        "words",
        "chapters_current",
        "chapters_total",
        "source_page_id",
        "source_html_path",
        "extraction_run_id",
        "url_warnings",
    ]

    metadata: dict[str, Any] = {}
    for field in optional_fields:
        if field in work_item:
            metadata[f"plan_{field}" if field in {"title", "author_name"} else field] = work_item[field]

    return metadata


def make_skipped_existing_result(work_item: dict[str, Any], output_path: Path) -> dict[str, Any]:
    """Create a manifest result for a work skipped because output already exists.

    Args:
        work_item: Planned work metadata.
        output_path: Existing output HTML path.

    Returns:
        A structured work-level manifest dictionary.
    """
    timestamp = utc_timestamp()
    return {
        "work_id": work_item["work_id"],
        "year": work_item["year"],
        "date_updated": work_item["date_updated"],
        "url": work_item["full_work_url"],
        "current_url": None,
        "output_path": str(output_path),
        "status": "skipped_existing",
        "error": None,
        "retries": 0,
        "duration_seconds": 0.0,
        "start_time": timestamp,
        "end_time": timestamp,
        "source_plan_line": work_item["source_plan_line"],
        "validation": {
            "title": None,
            "work_title": None,
            "byline": None,
            "workskin_detected": None,
            "chapters_detected": None,
            "chapter_count_detected": None,
            "work_metadata_detected": None,
            "tos_prompt_handled": False,
        },
        "metadata": make_manifest_metadata(work_item) | {
            "reason": "Output HTML file already exists and --reprocess was not provided",
        },
    }


def plan_captures(
        work_plan: list[dict[str, Any]],
        output_dir: Path,
        test_mode: bool,
        test_limit: int,
        reprocess: bool,
        start_work_id: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Create planned and skipped work capture records.

    This function performs filesystem checks but does not perform network I/O.

    Args:
        work_plan: Ordered list of validated work plan records.
        output_dir: Directory where captured HTML files are saved.
        test_mode: Whether to limit planned attempts.
        test_limit: Maximum planned attempts when test mode is active.
        reprocess: Whether existing HTML files should be re-captured.
        start_work_id: Optional work ID from which planning should start.

    Returns:
        A tuple containing planned capture records, skipped-existing result
        records, and total number of works in the full plan.

    Raises:
        ConfigurationError: If start_work_id is provided but not found.
    """
    total_works = len(work_plan)
    selected_works = work_plan

    if start_work_id is not None:
        clean_start_work_id = start_work_id.strip()
        start_index = next(
            (index for index, item in enumerate(work_plan) if item["work_id"] == clean_start_work_id),
            None,
        )
        if start_index is None:
            raise ConfigurationError(f"--start-work-id was not found in the collection plan: {clean_start_work_id}")
        selected_works = work_plan[start_index:]

    planned: list[dict[str, Any]] = []
    skipped_existing: list[dict[str, Any]] = []

    for work_item in selected_works:
        output_path = make_output_path(output_dir, work_item["work_id"], work_item["date_updated"])
        enriched_item = dict(work_item)
        enriched_item["output_path"] = output_path

        if output_path.exists() and not reprocess:
            skipped_existing.append(make_skipped_existing_result(enriched_item, output_path))
            continue

        planned.append(enriched_item)

    if test_mode:
        planned = planned[:test_limit]

    return planned, skipped_existing, total_works


def create_driver(browser: str, headless: bool, chrome_server_flags: bool, timeout: int) -> WebDriver:
    """Create a Selenium WebDriver for the requested browser.

    Args:
        browser: Browser name, either "chrome" or "firefox".
        headless: Whether to run in headless mode.
        chrome_server_flags: Whether to use Chrome options suitable for EC2.
        timeout: Base timeout in seconds from command-line configuration.

    Returns:
        A Selenium WebDriver instance.

    Raises:
        ConfigurationError: If the browser is unsupported or cannot be started.
    """
    try:
        if browser == "chrome":
            options = ChromeOptions()

            if headless:
                options.add_argument("--headless=new")

            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            if chrome_server_flags:
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout * 4)
            driver.set_script_timeout(timeout)
            return driver

        if browser == "firefox":
            options = FirefoxOptions()

            if headless:
                options.add_argument("--headless")

            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(timeout * 4)
            driver.set_script_timeout(timeout)
            return driver

    except WebDriverException as exc:
        raise ConfigurationError(f"Could not initialise Selenium {browser} driver: {exc}") from exc

    raise ConfigurationError(f"Unsupported browser: {browser}")


def element_is_displayed(driver: WebDriver, css_selector: str) -> bool:
    """Return whether an element exists and is displayed.

    Args:
        driver: Selenium WebDriver.
        css_selector: CSS selector to find.

    Returns:
        True when the element exists and is displayed, otherwise False.
    """
    try:
        return driver.find_element(By.CSS_SELECTOR, css_selector).is_displayed()
    except (NoSuchElementException, StaleElementReferenceException):
        return False


def element_exists(driver: WebDriver, css_selector: str) -> bool:
    """Return whether an element exists in the DOM.

    Args:
        driver: Selenium WebDriver.
        css_selector: CSS selector to find.

    Returns:
        True when at least one matching element exists, otherwise False.
    """
    try:
        return len(driver.find_elements(By.CSS_SELECTOR, css_selector)) > 0
    except StaleElementReferenceException:
        return False


def accept_ao3_tos_if_present(driver: WebDriver, timeout: int) -> bool:
    """Accept the AO3 Terms of Service prompt if it is present.

    This function performs browser interaction I/O.

    Args:
        driver: Selenium WebDriver.
        timeout: Maximum seconds to wait while interacting with the prompt.

    Returns:
        True if the prompt was present and accepted, False otherwise.

    Raises:
        TimeoutException: If the prompt is present but cannot be completed.
        WebDriverException: If Selenium interaction fails.
    """
    if not element_is_displayed(driver, AO3_TOS_PROMPT_SELECTOR):
        return False

    wait = WebDriverWait(driver, timeout)

    tos_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, AO3_TOS_CHECKBOX_SELECTOR)))
    if not tos_checkbox.is_selected():
        tos_checkbox.click()

    data_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, AO3_DATA_PROCESSING_CHECKBOX_SELECTOR)))
    if not data_checkbox.is_selected():
        data_checkbox.click()

    accept_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, AO3_TOS_ACCEPT_BUTTON_SELECTOR)))
    accept_button.click()

    wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, AO3_TOS_PROMPT_SELECTOR)))
    return True


def get_optional_text(driver: WebDriver, css_selector: str) -> str | None:
    """Return stripped text for the first matching element, or None.

    Args:
        driver: Selenium WebDriver.
        css_selector: CSS selector.

    Returns:
        Element text or None if no element is found.
    """
    try:
        text = driver.find_element(By.CSS_SELECTOR, css_selector).text.strip()
        return text or None
    except (NoSuchElementException, StaleElementReferenceException):
        return None


def wait_for_ao3_work_page(driver: WebDriver, timeout: int) -> dict[str, Any]:
    """Wait for an AO3 work page to be ready and return validation metadata.

    This function performs browser interaction and DOM inspection.

    Args:
        driver: Selenium WebDriver.
        timeout: Maximum seconds to wait.

    Returns:
        Validation metadata including title, work title, chapter count, and
        whether the AO3 TOS prompt was handled.

    Raises:
        TimeoutException: If readiness checks fail.
        WebDriverException: If Selenium operations fail.
    """
    wait = WebDriverWait(driver, timeout)

    wait.until(lambda current_driver: current_driver.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    tos_prompt_handled = accept_ao3_tos_if_present(driver, timeout)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, AO3_WORK_READY_SELECTOR)))

    workskin_detected = element_exists(driver, AO3_WORK_READY_SELECTOR)
    chapters_detected = element_exists(driver, AO3_WORK_CHAPTERS_SELECTOR)
    chapter_count_detected = len(driver.find_elements(By.CSS_SELECTOR, AO3_WORK_CHAPTER_SELECTOR))
    work_metadata_detected = element_exists(driver, AO3_WORK_METADATA_SELECTOR)

    if not workskin_detected:
        raise TimeoutException(f"Expected AO3 work content selector {AO3_WORK_READY_SELECTOR} was not found.")

    return {
        "title": driver.title or None,
        "work_title": get_optional_text(driver, AO3_WORK_TITLE_SELECTOR),
        "byline": get_optional_text(driver, AO3_WORK_BYLINE_SELECTOR),
        "workskin_detected": workskin_detected,
        "chapters_detected": chapters_detected,
        "chapter_count_detected": chapter_count_detected,
        "work_metadata_detected": work_metadata_detected,
        "tos_prompt_handled": tos_prompt_handled,
    }


def summarise_error(error: BaseException | str | None, max_length: int = 500) -> str:
    """Create a compact one-line error summary.

    Args:
        error: Exception, string, or None.
        max_length: Maximum returned length.

    Returns:
        Short error summary.
    """
    if error is None:
        return "Unknown error"

    text = str(error)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    useful_lines = [
        line for line in lines
        if not line.startswith("#") and "<unknown>" not in line
    ]

    if useful_lines:
        summary = useful_lines[0]
    elif lines:
        summary = lines[0]
    else:
        summary = type(error).__name__

    if not summary or summary == "Message:":
        summary = type(error).__name__

    if len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."

    return summary


def write_html_atomic(output_path: Path, html: str) -> None:
    """Write an HTML file using a temporary file and replacement.

    This function performs filesystem output.

    Args:
        output_path: Destination HTML file.
        html: HTML content to write.

    Raises:
        OSError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f"{output_path.name}.tmp")

    with temporary_path.open("w", encoding="utf-8") as output_file:
        output_file.write(html)

    temporary_path.replace(output_path)


def make_failed_result(
        work_item: dict[str, Any],
        status: str,
        error: BaseException | str,
        start_time: str,
        start_monotonic: float,
        retries_used: int,
        validation: dict[str, Any] | None = None,
        current_url: str | None = None,
) -> dict[str, Any]:
    """Create a failed work result for the manifest.

    Args:
        work_item: Work metadata.
        status: Failure status.
        error: Error object or message.
        start_time: ISO timestamp when capture began.
        start_monotonic: Monotonic start time.
        retries_used: Number of retries used.
        validation: Optional validation metadata.
        current_url: Optional current browser URL.

    Returns:
        Manifest-ready failed result dictionary.
    """
    return {
        "work_id": work_item["work_id"],
        "year": work_item["year"],
        "date_updated": work_item["date_updated"],
        "url": work_item["full_work_url"],
        "current_url": current_url,
        "output_path": str(work_item["output_path"]),
        "status": status,
        "error": summarise_error(error),
        "retries": retries_used,
        "duration_seconds": round(time.monotonic() - start_monotonic, 3),
        "start_time": start_time,
        "end_time": utc_timestamp(),
        "source_plan_line": work_item["source_plan_line"],
        "validation": validation or {
            "title": None,
            "work_title": None,
            "byline": None,
            "workskin_detected": None,
            "chapters_detected": None,
            "chapter_count_detected": None,
            "work_metadata_detected": None,
            "tos_prompt_handled": False,
        },
        "metadata": make_manifest_metadata(work_item),
    }


def capture_one_work(
        driver: WebDriver,
        work_item: dict[str, Any],
        timeout: int,
        max_retries: int,
        retry_delay: float,
        logger: logging.Logger,
) -> dict[str, Any]:
    """Capture one AO3 work page and return a structured manifest result.

    This function performs browser and filesystem I/O. It catches ordinary
    per-work failures and returns manifest-ready dictionaries instead of raising.

    Args:
        driver: Selenium WebDriver.
        work_item: Work metadata including URL and output path.
        timeout: Maximum seconds to wait for readiness.
        max_retries: Number of retries after the first failed attempt.
        retry_delay: Seconds to wait between failed attempts.
        logger: Logger used to record retry events.

    Returns:
        Structured result dictionary for the work.
    """
    run_start_time = utc_timestamp()
    run_start_monotonic = time.monotonic()
    attempts_allowed = max_retries + 1
    retries_used = 0
    last_error: BaseException | str | None = None
    last_status = "failed"
    last_validation: dict[str, Any] | None = None
    last_current_url: str | None = None

    for attempt_number in range(1, attempts_allowed + 1):
        try:
            driver.get(work_item["full_work_url"])
            validation = wait_for_ao3_work_page(driver, timeout)
            last_validation = validation
            last_current_url = driver.current_url

            html = driver.page_source
            write_html_atomic(work_item["output_path"], html)

            return {
                "work_id": work_item["work_id"],
                "year": work_item["year"],
                "date_updated": work_item["date_updated"],
                "url": work_item["full_work_url"],
                "current_url": driver.current_url,
                "output_path": str(work_item["output_path"]),
                "status": "success",
                "error": None,
                "retries": retries_used,
                "duration_seconds": round(time.monotonic() - run_start_monotonic, 3),
                "start_time": run_start_time,
                "end_time": utc_timestamp(),
                "source_plan_line": work_item["source_plan_line"],
                "validation": validation,
                "metadata": make_manifest_metadata(work_item),
            }

        except TimeoutException as exc:
            last_error = exc
            last_status = "failed_validation"
            try:
                last_current_url = driver.current_url
            except (WebDriverException, ReadTimeoutError):
                last_current_url = None

        except (WebDriverException, ReadTimeoutError, OSError, JavascriptException) as exc:
            last_error = exc
            last_status = "failed"
            try:
                last_current_url = driver.current_url
            except (WebDriverException, ReadTimeoutError):
                last_current_url = None

        if attempt_number < attempts_allowed:
            retries_used += 1
            logger.warning(
                "Retrying work_id=%s after failed attempt %s/%s: %s",
                work_item["work_id"],
                attempt_number,
                attempts_allowed,
                summarise_error(last_error),
            )
            if retry_delay > 0:
                time.sleep(retry_delay)

    return make_failed_result(
        work_item=work_item,
        status=last_status,
        error=last_error,
        start_time=run_start_time,
        start_monotonic=run_start_monotonic,
        retries_used=retries_used,
        validation=last_validation,
        current_url=last_current_url,
    )


def create_manifest(
        args: argparse.Namespace,
        work_plan: list[dict[str, Any]] | None,
        run_id: str,
        start_time: str,
        end_time: str | None,
        total_works_in_plan: int,
        selected_works: int,
        planned_attempts: int,
        results: list[dict[str, Any]],
        interrupted: bool = False,
) -> dict[str, Any]:
    """Create the JSON manifest object.

    Args:
        args: Parsed command-line arguments.
        work_plan: Loaded work collection plan, if available.
        run_id: Run identifier.
        start_time: Run start timestamp.
        end_time: Run end timestamp.
        total_works_in_plan: Number of works in the full plan.
        selected_works: Number of works selected after start-work filtering.
        planned_attempts: Number of works selected for attempted capture.
        results: Per-work results.
        interrupted: Whether the run was interrupted.

    Returns:
        Manifest dictionary ready to be written as JSON.
    """
    succeeded = sum(1 for item in results if item["status"] == "success")
    failed = sum(1 for item in results if item["status"] in {"failed", "failed_validation"})
    skipped_existing = sum(1 for item in results if item["status"] == "skipped_existing")

    years_detected = sorted({item["year"] for item in work_plan or []}, reverse=True)

    return {
        "run_metadata": {
            "run_id": run_id,
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "start_time": start_time,
            "end_time": end_time,
            "test_mode": args.test_mode,
            "test_limit": args.test_limit,
            "reprocess": args.reprocess,
            "workers": args.workers,
            "collection_plan": str(args.collection_plan),
            "output_dir": str(args.output_dir),
            "log_file": str(args.log_file),
            "manifest_file": str(args.manifest_file),
            "interrupted": interrupted,
            "config": {
                "browser": args.browser,
                "headless": args.headless,
                "chrome_server_flags": args.chrome_server_flags,
                "timeout_seconds": args.timeout,
                "max_retries": args.max_retries,
                "retry_delay_seconds": args.retry_delay,
                "request_delay_seconds": args.request_delay,
                "request_jitter_seconds": args.request_jitter,
                "start_work_id": args.start_work_id,
            },
            "plan_summary": {
                "total_works_in_plan": total_works_in_plan,
                "selected_works": selected_works,
                "years_detected": years_detected,
                "input_order_preserved": True,
                "duplicate_work_ids_detected": 0,
            },
            "summary": {
                "planned_attempts": planned_attempts,
                "attempted": succeeded + failed,
                "succeeded": succeeded,
                "failed": failed,
                "skipped_existing": skipped_existing,
            },
        },
        "works": results,
    }


def write_manifests(
        manifest: dict[str, Any],
        manifest_file: Path,
        run_id: str,
) -> tuple[Path, Path]:
    """Write latest and per-run manifest files.

    This function performs JSON file output.

    Args:
        manifest: Manifest dictionary to write.
        manifest_file: Path to the latest manifest file.
        run_id: Run identifier used for the per-run manifest filename.

    Returns:
        Tuple of latest manifest path and per-run manifest path.

    Raises:
        OSError: If writing either manifest fails.
    """
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    per_run_manifest_file = manifest_file.with_name(
        f"{manifest_file.stem}_{run_id}{manifest_file.suffix}"
    )

    with manifest_file.open("w", encoding="utf-8") as output_file:
        json.dump(manifest, output_file, ensure_ascii=False, indent=2)

    with per_run_manifest_file.open("w", encoding="utf-8") as output_file:
        json.dump(manifest, output_file, ensure_ascii=False, indent=2)

    return manifest_file, per_run_manifest_file


def log_configuration(
        logger: logging.Logger,
        args: argparse.Namespace,
        work_plan: list[dict[str, Any]],
        total_works_in_plan: int,
        run_id: str,
) -> None:
    """Log startup configuration details.

    Args:
        logger: Configured programme logger.
        args: Parsed command-line arguments.
        work_plan: Loaded work collection plan.
        total_works_in_plan: Number of works in the full plan.
        run_id: Current run identifier.
    """
    years = sorted({item["year"] for item in work_plan}, reverse=True)

    logger.info("Starting %s run_id=%s", TOOL_NAME, run_id)
    logger.info("Collection plan: %s", args.collection_plan)
    logger.info("Output directory: %s", args.output_dir)
    logger.info("Log file: %s", args.log_file)
    logger.info("Manifest file: %s", args.manifest_file)
    logger.info("Browser: %s; headless=%s", args.browser, args.headless)
    logger.info("Chrome server flags: %s", args.chrome_server_flags)
    logger.info("Test mode: %s; test_limit=%s", args.test_mode, args.test_limit)
    logger.info("Reprocess: %s", args.reprocess)
    logger.info("Workers: %s", args.workers)
    logger.info("Timeout seconds: %s", args.timeout)
    logger.info("Max retries: %s", args.max_retries)
    logger.info("Retry delay seconds: %s", args.retry_delay)
    logger.info("Request delay seconds: %s", args.request_delay)
    logger.info("Request jitter seconds: %s", args.request_jitter)
    logger.info("Start work ID: %s", args.start_work_id)
    logger.info("Total works in plan: %s", total_works_in_plan)
    logger.info("Years detected: %s", ", ".join(str(year) for year in years))


def wait_between_requests(request_delay: float, request_jitter: float) -> None:
    """Wait between requests according to configured delay and jitter.

    Args:
        request_delay: Base delay in seconds.
        request_jitter: Maximum random extra delay in seconds.
    """
    delay = request_delay
    if request_jitter > 0:
        delay += random.uniform(0, request_jitter)

    if delay > 0:
        time.sleep(delay)


def main() -> int:
    """Run the batch AO3 work capture workflow and return an exit code.

    This function orchestrates argument parsing, validation, plan loading,
    capture planning, Selenium browser lifecycle, sequential execution, logging,
    manifest writing, and exit-code selection.

    Returns:
        Process exit code:
        - 0 for success;
        - 1 if one or more work captures failed;
        - 2 for configuration errors;
        - 130 for keyboard interruption.
    """
    args = parse_args()
    run_id = make_run_id()
    run_start_time = utc_timestamp()
    logger: logging.Logger | None = None
    driver: WebDriver | None = None
    work_plan: list[dict[str, Any]] | None = None
    total_works_in_plan = 0
    selected_works = 0
    planned_attempts = 0
    results: list[dict[str, Any]] = []

    try:
        logger = setup_logging(args.log_file)
        validate_args(args)
        work_plan = load_collection_plan(args.collection_plan)

        planned, skipped_existing, total_works_in_plan = plan_captures(
            work_plan=work_plan,
            output_dir=args.output_dir,
            test_mode=args.test_mode,
            test_limit=args.test_limit,
            reprocess=args.reprocess,
            start_work_id=args.start_work_id,
        )
        planned_attempts = len(planned)
        selected_works = len(planned) + len(skipped_existing)
        results.extend(skipped_existing)

        log_configuration(logger, args, work_plan, total_works_in_plan, run_id)

        for item in work_plan:
            for warning in item.get("url_warnings", []):
                logger.warning("work_id=%s line=%s: %s", item["work_id"], item["source_plan_line"], warning)

        for skipped in skipped_existing:
            logger.info(
                "SKIPPED_EXISTING work_id=%s -> %s",
                skipped["work_id"],
                skipped["output_path"],
            )

        logger.info("Skipped existing works: %s", len(skipped_existing))
        logger.info("Planned capture attempts: %s", planned_attempts)

        if planned_attempts > 0:
            logger.info("Creating Selenium browser session")
            driver = create_driver(
                browser=args.browser,
                headless=args.headless,
                chrome_server_flags=args.chrome_server_flags,
                timeout=args.timeout,
            )

        for item in planned:
            logger.info("Capturing work_id=%s %s", item["work_id"], item["full_work_url"])

            result = capture_one_work(
                driver=driver,
                work_item=item,
                timeout=args.timeout,
                max_retries=args.max_retries,
                retry_delay=args.retry_delay,
                logger=logger,
            )
            results.append(result)

            if result["status"] == "success":
                logger.info(
                    "SUCCESS work_id=%s -> %s chapters=%s",
                    result["work_id"],
                    result["output_path"],
                    result["validation"].get("chapter_count_detected"),
                )
                if result["validation"].get("tos_prompt_handled"):
                    logger.info("AO3 Terms of Service prompt accepted")
            else:
                logger.error(
                    "FAILED work_id=%s status=%s error=%r",
                    result["work_id"],
                    result["status"],
                    result["error"],
                )

            wait_between_requests(args.request_delay, args.request_jitter)

        if driver is not None:
            logger.info("Closing Selenium browser session")
            driver.quit()
            driver = None

        manifest = create_manifest(
            args=args,
            work_plan=work_plan,
            run_id=run_id,
            start_time=run_start_time,
            end_time=utc_timestamp(),
            total_works_in_plan=total_works_in_plan,
            selected_works=selected_works,
            planned_attempts=planned_attempts,
            results=results,
        )

        latest_manifest, per_run_manifest = write_manifests(
            manifest=manifest,
            manifest_file=args.manifest_file,
            run_id=run_id,
        )

        logger.info("Wrote latest manifest: %s", latest_manifest)
        logger.info("Wrote per-run manifest: %s", per_run_manifest)

        summary = manifest["run_metadata"]["summary"]
        logger.info(
            "Finished run: succeeded=%s failed=%s skipped_existing=%s",
            summary["succeeded"],
            summary["failed"],
            summary["skipped_existing"],
        )

        if summary["failed"] > 0:
            return EXIT_CAPTURE_FAILURE

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        if logger is not None:
            logger.warning("Run interrupted by user")

        if driver is not None:
            try:
                driver.quit()
            except WebDriverException:
                pass

        manifest = create_manifest(
            args=args,
            work_plan=work_plan,
            run_id=run_id,
            start_time=run_start_time,
            end_time=utc_timestamp(),
            total_works_in_plan=total_works_in_plan,
            selected_works=selected_works,
            planned_attempts=planned_attempts,
            results=results,
            interrupted=True,
        )

        try:
            latest_manifest, per_run_manifest = write_manifests(
                manifest=manifest,
                manifest_file=args.manifest_file,
                run_id=run_id,
            )
            if logger is not None:
                logger.info("Wrote partial latest manifest: %s", latest_manifest)
                logger.info("Wrote partial per-run manifest: %s", per_run_manifest)
        except OSError as exc:
            if logger is not None:
                logger.error("Could not write partial manifest: %s", exc)

        return EXIT_INTERRUPTED

    except ConfigurationError as exc:
        message = f"Configuration error: {exc}"
        if logger is not None:
            logger.error(message)
        else:
            print(message, file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR

    except OSError as exc:
        message = f"File-system error: {exc}"
        if logger is not None:
            logger.error(message)
        else:
            print(message, file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR

    finally:
        if driver is not None:
            try:
                driver.quit()
            except WebDriverException:
                pass


if __name__ == "__main__":
    sys.exit(main())