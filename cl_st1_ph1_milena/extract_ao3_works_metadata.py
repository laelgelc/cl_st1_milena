#!/usr/bin/env python3
"""
Extract AO3 work metadata from captured list-page HTML files.

This script is an offline post-processing step for Phase 1 corpus data
collection. It reads a capture manifest produced by capture_ao3_lists.py,
selects successfully captured AO3 list pages, parses the corresponding local
HTML files, and extracts work-level metadata from each AO3 work blurb.

The script does not make network requests. It preserves page order and work
order, exports metadata to NDJSON, TSV, and XLSX, and writes an extraction
manifest describing the run.

NDJSON is the canonical structured output. TSV and XLSX are convenience exports
for inspection and analysis.

Example:
    python extract_ao3_works_metadata.py

Extract from a specific capture manifest:
    python extract_ao3_works_metadata.py \\
        --input-manifest corpus/01_ao3_list_pages/capture_ao3_lists_manifest_20261013T075915Z.json

Test extraction:
    python extract_ao3_works_metadata.py --limit-pages 10 --overwrite
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

try:
    from bs4 import BeautifulSoup
    from bs4.element import Tag
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[assignment]
    Tag = Any  # type: ignore[misc, assignment]

TOOL_NAME = "extract_ao3_works_metadata.py"
TOOL_VERSION = "v1"

AO3_BASE_URL = "https://archiveofourown.org"

DEFAULT_INPUT_MANIFEST = "corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json"
DEFAULT_OUTPUT_DIR = "corpus/00_sources/ao3_works_metadata"
DEFAULT_OUTPUT_BASENAME = "ao3_works_metadata"
DEFAULT_LOG_FILE = "corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata.log"
DEFAULT_MANIFEST_FILE = "corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest.json"

WORK_LIST_SELECTOR = "ol.work.index.group li.work"
WORK_ITEM_SELECTOR = "li.work"
REQUIRED_TAGS_SELECTOR = "ul.required-tags"
MAIN_TAGS_SELECTOR = "ul.tags.commas"
SUMMARY_SELECTOR = "blockquote.userstuff.summary"
SERIES_SELECTOR = "ul.series"
STATS_SELECTOR = "dl.stats"

OUTPUT_FIELDS = [
    "work_id",
    "title",
    "work_url",
    "full_work_url",
    "author_name",
    "author_url",
    "is_anonymous",
    "gift_recipient",
    "gift_recipient_url",
    "fandoms",
    "fandom_urls",
    "rating",
    "archive_warnings",
    "categories",
    "completion_status",
    "date_updated",
    "date_updated_raw",
    "collection_year",
    "warning_tags",
    "relationship_tags",
    "character_tags",
    "freeform_tags",
    "tag_urls",
    "summary_text",
    "summary_html",
    "series",
    "language",
    "language_code",
    "words",
    "chapters_current",
    "chapters_total",
    "latest_chapter_url",
    "collections",
    "comments",
    "kudos",
    "bookmarks",
    "hits",
    "source_page_id",
    "source_list_page",
    "source_list_url",
    "source_html_path",
    "extraction_run_id",
]

LIST_OR_OBJECT_FIELDS = {
    "fandoms",
    "fandom_urls",
    "archive_warnings",
    "categories",
    "warning_tags",
    "relationship_tags",
    "character_tags",
    "freeform_tags",
    "tag_urls",
    "series",
}

ALLOWED_FORMATS = {"ndjson", "tsv", "xlsx"}

EXIT_SUCCESS = 0
EXIT_EXTRACTION_FAILURE = 1
EXIT_CONFIGURATION_ERROR = 2
EXIT_INTERRUPTED = 130


class ConfigurationError(Exception):
    """Raised when command-line arguments or input configuration are invalid."""


def utc_now() -> datetime:
    """Return the current UTC datetime.

    Returns:
        A timezone-aware UTC datetime.
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """Format a UTC datetime for JSON metadata.

    Args:
        dt: Datetime to format.

    Returns:
        ISO-like UTC timestamp ending in `Z`.
    """
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_run_id() -> str:
    """Create a UTC run identifier.

    Returns:
        Timestamp run ID in `YYYYMMDDTHHMMSSZ` format.
    """
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for AO3 work metadata extraction.

    Returns:
        Parsed command-line argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Extract AO3 work metadata from captured list-page HTML files."
    )
    parser.add_argument(
        "--input-manifest",
        default=DEFAULT_INPUT_MANIFEST,
        type=Path,
        help=f"Input capture manifest path. Default: {DEFAULT_INPUT_MANIFEST}",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        type=Path,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--output-basename",
        default=DEFAULT_OUTPUT_BASENAME,
        help=f"Base filename for metadata outputs. Default: {DEFAULT_OUTPUT_BASENAME}",
    )
    parser.add_argument(
        "--log-file",
        default=DEFAULT_LOG_FILE,
        type=Path,
        help=f"Append-only log file path. Default: {DEFAULT_LOG_FILE}",
    )
    parser.add_argument(
        "--manifest-file",
        default=DEFAULT_MANIFEST_FILE,
        type=Path,
        help=f"Latest extraction manifest path. Default: {DEFAULT_MANIFEST_FILE}",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["ndjson", "tsv", "xlsx"],
        help="Output formats to write. Allowed: ndjson tsv xlsx",
    )
    parser.add_argument(
        "--limit-pages",
        type=int,
        default=None,
        help="Optional maximum number of successful pages to parse.",
    )
    parser.add_argument(
        "--start-page-id",
        default=None,
        help="Optional first page ID to include, e.g. 2026_0500.",
    )
    parser.add_argument(
        "--end-page-id",
        default=None,
        help="Optional final page ID to include, e.g. 2026_0600.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output data files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Stop after the first recoverable page-level or work-level failure.",
    )
    return parser.parse_args()


