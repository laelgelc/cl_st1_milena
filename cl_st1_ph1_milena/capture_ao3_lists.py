"""
Capture AO3 list pages for Phase 1 corpus data collection.

This script reads an AO3 list collection plan from JSON, generates AO3 Works
list URLs for English Original Work pages, and captures each rendered list page
as an HTML file using Selenium.

The Phase 1 collection plan captures yearly list ranges from 2026 down to 2019.
Recent years are processed first because AO3 users are more active in recent
periods, making those list ranges more susceptible to change.

By default, the script runs in test mode and attempts only the first 5 planned
missing pages. Existing HTML files are skipped unless --reprocess is provided,
making the script safe to re-run.

The script handles AO3's Terms of Service prompt when it appears, waits for
AO3 list-page content, saves rendered HTML, and records page-level validation
information in a JSON manifest.

Example:
    python capture_ao3_lists.py

Full run:
    python capture_ao3_lists.py --no-test-mode

Resume from a specific page:
    python capture_ao3_lists.py --no-test-mode --start-page-id 2025_0120

The script writes an append-only log file and JSON manifests describing
run-level metadata and per-page capture status.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

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


TOOL_NAME = "capture_ao3_lists.py"
TOOL_VERSION = "v1"

DEFAULT_COLLECTION_PLAN_PATH = "corpus/00_sources/ao3_list_collection_plan.json"
DEFAULT_OUTPUT_DIR = "corpus/01_ao3_list_pages"
DEFAULT_LOG_FILE = "corpus/01_ao3_list_pages/capture_ao3_lists.log"
DEFAULT_MANIFEST_FILE = "corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json"

DEFAULT_BROWSER = "chrome"
DEFAULT_HEADLESS = True
DEFAULT_CHROME_SERVER_FLAGS = True

DEFAULT_TEST_MODE = True
DEFAULT_TEST_LIMIT = 5
DEFAULT_WORKERS = 1

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_DELAY_SECONDS = 10

DEFAULT_REQUEST_DELAY_SECONDS = 3.0
DEFAULT_REQUEST_JITTER_SECONDS = 1.0

AO3_LIST_READY_SELECTOR = "ol.work.index.group li.work"
AO3_LIST_CONTAINER_SELECTOR = "ol.work.index.group"
AO3_MAIN_HEADING_SELECTOR = "#main h2.heading"
AO3_TOS_PROMPT_SELECTOR = "#tos_prompt"
AO3_TOS_CHECKBOX_SELECTOR = "#tos_agree"
AO3_DATA_PROCESSING_CHECKBOX_SELECTOR = "#data_processing_agree"
AO3_TOS_ACCEPT_BUTTON_SELECTOR = "#accept_tos"

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
    """Parse command-line arguments for the AO3 list capture programme.

    Returns:
        An argparse namespace containing command-line values. Semantic validation
        is performed separately by validate_args().
    """
    parser = argparse.ArgumentParser(
        description="Capture AO3 list pages as rendered HTML files using Selenium."
    )

    parser.add_argument(
        "--collection-plan",
        type=Path,
        default=Path(DEFAULT_COLLECTION_PLAN_PATH),
        help=f"Path to the JSON collection plan. Default: {DEFAULT_COLLECTION_PLAN_PATH}",
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
        help=f"Maximum pages to attempt in test mode. Default: {DEFAULT_TEST_LIMIT}",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Capture pages even when output HTML files already exist.",
    )
    parser.add_argument(
        "--start-page-id",
        type=str,
        default=None,
        help="Optional page ID from which to start planning, e.g. 2025_0120.",
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
        help=f"Maximum seconds to wait for one page. Default: {DEFAULT_TIMEOUT_SECONDS}",
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
        help=f"Delay in seconds between page requests. Default: {DEFAULT_REQUEST_DELAY_SECONDS}",
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
    if args.start_page_id is not None and not args.start_page_id.strip():
        raise ConfigurationError("--start-page-id must not be empty when provided")

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Could not create required output directories: {exc}") from exc


def load_collection_plan(plan_path: Path) -> dict[str, Any]:
    """Load and validate the AO3 list collection plan.

    This function performs file I/O.

    Args:
        plan_path: Path to the JSON plan file.

    Returns:
        The validated collection plan dictionary.

    Raises:
        ConfigurationError: If the file cannot be read, JSON is invalid, or
            required fields are missing/invalid.
    """
    try:
        with plan_path.open("r", encoding="utf-8") as input_file:
            plan = json.load(input_file)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Invalid JSON in collection plan {plan_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Could not read collection plan {plan_path}: {exc}") from exc

    required_top_level = ["collection_name", "base_url", "filters", "ranges"]
    for field in required_top_level:
        if field not in plan:
            raise ConfigurationError(f"Collection plan is missing required field: {field}")

    if not isinstance(plan["base_url"], str) or not plan["base_url"].strip():
        raise ConfigurationError("Collection plan base_url must be a non-empty string")
    if not isinstance(plan["filters"], dict):
        raise ConfigurationError("Collection plan filters must be an object")
    if not isinstance(plan["ranges"], list) or not plan["ranges"]:
        raise ConfigurationError("Collection plan ranges must be a non-empty list")

    required_filter_fields = [
        "sort_column",
        "other_tag_names",
        "excluded_tag_names",
        "crossover",
        "complete",
        "words_from",
        "words_to",
        "query",
        "language_id",
        "commit",
        "tag_id",
    ]
    for field in required_filter_fields:
        if field not in plan["filters"]:
            raise ConfigurationError(f"Collection plan filters are missing required field: {field}")

    required_range_fields = [
        "year",
        "date_from",
        "date_to",
        "expected_works",
        "page_from",
        "page_to",
    ]
    for index, range_item in enumerate(plan["ranges"], start=1):
        if not isinstance(range_item, dict):
            raise ConfigurationError(f"Range item {index} must be an object")

        for field in required_range_fields:
            if field not in range_item:
                raise ConfigurationError(f"Range item {index} is missing required field: {field}")

        year = range_item["year"]
        page_from = range_item["page_from"]
        page_to = range_item["page_to"]
        expected_works = range_item["expected_works"]

        if not isinstance(year, int):
            raise ConfigurationError(f"Range item {index} year must be an integer")
        if not isinstance(page_from, int) or page_from <= 0:
            raise ConfigurationError(f"Range item {index} page_from must be a positive integer")
        if not isinstance(page_to, int) or page_to <= 0:
            raise ConfigurationError(f"Range item {index} page_to must be a positive integer")
        if page_from > page_to:
            raise ConfigurationError(f"Range item {index} page_from must not exceed page_to")
        if not isinstance(expected_works, int) or expected_works < 0:
            raise ConfigurationError(f"Range item {index} expected_works must be a non-negative integer")
        if not isinstance(range_item["date_from"], str) or not range_item["date_from"].strip():
            raise ConfigurationError(f"Range item {index} date_from must be a non-empty string")
        if not isinstance(range_item["date_to"], str) or not range_item["date_to"].strip():
            raise ConfigurationError(f"Range item {index} date_to must be a non-empty string")

    return plan


def build_ao3_list_url(base_url: str, filters: dict[str, Any], range_item: dict[str, Any], page: int) -> str:
    """Build a canonical AO3 list URL from plan filters, year range, and page number.

    Args:
        base_url: AO3 works base URL.
        filters: Shared filters from the collection plan.
        range_item: Year-specific range object from the collection plan.
        page: Page number to request.

    Returns:
        A URL string with URL-encoded query parameters.
    """
    query_params = {
        "view_adult": "true",
        "work_search[sort_column]": filters.get("sort_column", ""),
        "work_search[other_tag_names]": filters.get("other_tag_names", ""),
        "work_search[excluded_tag_names]": filters.get("excluded_tag_names", ""),
        "work_search[crossover]": filters.get("crossover", ""),
        "work_search[complete]": filters.get("complete", ""),
        "work_search[words_from]": filters.get("words_from", ""),
        "work_search[words_to]": filters.get("words_to", ""),
        "work_search[date_from]": range_item["date_from"],
        "work_search[date_to]": range_item["date_to"],
        "work_search[query]": filters.get("query", ""),
        "work_search[language_id]": filters.get("language_id", ""),
        "commit": filters.get("commit", ""),
        "tag_id": filters.get("tag_id", ""),
        "page": str(page),
    }
    return f"{base_url}?{urlencode(query_params)}"


def make_page_id(year: int, page: int) -> str:
    """Create a stable page identifier from year and page number."""
    return f"{year}_{page:04d}"


def make_skipped_existing_result(page_item: dict[str, Any], output_path: Path) -> dict[str, Any]:
    """Create a manifest result for a page skipped because output already exists.

    Args:
        page_item: Planned page metadata.
        output_path: Existing output HTML path.

    Returns:
        A structured page-level manifest dictionary.
    """
    timestamp = utc_timestamp()
    return {
        "page_id": page_item["page_id"],
        "year": page_item["year"],
        "page": page_item["page"],
        "url": page_item["url"],
        "current_url": None,
        "output_path": str(output_path),
        "status": "skipped_existing",
        "error": None,
        "retries": 0,
        "duration_seconds": 0.0,
        "start_time": timestamp,
        "end_time": timestamp,
        "validation": {
            "title": None,
            "heading": None,
            "work_items_detected": None,
            "tos_prompt_handled": False,
        },
        "metadata": {
            "reason": "Output HTML file already exists and --reprocess was not provided",
        },
    }


def expand_collection_plan(collection_plan: dict[str, Any], output_dir: Path) -> list[dict[str, Any]]:
    """Expand a collection plan into ordered page records.

    Args:
        collection_plan: Validated collection plan dictionary.
        output_dir: Base output directory for HTML pages.

    Returns:
        Ordered page item dictionaries preserving collection plan range order.
    """
    pages: list[dict[str, Any]] = []

    for range_item in collection_plan["ranges"]:
        year = range_item["year"]
        year_dir = output_dir / str(year)

        for page_number in range(range_item["page_from"], range_item["page_to"] + 1):
            page_id = make_page_id(year, page_number)
            output_path = year_dir / f"{page_id}.html"
            url = build_ao3_list_url(
                base_url=collection_plan["base_url"],
                filters=collection_plan["filters"],
                range_item=range_item,
                page=page_number,
            )
            pages.append(
                {
                    "page_id": page_id,
                    "year": year,
                    "page": page_number,
                    "date_from": range_item["date_from"],
                    "date_to": range_item["date_to"],
                    "expected_works": range_item["expected_works"],
                    "url": url,
                    "output_path": output_path,
                }
            )

    return pages


def plan_captures(
        collection_plan: dict[str, Any],
        output_dir: Path,
        test_mode: bool,
        test_limit: int,
        reprocess: bool,
        start_page_id: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Create planned and skipped page capture records.

    This function performs filesystem checks but does not perform network I/O.

    Args:
        collection_plan: Validated collection plan dictionary.
        output_dir: Directory where captured HTML files are saved.
        test_mode: Whether to limit planned attempts.
        test_limit: Maximum planned attempts when test mode is active.
        reprocess: Whether existing HTML files should be re-captured.
        start_page_id: Optional page ID from which planning should start.

    Returns:
        A tuple containing:
        - planned capture records;
        - skipped-existing result records;
        - total number of pages in the full collection plan.

    Raises:
        ConfigurationError: If start_page_id is provided but not found.
    """
    all_pages = expand_collection_plan(collection_plan, output_dir)
    total_pages = len(all_pages)
    selected_pages = all_pages

    if start_page_id is not None:
        clean_start_page_id = start_page_id.strip()
        start_index = next(
            (index for index, item in enumerate(all_pages) if item["page_id"] == clean_start_page_id),
            None,
        )
        if start_index is None:
            raise ConfigurationError(f"--start-page-id was not found in the collection plan: {clean_start_page_id}")
        selected_pages = all_pages[start_index:]

    planned: list[dict[str, Any]] = []
    skipped_existing: list[dict[str, Any]] = []

    for page_item in selected_pages:
        output_path = page_item["output_path"]

        if output_path.exists() and not reprocess:
            skipped_existing.append(make_skipped_existing_result(page_item, output_path))
            continue

        planned.append(page_item)

    if test_mode:
        planned = planned[:test_limit]

    return planned, skipped_existing, total_pages


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