def setup_logging(log_file: Path) -> logging.Logger:
    """Configure append-only file logging and console logging.

    This function performs file-system I/O by creating the log directory and
    opening the append-only log file.

    Args:
        log_file: Path to the log file.

    Returns:
        Configured logger.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(TOOL_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ConfigurationError: If any argument is invalid.
    """
    if not args.input_manifest.exists():
        raise ConfigurationError(f"Input manifest does not exist: {args.input_manifest}")
    if not args.input_manifest.is_file():
        raise ConfigurationError(f"Input manifest is not a file: {args.input_manifest}")

    formats = set(args.formats)
    unsupported = formats - ALLOWED_FORMATS
    if unsupported:
        raise ConfigurationError(f"Unsupported output format(s): {sorted(unsupported)}")

    if args.limit_pages is not None and args.limit_pages <= 0:
        raise ConfigurationError("--limit-pages must be a positive integer.")

    if not args.output_basename.strip():
        raise ConfigurationError("--output-basename cannot be empty.")

    if "xlsx" in formats:
        try:
            import openpyxl  # noqa: F401
        except ImportError as exc:
            raise ConfigurationError(
                "XLSX output requested, but openpyxl is not installed."
            ) from exc

    if BeautifulSoup is None:
        raise ConfigurationError(
            "beautifulsoup4 is not installed. Install it before running this programme."
        )


def output_paths(args: argparse.Namespace) -> dict[str, Path]:
    """Build output paths for requested formats.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Mapping from output format to output path.
    """
    return {
        output_format: args.output_dir / f"{args.output_basename}.{output_format}"
        for output_format in args.formats
    }


def validate_output_paths(args: argparse.Namespace) -> None:
    """Validate output paths and overwrite policy.

    This function performs file-system I/O by creating the output and manifest
    parent directories.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ConfigurationError: If an output file exists and overwrite is disabled.
    """
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.manifest_file.parent.mkdir(parents=True, exist_ok=True)
    args.log_file.parent.mkdir(parents=True, exist_ok=True)

    existing_outputs = [
        str(path)
        for path in output_paths(args).values()
        if path.exists() and not args.overwrite
    ]
    if existing_outputs:
        joined = "\n  ".join(existing_outputs)
        raise ConfigurationError(
            "Output data file(s) already exist. Use --overwrite to replace them:\n"
            f"  {joined}"
        )


def load_capture_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and validate the AO3 list capture manifest.

    This function performs file I/O.

    Args:
        manifest_path: Path to the capture manifest.

    Returns:
        Parsed manifest dictionary.

    Raises:
        ConfigurationError: If the manifest cannot be read or is structurally invalid.
    """
    try:
        with manifest_path.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Invalid JSON in input manifest: {manifest_path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Could not read input manifest: {manifest_path}") from exc

    if not isinstance(manifest, dict):
        raise ConfigurationError("Input manifest root must be a JSON object.")
    if "pages" not in manifest or not isinstance(manifest["pages"], list):
        raise ConfigurationError("Input manifest must contain a top-level pages list.")

    return manifest


def select_successful_pages(
        capture_manifest: dict[str, Any],
        start_page_id: str | None = None,
        end_page_id: str | None = None,
        limit_pages: int | None = None,
) -> list[dict[str, Any]]:
    """Select successful captured pages for metadata extraction.

    Args:
        capture_manifest: Loaded capture manifest.
        start_page_id: Optional first page ID to include.
        end_page_id: Optional last page ID to include.
        limit_pages: Optional maximum number of selected pages.

    Returns:
        Successful page records after filtering.

    Raises:
        ConfigurationError: If no successful pages are found or page ID filters are invalid.
    """
    pages = [
        page for page in capture_manifest.get("pages", [])
        if isinstance(page, dict) and page.get("status") == "success"
    ]

    if not pages:
        raise ConfigurationError("No successful pages are available for extraction.")

    page_ids = [page.get("page_id") for page in pages]

    start_index = 0
    end_index = len(pages) - 1

    if start_page_id:
        if start_page_id not in page_ids:
            raise ConfigurationError(
                f"--start-page-id was not found among successful pages: {start_page_id}"
            )
        start_index = page_ids.index(start_page_id)

    if end_page_id:
        if end_page_id not in page_ids:
            raise ConfigurationError(
                f"--end-page-id was not found among successful pages: {end_page_id}"
            )
        end_index = page_ids.index(end_page_id)

    if end_index < start_index:
        raise ConfigurationError("--end-page-id occurs before --start-page-id.")

    selected = pages[start_index:end_index + 1]

    if limit_pages is not None:
        selected = selected[:limit_pages]

    if not selected:
        raise ConfigurationError("No pages remain after applying selection filters.")

    return selected


def parse_html_file(html_path: Path) -> BeautifulSoup:
    """Read and parse a saved AO3 list-page HTML file.

    This function performs file I/O.

    Args:
        html_path: Path to the saved HTML file.

    Returns:
        Beautiful Soup parsed document.

    Raises:
        OSError: If the file cannot be read.
    """
    with html_path.open("r", encoding="utf-8", errors="replace") as file:
        html_text = file.read()
    return BeautifulSoup(html_text, "html.parser")


def normalise_text(value: str | None) -> str | None:
    """Normalise whitespace in a text value.

    Args:
        value: Raw text value.

    Returns:
        Whitespace-normalised string, or None if empty.
    """
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def text_of(tag: Tag | None, separator: str = " ") -> str | None:
    """Get normalised text from a Beautiful Soup tag.

    Args:
        tag: Beautiful Soup tag or None.
        separator: Separator used by Beautiful Soup when joining text nodes.

    Returns:
        Normalised tag text or None.
    """
    if tag is None:
        return None
    return normalise_text(tag.get_text(separator=separator, strip=True))


def inner_html(tag: Tag | None) -> str | None:
    """Return a tag's inner HTML.

    Args:
        tag: Beautiful Soup tag or None.

    Returns:
        Inner HTML string or None.
    """
    if tag is None:
        return None
    content = "".join(str(child) for child in tag.contents).strip()
    return content or None


def absolute_ao3_url(href: str | None) -> str | None:
    """Convert an AO3 relative URL to an absolute URL.

    Args:
        href: Relative or absolute URL.

    Returns:
        Absolute AO3 URL, or None if href is missing.
    """
    if not href:
        return None
    return urljoin(AO3_BASE_URL, href)


def build_full_work_url(work_url: str | None) -> str | None:
    """Build a full-work AO3 URL with adult acknowledgement and full-work view.

    Args:
        work_url: Canonical AO3 work URL.

    Returns:
        URL containing `view_adult=true` and `view_full_work=true`, or None.
    """
    if not work_url:
        return None

    parsed = urlparse(work_url)
    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_pairs["view_adult"] = "true"
    query_pairs["view_full_work"] = "true"

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_pairs),
            parsed.fragment,
        )
    )


def parse_ao3_display_date(date_raw: str | None) -> str | None:
    """Parse an AO3 display date into ISO YYYY-MM-DD format.

    Args:
        date_raw: AO3 display date such as `13 Oct 2026`.

    Returns:
        ISO date string, or None if parsing fails.
    """
    if not date_raw:
        return None

    cleaned = normalise_text(date_raw)
    if not cleaned:
        return None

    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_int(text: str | None) -> int | None:
    """Parse an integer from AO3 text containing commas or whitespace.

    Args:
        text: Raw numeric text.

    Returns:
        Parsed integer, or None if parsing fails.
    """
    if text is None:
        return None
    match = re.search(r"\d[\d,]*", text)
    if not match:
        return None
    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return None


def split_multi_value(value: str | None) -> list[str]:
    """Split comma-separated AO3 required-tag values.

    Args:
        value: Raw AO3 required-tag value.

    Returns:
        List of cleaned values.
    """
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_chapters(chapters_text: str | None) -> tuple[int | None, int | None]:
    """Parse AO3 chapter text such as `3/?` or `1/1`.

    Args:
        chapters_text: Raw AO3 chapters text.

    Returns:
        Tuple of current chapters and total chapters.
    """
    if not chapters_text:
        return None, None

    cleaned = normalise_text(chapters_text)
    if not cleaned:
        return None, None

    match = re.search(r"(\d+)\s*/\s*(\d+|\?)", cleaned)
    if not match:
        return parse_int(cleaned), None

    current = int(match.group(1))
    total = None if match.group(2) == "?" else int(match.group(2))
    return current, total


def extract_work_id(work_item: Tag, title_link: Tag | None) -> int | None:
    """Extract AO3 work ID from a work blurb.

    Args:
        work_item: AO3 work item tag.
        title_link: Title link tag.

    Returns:
        Numeric AO3 work ID, or None.
    """
    item_id = work_item.get("id")
    if item_id:
        match = re.search(r"work_(\d+)", item_id)
        if match:
            return int(match.group(1))

    if title_link is not None:
        href = title_link.get("href")
        if href:
            match = re.search(r"/works/(\d+)", href)
            if match:
                return int(match.group(1))

    return None


def first_direct_work_link(work_item: Tag) -> Tag | None:
    """Find the primary work title link.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Tag for the primary work link, or None.
    """
    heading = work_item.select_one("h4.heading")
    if heading is None:
        return work_item.find("a", href=re.compile(r"^/works/\d+"))

    for link in heading.find_all("a", href=True):
        href = link.get("href", "")
        if re.match(r"^/works/\d+/?$", href):
            return link
    return None


def extract_author(work_item: Tag) -> tuple[str | None, str | None, bool]:
    """Extract author metadata from a work blurb.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Tuple of author name, author URL, and anonymous flag.
    """
    author_link = work_item.select_one('h4.heading a[rel="author"]')
    classes = set(work_item.get("class", []))

    if author_link is not None:
        author_name = text_of(author_link)
        author_url = absolute_ao3_url(author_link.get("href"))
        return author_name, author_url, False

    heading = work_item.select_one("h4.heading")
    heading_text = heading.get_text(" ", strip=True) if heading else ""
    is_anonymous = "anonymous" in classes or bool(re.search(r"\bby\s+Anonymous\b", heading_text))
    author_name = "Anonymous" if is_anonymous else None

    return author_name, None, is_anonymous


def extract_gift_recipient(work_item: Tag) -> tuple[str | None, str | None]:
    """Extract gift recipient metadata from a work blurb.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Tuple of gift recipient text and URL.
    """
    heading = work_item.select_one("h4.heading")
    if heading is None:
        return None, None

    for link in heading.find_all("a", href=True):
        href = link.get("href", "")
        if href.startswith("/gifts?recipient="):
            return text_of(link), absolute_ao3_url(href)

    return None, None


def extract_fandoms(work_item: Tag) -> tuple[list[str], list[str]]:
    """Extract fandom names and URLs.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Tuple of fandom names and fandom URLs.
    """
    fandoms: list[str] = []
    fandom_urls: list[str] = []

    fandom_block = work_item.select_one("h5.fandoms")
    if fandom_block is None:
        return fandoms, fandom_urls

    for link in fandom_block.select("a.tag[href]"):
        name = text_of(link)
        if name:
            fandoms.append(name)
            fandom_urls.append(absolute_ao3_url(link.get("href")) or "")

    return fandoms, fandom_urls


def extract_required_tags(work_item: Tag) -> tuple[str | None, list[str], list[str], str | None]:
    """Extract AO3 required tags.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Tuple of rating, archive warnings, categories, and completion status.
    """
    rating = None
    archive_warnings: list[str] = []
    categories: list[str] = []
    completion_status = None

    required = work_item.select_one(REQUIRED_TAGS_SELECTOR)
    if required is None:
        return rating, archive_warnings, categories, completion_status

    for span in required.select("span[title]"):
        classes = set(span.get("class", []))
        value = span.get("title")
        if not value:
            continue

        if "rating" in classes and rating is None:
            rating = value
        elif "warnings" in classes:
            archive_warnings.extend(split_multi_value(value))
        elif "category" in classes:
            categories.extend(split_multi_value(value))
        elif "iswip" in classes and completion_status is None:
            completion_status = value

    return rating, archive_warnings, categories, completion_status


def extract_tag_group(work_item: Tag, class_name: str) -> tuple[list[str], list[dict[str, str | None]]]:
    """Extract a tag group from the main AO3 tag list.

    Args:
        work_item: AO3 work item tag.
        class_name: AO3 tag list item class to extract.

    Returns:
        Tuple of tag names and structured name/URL dictionaries.
    """
    names: list[str] = []
    urls: list[dict[str, str | None]] = []

    tags_block = work_item.select_one(MAIN_TAGS_SELECTOR)
    if tags_block is None:
        return names, urls

    for item in tags_block.select(f"li.{class_name}"):
        link = item.select_one("a.tag[href]")
        if link is None:
            continue
        name = text_of(link)
        if not name:
            continue
        url = absolute_ao3_url(link.get("href"))
        names.append(name)
        urls.append({"name": name, "url": url})

    return names, urls


def extract_summary(work_item: Tag) -> tuple[str | None, str | None]:
    """Extract summary text and summary HTML.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Tuple of summary text and summary inner HTML.
    """
    summary = work_item.select_one(SUMMARY_SELECTOR)
    if summary is None:
        return None, None

    return text_of(summary, separator="\n"), inner_html(summary)


def extract_series(work_item: Tag) -> list[dict[str, Any]]:
    """Extract series memberships.

    Args:
        work_item: AO3 work item tag.

    Returns:
        List of series membership dictionaries.
    """
    series_block = work_item.select_one(SERIES_SELECTOR)
    if series_block is None:
        return []

    memberships: list[dict[str, Any]] = []
    for item in series_block.select("li"):
        part = None
        part_tag = item.find("strong")
        if part_tag is not None:
            part = parse_int(text_of(part_tag))

        link = item.find("a", href=True)
        title = text_of(link) if link else None
        url = absolute_ao3_url(link.get("href")) if link else None

        if part is not None or title or url:
            memberships.append({"part": part, "title": title, "url": url})

    return memberships


def extract_stats(work_item: Tag) -> dict[str, Any]:
    """Extract AO3 stats from a work blurb.

    Args:
        work_item: AO3 work item tag.

    Returns:
        Dictionary containing parsed language, word, chapter, and count stats.
    """
    stats = {
        "language": None,
        "language_code": None,
        "words": None,
        "chapters_current": None,
        "chapters_total": None,
        "latest_chapter_url": None,
        "collections": 0,
        "comments": 0,
        "kudos": 0,
        "bookmarks": 0,
        "hits": None,
    }

    stats_block = work_item.select_one(STATS_SELECTOR)
    if stats_block is None:
        return stats

    language_dd = stats_block.select_one("dd.language")
    if language_dd is not None:
        stats["language"] = text_of(language_dd)
        stats["language_code"] = language_dd.get("lang")

    for field in ("words", "collections", "comments", "kudos", "bookmarks", "hits"):
        dd = stats_block.select_one(f"dd.{field}")
        if dd is not None:
            stats[field] = parse_int(text_of(dd))

    chapters_dd = stats_block.select_one("dd.chapters")
    if chapters_dd is not None:
        chapters_text = text_of(chapters_dd)
        current, total = parse_chapters(chapters_text)
        stats["chapters_current"] = current
        stats["chapters_total"] = total

        chapter_link = chapters_dd.find("a", href=True)
        if chapter_link is not None:
            stats["latest_chapter_url"] = absolute_ao3_url(chapter_link.get("href"))

    for count_field in ("collections", "comments", "kudos", "bookmarks"):
        if stats[count_field] is None:
            stats[count_field] = 0

    return stats


def extract_work_metadata(
        work_item: Tag,
        page_record: dict[str, Any],
        extraction_run_id: str,
) -> dict[str, Any]:
    """Extract a single AO3 work metadata record from one list-page work blurb.

    Args:
        work_item: AO3 work item tag.
        page_record: Source page record from the capture manifest.
        extraction_run_id: Current extraction run ID.

    Returns:
        Metadata record dictionary.
    """
    title_link = first_direct_work_link(work_item)
    work_id = extract_work_id(work_item, title_link)
    title = text_of(title_link)
    work_url = absolute_ao3_url(title_link.get("href")) if title_link else None
    full_work_url = build_full_work_url(work_url)

    author_name, author_url, is_anonymous = extract_author(work_item)
    gift_recipient, gift_recipient_url = extract_gift_recipient(work_item)
    fandoms, fandom_urls = extract_fandoms(work_item)
    rating, archive_warnings, categories, completion_status = extract_required_tags(work_item)

    date_updated_raw = text_of(work_item.select_one("p.datetime"))
    date_updated = parse_ao3_display_date(date_updated_raw)

    warning_tags, warning_urls = extract_tag_group(work_item, "warnings")
    relationship_tags, relationship_urls = extract_tag_group(work_item, "relationships")
    character_tags, character_urls = extract_tag_group(work_item, "characters")
    freeform_tags, freeform_urls = extract_tag_group(work_item, "freeforms")

    summary_text, summary_html = extract_summary(work_item)
    series = extract_series(work_item)
    stats = extract_stats(work_item)

    source_list_url = page_record.get("current_url") or page_record.get("url")

    record = {
        "work_id": work_id,
        "title": title,
        "work_url": work_url,
        "full_work_url": full_work_url,
        "author_name": author_name,
        "author_url": author_url,
        "is_anonymous": is_anonymous,
        "gift_recipient": gift_recipient,
        "gift_recipient_url": gift_recipient_url,
        "fandoms": fandoms,
        "fandom_urls": fandom_urls,
        "rating": rating,
        "archive_warnings": archive_warnings,
        "categories": categories,
        "completion_status": completion_status,
        "date_updated": date_updated,
        "date_updated_raw": date_updated_raw,
        "collection_year": page_record.get("year"),
        "warning_tags": warning_tags,
        "relationship_tags": relationship_tags,
        "character_tags": character_tags,
        "freeform_tags": freeform_tags,
        "tag_urls": {
            "warnings": warning_urls,
            "relationships": relationship_urls,
            "characters": character_urls,
            "freeforms": freeform_urls,
        },
        "summary_text": summary_text,
        "summary_html": summary_html,
        "series": series,
        "language": stats["language"],
        "language_code": stats["language_code"],
        "words": stats["words"],
        "chapters_current": stats["chapters_current"],
        "chapters_total": stats["chapters_total"],
        "latest_chapter_url": stats["latest_chapter_url"],
        "collections": stats["collections"],
        "comments": stats["comments"],
        "kudos": stats["kudos"],
        "bookmarks": stats["bookmarks"],
        "hits": stats["hits"],
        "source_page_id": page_record.get("page_id"),
        "source_list_page": page_record.get("page"),
        "source_list_url": source_list_url,
        "source_html_path": page_record.get("output_path"),
        "extraction_run_id": extraction_run_id,
    }

    return {field: record.get(field) for field in OUTPUT_FIELDS}


def resolve_source_html_path(path_value: str | None) -> Path:
    """Resolve an HTML source path from a manifest value.

    Args:
        path_value: Path value from the capture manifest.

    Returns:
        Path object.

    Raises:
        FileNotFoundError: If no path value is provided.
    """
    if not path_value:
        raise FileNotFoundError("Manifest page record has no output_path.")
    return Path(path_value)


def extract_page_works(
        page_record: dict[str, Any],
        extraction_run_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Extract all work metadata records from one AO3 list-page HTML file.

    This function performs file I/O by reading the source HTML file.

    Args:
        page_record: Source page record from the capture manifest.
        extraction_run_id: Current extraction run ID.

    Returns:
        Tuple of extracted records and page-level manifest result.
    """
    page_id = page_record.get("page_id")
    html_path = resolve_source_html_path(page_record.get("output_path"))

    page_result = {
        "page_id": page_id,
        "source_html_path": str(html_path),
        "status": "success",
        "works_extracted": 0,
        "error": None,
        "warnings": [],
    }

    soup = parse_html_file(html_path)
    work_items = soup.select(WORK_LIST_SELECTOR)
    if not work_items:
        work_items = soup.select(WORK_ITEM_SELECTOR)

    if not work_items:
        page_result["status"] = "failed"
        page_result["error"] = "No AO3 work items were found in source HTML."
        return [], page_result

    records: list[dict[str, Any]] = []
    for index, work_item in enumerate(work_items, start=1):
        try:
            record = extract_work_metadata(work_item, page_record, extraction_run_id)
            if record.get("work_id") is None and record.get("title") is None:
                warning = f"Skipped malformed work blurb #{index}: no work_id or title."
                page_result["warnings"].append(warning)
                continue
            records.append(record)
        except Exception as exc:  # noqa: BLE001
            warning = f"Malformed work blurb #{index}: {exc}"
            page_result["warnings"].append(warning)

    page_result["works_extracted"] = len(records)
    return records, page_result