def wait_for_ao3_list_page(driver: WebDriver, timeout: int) -> dict[str, Any]:
    """Wait for an AO3 list page to be ready and return validation metadata.

    This function performs browser interaction and DOM inspection.

    Args:
        driver: Selenium WebDriver.
        timeout: Maximum seconds to wait.

    Returns:
        Validation metadata including title, heading, work count, and whether
        the AO3 TOS prompt was handled.

    Raises:
        TimeoutException: If readiness checks fail.
        WebDriverException: If Selenium operations fail.
    """
    wait = WebDriverWait(driver, timeout)

    wait.until(lambda current_driver: current_driver.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    tos_prompt_handled = accept_ao3_tos_if_present(driver, timeout)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, AO3_LIST_CONTAINER_SELECTOR)))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, AO3_LIST_READY_SELECTOR)))

    work_items_detected = len(driver.find_elements(By.CSS_SELECTOR, AO3_LIST_READY_SELECTOR))
    if work_items_detected <= 0:
        raise TimeoutException("Expected AO3 work items were not found.")

    return {
        "title": driver.title or None,
        "heading": get_optional_text(driver, AO3_MAIN_HEADING_SELECTOR),
        "work_items_detected": work_items_detected,
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
        page_item: dict[str, Any],
        status: str,
        error: BaseException | str,
        start_time: str,
        start_monotonic: float,
        retries_used: int,
        validation: dict[str, Any] | None = None,
        current_url: str | None = None,
) -> dict[str, Any]:
    """Create a failed page result for the manifest.

    Args:
        page_item: Page metadata.
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
        "page_id": page_item["page_id"],
        "year": page_item["year"],
        "page": page_item["page"],
        "url": page_item["url"],
        "current_url": current_url,
        "output_path": str(page_item["output_path"]),
        "status": status,
        "error": summarise_error(error),
        "retries": retries_used,
        "duration_seconds": round(time.monotonic() - start_monotonic, 3),
        "start_time": start_time,
        "end_time": utc_timestamp(),
        "validation": validation or {
            "title": None,
            "heading": None,
            "work_items_detected": None,
            "tos_prompt_handled": False,
        },
    }


def capture_one_page(
        driver: WebDriver,
        page_item: dict[str, Any],
        timeout: int,
        max_retries: int,
        retry_delay: float,
        logger: logging.Logger,
) -> dict[str, Any]:
    """Capture one AO3 list page and return a structured manifest result.

    This function performs browser and filesystem I/O. It catches ordinary
    per-page failures and returns manifest-ready dictionaries instead of raising.

    Args:
        driver: Selenium WebDriver.
        page_item: Page metadata including URL and output path.
        timeout: Maximum seconds to wait for readiness.
        max_retries: Number of retries after the first failed attempt.
        retry_delay: Seconds to wait between failed attempts.
        logger: Logger used to record retry events.

    Returns:
        Structured result dictionary for the page.
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
            driver.get(page_item["url"])
            validation = wait_for_ao3_list_page(driver, timeout)
            last_validation = validation
            last_current_url = driver.current_url

            html = driver.page_source
            write_html_atomic(page_item["output_path"], html)

            return {
                "page_id": page_item["page_id"],
                "year": page_item["year"],
                "page": page_item["page"],
                "url": page_item["url"],
                "current_url": driver.current_url,
                "output_path": str(page_item["output_path"]),
                "status": "success",
                "error": None,
                "retries": retries_used,
                "duration_seconds": round(time.monotonic() - run_start_monotonic, 3),
                "start_time": run_start_time,
                "end_time": utc_timestamp(),
                "validation": validation,
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
                "Retrying %s after failed attempt %s/%s: %s",
                page_item["page_id"],
                attempt_number,
                attempts_allowed,
                summarise_error(last_error),
            )
            if retry_delay > 0:
                time.sleep(retry_delay)

    return make_failed_result(
        page_item=page_item,
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
        collection_plan: dict[str, Any] | None,
        run_id: str,
        start_time: str,
        end_time: str | None,
        total_pages_in_plan: int,
        planned_attempts: int,
        results: list[dict[str, Any]],
        interrupted: bool = False,
) -> dict[str, Any]:
    """Create the JSON manifest object.

    Args:
        args: Parsed command-line arguments.
        collection_plan: Loaded collection plan, if available.
        run_id: Run identifier.
        start_time: Run start timestamp.
        end_time: Run end timestamp.
        total_pages_in_plan: Number of pages in the full plan.
        planned_attempts: Number of pages selected for attempted capture.
        results: Per-page results.
        interrupted: Whether the run was interrupted.

    Returns:
        Manifest dictionary ready to be written as JSON.
    """
    succeeded = sum(1 for item in results if item["status"] == "success")
    failed = sum(1 for item in results if item["status"] in {"failed", "failed_validation"})
    skipped_existing = sum(1 for item in results if item["status"] == "skipped_existing")

    if collection_plan is not None:
        years = [item["year"] for item in collection_plan.get("ranges", [])]
        total_expected_works = sum(item.get("expected_works", 0) for item in collection_plan.get("ranges", []))
        range_order = collection_plan.get("range_order")
        page_order_within_year = collection_plan.get("page_order_within_year")
        collection_name = collection_plan.get("collection_name")
    else:
        years = []
        total_expected_works = 0
        range_order = None
        page_order_within_year = None
        collection_name = None

    return {
        "run_metadata": {
            "run_id": run_id,
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "collection_name": collection_name,
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
                "start_page_id": args.start_page_id,
            },
            "plan_summary": {
                "range_order": range_order,
                "page_order_within_year": page_order_within_year,
                "years": years,
                "total_pages_in_plan": total_pages_in_plan,
                "total_expected_works": total_expected_works,
            },
            "summary": {
                "selected_pages": planned_attempts + skipped_existing,
                "planned_attempts": planned_attempts,
                "attempted": succeeded + failed,
                "succeeded": succeeded,
                "failed": failed,
                "skipped_existing": skipped_existing,
            },
        },
        "pages": results,
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
        collection_plan: dict[str, Any],
        total_pages_in_plan: int,
        run_id: str,
) -> None:
    """Log startup configuration details.

    Args:
        logger: Configured programme logger.
        args: Parsed command-line arguments.
        collection_plan: Loaded collection plan.
        total_pages_in_plan: Number of planned pages before filtering/skipping.
        run_id: Current run identifier.
    """
    years = [item["year"] for item in collection_plan["ranges"]]

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
    logger.info("Start page ID: %s", args.start_page_id)
    logger.info("Loaded plan years: %s", ", ".join(str(year) for year in years))
    logger.info("Range order: %s", collection_plan.get("range_order"))
    logger.info("Page order within year: %s", collection_plan.get("page_order_within_year"))
    logger.info("Total pages in plan: %s", total_pages_in_plan)


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
    """Run the batch AO3 list capture workflow and return an exit code.

    This function orchestrates argument parsing, validation, plan loading,
    capture planning, Selenium browser lifecycle, sequential execution, logging,
    manifest writing, and exit-code selection.

    Returns:
        Process exit code:
        - 0 for success;
        - 1 if one or more page captures failed;
        - 2 for configuration errors;
        - 130 for keyboard interruption.
    """
    args = parse_args()
    run_id = make_run_id()
    run_start_time = utc_timestamp()
    logger: logging.Logger | None = None
    driver: WebDriver | None = None
    collection_plan: dict[str, Any] | None = None
    total_pages_in_plan = 0
    planned_attempts = 0
    results: list[dict[str, Any]] = []

    try:
        logger = setup_logging(args.log_file)
        validate_args(args)
        collection_plan = load_collection_plan(args.collection_plan)

        planned, skipped_existing, total_pages_in_plan = plan_captures(
            collection_plan=collection_plan,
            output_dir=args.output_dir,
            test_mode=args.test_mode,
            test_limit=args.test_limit,
            reprocess=args.reprocess,
            start_page_id=args.start_page_id,
        )
        planned_attempts = len(planned)
        results.extend(skipped_existing)

        log_configuration(logger, args, collection_plan, total_pages_in_plan, run_id)

        for skipped in skipped_existing:
            logger.info(
                "SKIPPED_EXISTING %s -> %s",
                skipped["page_id"],
                skipped["output_path"],
            )

        logger.info("Skipped existing pages: %s", len(skipped_existing))
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
            logger.info("Capturing %s %s", item["page_id"], item["url"])

            result = capture_one_page(
                driver=driver,
                page_item=item,
                timeout=args.timeout,
                max_retries=args.max_retries,
                retry_delay=args.retry_delay,
                logger=logger,
            )
            results.append(result)

            if result["status"] == "success":
                logger.info(
                    "SUCCESS %s -> %s work_items=%s",
                    result["page_id"],
                    result["output_path"],
                    result["validation"].get("work_items_detected"),
                )
                if result["validation"].get("tos_prompt_handled"):
                    logger.info("AO3 Terms of Service prompt accepted")
            else:
                logger.error(
                    "FAILED %s status=%s error=%r",
                    result["page_id"],
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
            collection_plan=collection_plan,
            run_id=run_id,
            start_time=run_start_time,
            end_time=utc_timestamp(),
            total_pages_in_plan=total_pages_in_plan,
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
            collection_plan=collection_plan,
            run_id=run_id,
            start_time=run_start_time,
            end_time=utc_timestamp(),
            total_pages_in_plan=total_pages_in_plan,
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