def serialise_tabular_value(value: Any) -> Any:
    """Serialise a value for TSV/XLSX output.

    Args:
        value: Raw metadata value.

    Returns:
        Tabular-safe value.
    """
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def write_ndjson(records: list[dict[str, Any]], output_path: Path) -> None:
    """Write metadata records as newline-delimited JSON.

    This function performs file I/O.

    Args:
        records: Metadata records.
        output_path: Output NDJSON path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            file.write("\n")


def write_tsv(records: list[dict[str, Any]], output_path: Path, fieldnames: list[str]) -> None:
    """Write metadata records as TSV, serialising list/object fields as JSON strings.

    This function performs file I/O.

    Args:
        records: Metadata records.
        output_path: Output TSV path.
        fieldnames: Ordered output field names.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({field: serialise_tabular_value(record.get(field)) for field in fieldnames})


def write_xlsx(records: list[dict[str, Any]], output_path: Path, fieldnames: list[str]) -> None:
    """Write metadata records as XLSX, serialising list/object fields as JSON strings.

    This function performs file I/O.

    Args:
        records: Metadata records.
        output_path: Output XLSX path.
        fieldnames: Ordered output field names.
    """
    from openpyxl import Workbook

    output_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "ao3_works_metadata"
    worksheet.append(fieldnames)

    for record in records:
        worksheet.append([serialise_tabular_value(record.get(field)) for field in fieldnames])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    workbook.save(output_path)


def analyse_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Analyse duplicate work IDs without removing duplicates.

    Args:
        records: Metadata records.

    Returns:
        Duplicate summary list.
    """
    ids = [record.get("work_id") for record in records if record.get("work_id") is not None]
    counts = Counter(ids)
    page_ids_by_work_id: dict[Any, list[str]] = defaultdict(list)

    for record in records:
        work_id = record.get("work_id")
        page_id = record.get("source_page_id")
        if work_id is not None and page_id:
            page_ids_by_work_id[work_id].append(page_id)

    duplicates = []
    for work_id, count in sorted(counts.items(), key=lambda item: str(item[0])):
        if count > 1:
            duplicates.append(
                {
                    "work_id": work_id,
                    "occurrences": count,
                    "source_page_ids": page_ids_by_work_id.get(work_id, []),
                }
            )

    return duplicates


def write_extraction_manifests(
        manifest: dict[str, Any],
        manifest_file: Path,
        run_id: str,
) -> tuple[Path, Path]:
    """Write latest and timestamped extraction manifest files.

    This function performs file I/O.

    Args:
        manifest: Extraction manifest object.
        manifest_file: Latest manifest path.
        run_id: Extraction run ID.

    Returns:
        Tuple of latest manifest path and timestamped manifest path.
    """
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    timestamped_path = manifest_file.with_name(f"{manifest_file.stem}_{run_id}{manifest_file.suffix}")

    for path in (manifest_file, timestamped_path):
        with path.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, ensure_ascii=False, indent=2)
            file.write("\n")

    return manifest_file, timestamped_path


def build_manifest(
        args: argparse.Namespace,
        run_id: str,
        start_time: str,
        end_time: str | None,
        capture_manifest: dict[str, Any],
        selected_pages: list[dict[str, Any]],
        page_results: list[dict[str, Any]],
        records: list[dict[str, Any]],
        duplicates: list[dict[str, Any]],
        outputs: dict[str, Path],
        interrupted: bool = False,
) -> dict[str, Any]:
    """Build the extraction manifest object.

    Args:
        args: Parsed command-line arguments.
        run_id: Extraction run ID.
        start_time: Run start timestamp.
        end_time: Run end timestamp.
        capture_manifest: Input capture manifest.
        selected_pages: Pages selected for extraction.
        page_results: Page-level extraction results.
        records: Extracted records.
        duplicates: Duplicate work ID summary.
        outputs: Mapping of output formats to paths.
        interrupted: Whether the run was interrupted.

    Returns:
        Extraction manifest dictionary.
    """
    capture_run_id = capture_manifest.get("run_metadata", {}).get("run_id")
    pages = capture_manifest.get("pages", [])
    successful_pages = [
        page for page in pages
        if isinstance(page, dict) and page.get("status") == "success"
    ]

    pages_failed = sum(1 for page in page_results if page.get("status") != "success")
    pages_parsed = sum(1 for page in page_results if page.get("status") == "success")
    work_parse_warnings = sum(len(page.get("warnings", [])) for page in page_results)
    unique_work_ids = len({record.get("work_id") for record in records if record.get("work_id") is not None})

    return {
        "run_metadata": {
            "run_id": run_id,
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "start_time": start_time,
            "end_time": end_time,
            "interrupted": interrupted,
            "input_manifest": str(args.input_manifest),
            "capture_run_id": capture_run_id,
            "output_dir": str(args.output_dir),
            "outputs": {key: str(value) for key, value in outputs.items()},
            "log_file": str(args.log_file),
            "manifest_file": str(args.manifest_file),
            "config": {
                "formats": args.formats,
                "overwrite": args.overwrite,
                "strict": args.strict,
                "start_page_id": args.start_page_id,
                "end_page_id": args.end_page_id,
                "limit_pages": args.limit_pages,
            },
            "summary": {
                "pages_in_input_manifest": len(pages),
                "successful_pages_in_input_manifest": len(successful_pages),
                "pages_selected_for_extraction": len(selected_pages),
                "pages_parsed": pages_parsed,
                "pages_failed": pages_failed,
                "works_extracted": len(records),
                "unique_work_ids": unique_work_ids,
                "duplicate_work_ids": len(duplicates),
                "work_parse_warnings": work_parse_warnings,
            },
        },
        "pages": page_results,
        "duplicates": duplicates,
    }


def write_outputs(
        args: argparse.Namespace,
        records: list[dict[str, Any]],
        outputs: dict[str, Path],
        logger: logging.Logger,
) -> None:
    """Write requested metadata output files.

    Args:
        args: Parsed command-line arguments.
        records: Extracted metadata records.
        outputs: Mapping of output formats to paths.
        logger: Logger instance.
    """
    if "ndjson" in args.formats:
        write_ndjson(records, outputs["ndjson"])
        logger.info("Wrote NDJSON: %s", outputs["ndjson"])

    if "tsv" in args.formats:
        write_tsv(records, outputs["tsv"], OUTPUT_FIELDS)
        logger.info("Wrote TSV: %s", outputs["tsv"])

    if "xlsx" in args.formats:
        write_xlsx(records, outputs["xlsx"], OUTPUT_FIELDS)
        logger.info("Wrote XLSX: %s", outputs["xlsx"])


def main() -> int:
    """Run AO3 work metadata extraction and return an exit code.

    Returns:
        Process exit code.
    """
    args = parse_args()
    run_id = make_run_id()
    start_dt = utc_now()
    start_time = format_timestamp(start_dt)

    logger: logging.Logger | None = None
    capture_manifest: dict[str, Any] = {}
    selected_pages: list[dict[str, Any]] = []
    page_results: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    outputs: dict[str, Path] = {}

    try:
        logger = setup_logging(args.log_file)
        logger.info("Starting %s run_id=%s", TOOL_NAME, run_id)
        logger.info("Input manifest: %s", args.input_manifest)
        logger.info("Output directory: %s", args.output_dir)
        logger.info("Formats: %s", ", ".join(args.formats))
        logger.info("Overwrite: %s; strict=%s", args.overwrite, args.strict)

        validate_args(args)
        validate_output_paths(args)

        outputs = output_paths(args)
        capture_manifest = load_capture_manifest(args.input_manifest)
        selected_pages = select_successful_pages(
            capture_manifest,
            start_page_id=args.start_page_id,
            end_page_id=args.end_page_id,
            limit_pages=args.limit_pages,
        )

        logger.info("Pages in input manifest: %d", len(capture_manifest.get("pages", [])))
        logger.info("Successful pages selected for extraction: %d", len(selected_pages))

        for page_record in selected_pages:
            page_id = page_record.get("page_id")
            logger.info("Parsing page %s: %s", page_id, page_record.get("output_path"))

            try:
                page_records, page_result = extract_page_works(page_record, run_id)
                records.extend(page_records)
                page_results.append(page_result)

                if page_result.get("status") == "success":
                    logger.info(
                        "SUCCESS %s works_extracted=%d warnings=%d",
                        page_id,
                        page_result.get("works_extracted", 0),
                        len(page_result.get("warnings", [])),
                    )
                else:
                    logger.error("FAILED %s error=%s", page_id, page_result.get("error"))
                    if args.strict:
                        break

                if page_result.get("warnings"):
                    for warning in page_result["warnings"]:
                        logger.warning("%s: %s", page_id, warning)
                    if args.strict:
                        break

            except FileNotFoundError as exc:
                page_result = {
                    "page_id": page_id,
                    "source_html_path": str(page_record.get("output_path")),
                    "status": "failed",
                    "works_extracted": 0,
                    "error": str(exc),
                    "warnings": [],
                }
                page_results.append(page_result)
                logger.error("FAILED %s missing source HTML: %s", page_id, exc)
                if args.strict:
                    break

            except Exception as exc:  # noqa: BLE001
                page_result = {
                    "page_id": page_id,
                    "source_html_path": str(page_record.get("output_path")),
                    "status": "failed",
                    "works_extracted": 0,
                    "error": str(exc),
                    "warnings": [],
                }
                page_results.append(page_result)
                logger.exception("FAILED %s unexpected extraction error", page_id)
                if args.strict:
                    break

        duplicates = analyse_duplicates(records)
        logger.info("Works extracted: %d", len(records))
        logger.info("Duplicate work IDs: %d", len(duplicates))

        write_outputs(args, records, outputs, logger)

        end_time = format_timestamp(utc_now())
        manifest = build_manifest(
            args=args,
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            capture_manifest=capture_manifest,
            selected_pages=selected_pages,
            page_results=page_results,
            records=records,
            duplicates=duplicates,
            outputs=outputs,
        )
        latest_manifest, timestamped_manifest = write_extraction_manifests(
            manifest,
            args.manifest_file,
            run_id,
        )
        logger.info("Wrote latest extraction manifest: %s", latest_manifest)
        logger.info("Wrote timestamped extraction manifest: %s", timestamped_manifest)

        failed_pages = sum(1 for page in page_results if page.get("status") != "success")
        warning_count = sum(len(page.get("warnings", [])) for page in page_results)

        logger.info(
            "Finished extraction: pages=%d failed_pages=%d works=%d warnings=%d",
            len(page_results),
            failed_pages,
            len(records),
            warning_count,
        )

        if failed_pages > 0 or (args.strict and warning_count > 0):
            return EXIT_EXTRACTION_FAILURE
        return EXIT_SUCCESS

    except KeyboardInterrupt:
        if logger:
            logger.warning("Interrupted by user.")
        end_time = format_timestamp(utc_now())
        try:
            duplicates = analyse_duplicates(records)
            manifest = build_manifest(
                args=args,
                run_id=run_id,
                start_time=start_time,
                end_time=end_time,
                capture_manifest=capture_manifest,
                selected_pages=selected_pages,
                page_results=page_results,
                records=records,
                duplicates=duplicates,
                outputs=outputs,
                interrupted=True,
            )
            write_extraction_manifests(manifest, args.manifest_file, run_id)
        except Exception as exc:  # noqa: BLE001
            if logger:
                logger.error("Could not write interrupted partial manifest: %s", exc)
        return EXIT_INTERRUPTED

    except ConfigurationError as exc:
        if logger:
            logger.error("Configuration error: %s", exc)
        else:
            print(f"Configuration error: {exc}", file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR

    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.exception("Unexpected fatal error: %s", exc)
        else:
            print(f"Unexpected fatal error: {exc}", file=sys.stderr)
        return EXIT_EXTRACTION_FAILURE


if __name__ == "__main__":
    sys.exit(main())