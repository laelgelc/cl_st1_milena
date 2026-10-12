# `capture_ao3_lists.py` — Programme Specification for Development

## 1. High-level Functionality Specification

### Programme Summary

`capture_ao3_lists.py` is a batch-processing programme that captures Archive of Our Own (AO3) list/search result pages as rendered HTML files for the Phase 1 data collection workflow.

This programme implements the **Lists Collection** subphase of Phase 1. It does **not** extract metadata and does **not** extract text. Its sole data-collection responsibility is to capture and save AO3 list pages as HTML files in a reproducible, resumable, auditable way.

The programme reads a fixed JSON collection plan:
```
text
corpus/00_sources/ao3_list_collection_plan.json
```
The collection plan defines:

- the AO3 base URL;
- the shared query parameters for the study selection;
- the yearly date ranges;
- the expected number of works per year;
- the first and last page to capture for each year;
- the planned capture order.

For Phase 1, the planned capture range is:
```
text
2026 → 2025 → 2024 → 2023 → 2022 → 2021 → 2020 → 2019
```
Years are captured in **descending order** because the most recent AO3 lists are more volatile. AO3 users are more active in recent years, so list ranges for 2026 and 2025 are more susceptible to change. Capturing recent years first reduces the risk that the documented page ranges become stale before acquisition.

Within each year, pages are captured in ascending page order:
```
text
2026_0001 → 2026_0002 → ... → 2026_3793
2025_0001 → 2025_0002 → ... → 2025_3132
...
2019_0001 → ... → 2019_0531
```
The programme saves each list page as:
```
text
corpus/01_ao3_list_pages/<year>/<year>_<page:04d>.html
```
For example:
```
text
corpus/01_ao3_list_pages/2026/2026_0001.html
corpus/01_ao3_list_pages/2025/2025_0001.html
corpus/01_ao3_list_pages/2019/2019_0531.html
```
The programme uses Selenium to run a real browser in headless mode. Chrome is the default browser, and Firefox is supported through a command-line option.

The programme must handle AO3’s Terms of Service consent prompt when it appears, wait for list-page content to be available, validate that the expected AO3 list structure is present, and then save the rendered HTML.

The programme must be safe to re-run: existing HTML files are skipped by default unless `--reprocess` is provided.

The programme writes an append-only log file and JSON manifests describing run-level metadata and page-level capture status.

---

## 2. Key Behaviours

The programme must implement the following behaviours:

- Read the AO3 list collection plan from JSON.
- Preserve the order of yearly ranges defined in the JSON plan.
- For Phase 1, process years in descending order from 2026 to 2019.
- Process pages in ascending order within each year.
- Generate canonical AO3 list URLs from:
  - base URL;
  - shared query parameters;
  - year-specific date range;
  - page number.
- Capture rendered AO3 list pages with Selenium.
- Use Chrome by default.
- Support Firefox as an alternative browser.
- Run headless by default.
- Use one browser session per run for efficiency and to preserve AO3 consent state.
- Handle the AO3 Terms of Service consent prompt if it appears.
- Wait for AO3 list content using page-specific readiness checks.
- Save only HTML files.
- Do not produce scraped `.txt` files.
- Do not extract full metadata in this programme.
- Record basic validation information such as:
  - page title;
  - page heading;
  - number of detected work blurbs.
- Skip existing HTML files by default.
- Reprocess existing HTML files only when `--reprocess` is provided.
- Use test mode by default, limiting capture to 5 planned pages.
- Support starting from a specific page identifier using `--start-page-id`.
- Continue processing remaining pages if one page fails.
- Apply a configurable delay between page captures.
- Optionally apply random jitter to the inter-page delay.
- Record progress and errors in an append-only log file.
- Produce a JSON manifest with run-level metadata and page-level results.
- Write both:
  - a timestamped per-run manifest;
  - a latest manifest that is overwritten on each run.
- Exit with status code `0` only when all attempted captures succeed or are skipped.
- Exit with a non-zero status code if one or more attempted captures fail, or if there is a configuration/validation error.

---

## 3. Input / Output Specification

### 3.1 Input

#### Collection plan file

Default path:
```
text
corpus/00_sources/ao3_list_collection_plan.json
```
The collection plan is a JSON file defining the Phase 1 AO3 list capture task.

The file is expected to contain:

- collection-level metadata;
- base URL;
- shared query parameters;
- output filename pattern;
- yearly date/page ranges;
- expected works count for each year.

#### Recommended collection plan structure
```
json
{
  "collection_name": "ao3_original_work_english_lists_2026_2019",
  "created_on": "2026-10-12",
  "base_url": "https://archiveofourown.org/works",
  "range_order": "descending_year",
  "page_order_within_year": "ascending_page",
  "output_file_pattern": "{year}_{page:04d}.html",
  "filters": {
    "sort_column": "revised_at",
    "other_tag_names": "",
    "excluded_tag_names": "",
    "crossover": "F",
    "complete": "",
    "words_from": "",
    "words_to": "",
    "query": "",
    "language_id": "en",
    "commit": "Sort and Filter",
    "tag_id": "Original Work"
  },
  "ranges": [
    {
      "year": 2026,
      "date_from": "2026-01-01",
      "date_to": "2026-12-31",
      "expected_works": 75852,
      "page_from": 1,
      "page_to": 3793
    },
    {
      "year": 2025,
      "date_from": "2025-01-01",
      "date_to": "2025-12-31",
      "expected_works": 62624,
      "page_from": 1,
      "page_to": 3132
    },
    {
      "year": 2024,
      "date_from": "2024-01-01",
      "date_to": "2024-12-31",
      "expected_works": 45720,
      "page_from": 1,
      "page_to": 2286
    },
    {
      "year": 2023,
      "date_from": "2023-01-01",
      "date_to": "2023-12-31",
      "expected_works": 37817,
      "page_from": 1,
      "page_to": 1891
    },
    {
      "year": 2022,
      "date_from": "2022-01-01",
      "date_to": "2022-12-31",
      "expected_works": 29197,
      "page_from": 1,
      "page_to": 1460
    },
    {
      "year": 2021,
      "date_from": "2021-01-01",
      "date_to": "2021-12-31",
      "expected_works": 22574,
      "page_from": 1,
      "page_to": 1129
    },
    {
      "year": 2020,
      "date_from": "2020-01-01",
      "date_to": "2020-12-31",
      "expected_works": 16422,
      "page_from": 1,
      "page_to": 822
    },
    {
      "year": 2019,
      "date_from": "2019-01-01",
      "date_to": "2019-12-31",
      "expected_works": 10613,
      "page_from": 1,
      "page_to": 531
    }
  ]
}
```
#### Query parameter mapping

The programme must translate the plan’s `filters` object into AO3 query parameters.

For the filters above, the generated URL must include:

| Plan field | AO3 query parameter |
|---|---|
| `sort_column` | `work_search[sort_column]` |
| `other_tag_names` | `work_search[other_tag_names]` |
| `excluded_tag_names` | `work_search[excluded_tag_names]` |
| `crossover` | `work_search[crossover]` |
| `complete` | `work_search[complete]` |
| `words_from` | `work_search[words_from]` |
| `words_to` | `work_search[words_to]` |
| `date_from` | `work_search[date_from]` |
| `date_to` | `work_search[date_to]` |
| `query` | `work_search[query]` |
| `language_id` | `work_search[language_id]` |
| `commit` | `commit` |
| `tag_id` | `tag_id` |
| page number | `page` |

Example generated URL:
```
text
https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=1
```
The exact encoding may differ as long as the resulting URL is semantically equivalent and valid.

---

### 3.2 Output

#### HTML output directory

Default path:
```
text
corpus/01_ao3_list_pages/
```
The programme must create this directory if it does not already exist.

#### Per-year output directories

The programme must save pages under year-specific subdirectories:
```
text
corpus/01_ao3_list_pages/2026/
corpus/01_ao3_list_pages/2025/
corpus/01_ao3_list_pages/2024/
corpus/01_ao3_list_pages/2023/
corpus/01_ao3_list_pages/2022/
corpus/01_ao3_list_pages/2021/
corpus/01_ao3_list_pages/2020/
corpus/01_ao3_list_pages/2019/
```
#### Per-page HTML output

Each page must be saved as:
```
text
<output_dir>/<year>/<year>_<page:04d>.html
```
Examples:
```
text
corpus/01_ao3_list_pages/2026/2026_0001.html
corpus/01_ao3_list_pages/2026/2026_3793.html
corpus/01_ao3_list_pages/2019/2019_0531.html
```
#### No text output

The programme must **not** save `.txt` versions of the pages.

Text extraction is outside the scope of `capture_ao3_lists.py`.

#### Log file

Default path:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists.log
```
The log file must be:

- plain text;
- UTF-8 encoded;
- append-only;
- line-oriented.

#### Manifest files

The programme must write two manifest files.

##### Latest manifest

Default path:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```
This file is overwritten at the end of each run.

##### Per-run manifest

A timestamped copy must also be written using the run ID.

Filename pattern:
```
text
capture_ao3_lists_manifest_<run_id>.json
```
Example:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest_20261012T143012Z.json
```
---

## 4. Command-line Interface

### 4.1 Default usage
```
bash
python capture_ao3_lists.py
```
Default behaviour:

- collection plan: `corpus/00_sources/ao3_list_collection_plan.json`
- output directory: `corpus/01_ao3_list_pages/`
- log file: `corpus/01_ao3_list_pages/capture_ao3_lists.log`
- manifest file: `corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json`
- browser: `chrome`
- headless mode: enabled
- test mode: enabled
- test limit: 5 pages
- reprocess: disabled
- existing `.html` files are skipped
- workers: 1 / sequential processing
- request delay: enabled
- AO3 Terms of Service prompt handling: enabled
- no start page filter

---

### 4.2 Required arguments

There are no required command-line arguments if all default paths are used.

However, all important paths and processing controls must be configurable.

---

### 4.3 Optional arguments

#### Collection plan path
```
bash
--collection-plan PATH
```
Default:
```
text
corpus/00_sources/ao3_list_collection_plan.json
```
Description:

Path to the JSON collection plan file.

---

#### Output directory
```
bash
--output-dir PATH
```
Default:
```
text
corpus/01_ao3_list_pages/
```
Description:

Directory where captured AO3 list HTML files will be saved.

---

#### Browser
```
bash
--browser chrome
--browser firefox
```
Default:
```
text
chrome
```
Description:

Browser to use for Selenium capture.

Supported values:

- `chrome`
- `firefox`

---

#### Headless mode
```
bash
--headless
--no-headless
```
Default:
```
text
--headless
```
Description:

Run the browser in headless mode by default. This is required for production use on EC2.

---

#### Test mode
```
bash
--test-mode
--no-test-mode
```
Default:
```
text
--test-mode
```
Description:

When test mode is enabled, the programme processes only a limited number of planned pages.

---

#### Test limit
```
bash
--test-limit N
```
Default:
```
text
5
```
Description:

Maximum number of pages to attempt when test mode is enabled.

Must be a positive integer.

Example:
```
bash
python capture_ao3_lists.py --test-limit 10
```
---

#### Reprocess existing pages
```
bash
--reprocess
```
Default:
```
text
False
```
Description:

When omitted, the programme skips any page whose output `.html` file already exists.

When provided, the programme captures the page again and overwrites the existing output file.

Example:
```
bash
python capture_ao3_lists.py --reprocess
```
---

#### Start page ID
```
bash
--start-page-id PAGE_ID
```
Default:
```
text
None
```
Description:

Optional page identifier from which to start planning captures.

The page ID format is:
```
text
<year>_<page:04d>
```
Examples:
```
text
2026_0001
2025_0120
2019_0531
```
When `--start-page-id` is provided, the programme must preserve the collection plan order but ignore all pages that occur before the specified page ID. The specified page itself must be included in the planning step.

Example:
```
bash
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2025_0120
```
If the requested page ID is not found in the planned page list, the programme must fail fast with a configuration error.

---

#### Log file
```
bash
--log-file PATH
```
Default:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists.log
```
Description:

Path to the append-only log file.

---

#### Manifest file
```
bash
--manifest-file PATH
```
Default:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```
Description:

Path to the latest manifest file. The per-run timestamped manifest should be written next to this file.

---

#### Workers
```
bash
--workers N
```
Default:
```
text
1
```
Description:

Number of worker processes.

For the current implementation, sequential execution with `--workers 1` is required. The architecture may allow parallel execution later, but parallel browser-based scraping is not recommended in the first production version.

Must be a positive integer.

---

#### Timeout
```
bash
--timeout SECONDS
```
Default suggestion:
```
text
30
```
Description:

Maximum allowed time to wait for one AO3 page to load and pass readiness checks.

If the timeout is reached:

- mark the item as failed;
- log the timeout;
- continue with the next page.

---

#### Maximum retries
```
bash
--max-retries N
```
Default suggestion:
```
text
2
```
Description:

Number of retry attempts after a failed capture.

For example, with `--max-retries 2`, each failed page may be attempted three times in total:

1. initial attempt;
2. first retry;
3. second retry.

Must be zero or a positive integer.

---

#### Retry delay
```
bash
--retry-delay SECONDS
```
Default suggestion:
```
text
10
```
Description:

Delay between failed capture attempts.

Must be zero or a positive integer.

---

#### Request delay
```
bash
--request-delay SECONDS
```
Default suggestion:
```
text
3
```
Description:

Delay after each attempted page capture before the next page is requested.

This is a politeness control to avoid placing unnecessary load on AO3.

---

#### Request jitter
```
bash
--request-jitter SECONDS
```
Default suggestion:
```
text
1
```
Description:

Maximum random additional delay added to `--request-delay`.

For example, with:
```
bash
--request-delay 3 --request-jitter 1
```
the programme waits between 3 and 4 seconds between page requests.

---

#### Chrome server flags
```
bash
--chrome-server-flags
--no-chrome-server-flags
```
Default:
```
text
--chrome-server-flags
```
Description:

When using Chrome, include options suitable for headless Linux/EC2 execution, such as:
```
text
--no-sandbox
--disable-dev-shm-usage
--disable-gpu
--window-size=1920,1080
```
---

## 4.4 Example commands

### Small default test run
```
bash
python capture_ao3_lists.py
```
Captures up to 5 missing pages using the default collection plan.

---

### Test run with 10 pages
```
bash
python capture_ao3_lists.py --test-limit 10
```
---

### Test run from a specific page ID
```
bash
python capture_ao3_lists.py \
  --test-limit 10 \
  --start-page-id 2025_0120
```
---

### Full production run
```
bash
python capture_ao3_lists.py --no-test-mode
```
---

### Full production run from a specific page ID
```
bash
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2025_0120
```
---

### Full production run with explicit paths
```
bash
python capture_ao3_lists.py \
  --collection-plan corpus/00_sources/ao3_list_collection_plan.json \
  --output-dir corpus/01_ao3_list_pages \
  --no-test-mode
```
---

### Full production run with Firefox
```
bash
python capture_ao3_lists.py \
  --browser firefox \
  --no-test-mode
```
---

### Re-capture pages even if files already exist
```
bash
python capture_ao3_lists.py \
  --no-test-mode \
  --reprocess
```
---

### More conservative production run
```
bash
python capture_ao3_lists.py \
  --no-test-mode \
  --request-delay 5 \
  --request-jitter 2 \
  --max-retries 3 \
  --retry-delay 20
```
---

### EC2 full run with `nohup`
```
bash
nohup bash run_python_ec2.sh \
  capture_ao3_lists.py \
    --no-test-mode \
    --browser chrome \
    --request-delay 3 \
    --request-jitter 1 \
> process_output.log 2>&1 &
```
---

### EC2 full run from a specific page ID
```
bash
nohup bash run_python_ec2.sh \
  capture_ao3_lists.py \
    --no-test-mode \
    --browser chrome \
    --start-page-id 2025_0120 \
    --request-delay 3 \
    --request-jitter 1 \
> process_output.log 2>&1 &
```
---

## 5. Argument Validation

The programme must fail fast with a clear message if:

- the collection plan file does not exist;
- the collection plan path is not a file;
- the collection plan contains invalid JSON;
- the collection plan is missing required top-level fields;
- the collection plan has an empty `ranges` list;
- a range is missing required fields:
  - `year`;
  - `date_from`;
  - `date_to`;
  - `page_from`;
  - `page_to`;
  - `expected_works`;
- a range has invalid page values;
- a range has `page_from` greater than `page_to`;
- an output directory cannot be created;
- `--browser` is not one of the supported browsers;
- `--test-limit` is less than or equal to zero;
- `--workers` is less than or equal to zero;
- `--workers` is not `1` in the current sequential implementation;
- `--timeout` is less than or equal to zero;
- `--max-retries` is negative;
- `--retry-delay` is negative;
- `--request-delay` is negative;
- `--request-jitter` is negative;
- `--start-page-id` is provided but empty;
- `--start-page-id` is provided but not found in the planned page list;
- Selenium cannot initialise the selected browser.

A validation error should:

- be printed clearly to the console;
- be written to the log if logging has already been configured;
- cause the programme to exit with a non-zero status code.

---

## 6. Environment and Configuration

### Required Python packages

The programme requires Python and Selenium.

Suggested Python dependencies:
```
text
selenium
```
The programme may use only Python standard-library modules besides Selenium.

Suggested standard-library modules:

- `argparse`
- `json`
- `logging`
- `pathlib`
- `datetime`
- `time`
- `random`
- `sys`
- `urllib.parse`
- `typing`

### Browser dependencies

At least one supported browser must be installed:

- Chrome or Chromium; or
- Firefox.

Chrome is recommended for EC2 production runs.

### Selenium Manager

Selenium Manager may be used automatically by Selenium to locate, download, and cache the appropriate browser driver. No explicit driver path should be required in the first implementation.

### EC2 portability requirements

The programme must be portable to an EC2 instance.

For Chrome on EC2, the following browser options should be used by default in headless mode:
```
text
--headless=new
--no-sandbox
--disable-dev-shm-usage
--disable-gpu
--window-size=1920,1080
```
For Firefox on EC2, the browser should run with:
```
text
--headless
```
### Secrets and credentials

This programme does not require API keys or secret credentials.

For this first implementation, AO3 cookies are not required. AO3 Terms of Service consent should be handled through Selenium interaction.

---

## 7. Core Processing Architecture

### 7.1 High-level flow

The programme must follow this workflow:

1. **Startup**
   - Parse command-line arguments.
   - Generate a UTC run ID.
   - Set up logging.
   - Validate arguments.
   - Load and validate the collection plan.
   - Ensure output, log, and manifest directories exist.

2. **Planning**
   - Build the ordered list of planned pages from the collection plan.
   - Preserve the yearly order from `ranges`.
   - For the Phase 1 plan, this means 2026 through 2019.
   - For each year, create page IDs in ascending page order.
   - Generate canonical AO3 URLs for each page.
   - If `--start-page-id` is provided:
     - locate the specified page ID;
     - ignore all pages before it;
     - include the specified page and all following pages;
     - fail fast if the specified page ID is not found.
   - For each selected page:
     - compute output path;
     - decide whether to skip or attempt capture.
   - If the file exists and `--reprocess` is not enabled:
     - mark the page as `skipped_existing`.
   - If the file does not exist or `--reprocess` is enabled:
     - plan the page for capture.
   - If test mode is enabled:
     - limit attempted captures to `--test-limit`.

3. **Browser setup**
   - Create one Selenium WebDriver instance for the run.
   - Use the selected browser.
   - Configure headless mode.
   - Configure EC2-safe Chrome flags when applicable.

4. **Execution**
   - For each planned page:
     - request the generated URL with Selenium;
     - wait for browser-level readiness;
     - handle AO3 Terms of Service prompt if it appears;
     - wait for AO3 list-page content;
     - validate expected list-page structure;
     - save HTML;
     - record page-level result.
   - If a page capture fails:
     - retry according to `--max-retries`;
     - if all attempts fail, mark the page as failed;
     - continue to the next page.
   - Apply request delay and jitter between pages.

5. **End-of-run summary**
   - Count:
     - total plan pages;
     - selected pages after start-page filtering;
     - skipped existing pages;
     - attempted pages;
     - successful captures;
     - failed captures.
   - Write the latest manifest.
   - Write the per-run manifest.
   - Log the final summary.
   - Exit with an appropriate status code.

6. **Interrupt handling**
   - Catch `KeyboardInterrupt`.
   - Stop cleanly.
   - Quit the browser if it exists.
   - Write a partial manifest.
   - Log the interruption.
   - Exit non-zero.

---

### 7.2 Separation of concerns

The implementation should be organised around the following responsibilities.

#### CLI parsing

Responsible for:

- defining command-line arguments;
- applying defaults;
- returning a configuration object or namespace.

Suggested function:
```
python
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the AO3 list capture programme."""
```
#### Logging setup

Responsible for:

- creating the log directory;
- configuring append-only file logging;
- configuring console logging.

Suggested function:
```
python
def setup_logging(log_file: Path) -> logging.Logger:
    """Configure append-only file logging and console logging."""
```
#### Argument validation

Responsible for:

- checking paths;
- checking numeric arguments;
- checking supported browser selection;
- checking worker count;
- checking start page ID syntax.

Suggested function:
```
python
def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments before processing."""
```
#### Collection plan loading

Responsible for:

- reading JSON;
- validating required fields;
- validating yearly ranges;
- preserving range order.

Suggested function:
```
python
def load_collection_plan(plan_path: Path) -> dict:
    """Load and validate the AO3 list collection plan."""
```
#### URL generation

Responsible for:

- translating plan filters into AO3 query parameters;
- adding year-specific date filters;
- adding page number;
- returning a valid URL string.

Suggested function:
```
python
def build_ao3_list_url(base_url: str, filters: dict, range_item: dict, page: int) -> str:
    """Build a canonical AO3 list URL from plan filters, year range, and page number."""
```
#### Planning

Responsible for:

- expanding year ranges into page records;
- creating page IDs;
- applying `--start-page-id`;
- checking existing files;
- applying test limit.

Suggested function:
```
python
def plan_captures(
    collection_plan: dict,
    output_dir: Path,
    test_mode: bool,
    test_limit: int,
    reprocess: bool,
    start_page_id: str | None = None
) -> tuple[list[dict], list[dict], int]:
    """Create planned and skipped page capture records."""
```
#### Browser creation

Responsible for:

- creating a Selenium WebDriver;
- selecting Chrome or Firefox;
- setting headless options;
- setting EC2/server-safe Chrome flags.

Suggested function:
```
python
def create_driver(browser: str, headless: bool, chrome_server_flags: bool) -> webdriver.Remote:
    """Create a Selenium WebDriver for the requested browser."""
```
#### AO3 consent handling

Responsible for:

- detecting AO3 Terms of Service prompt;
- clicking both checkboxes;
- clicking the accept button;
- waiting for the prompt to disappear.

Suggested function:
```
python
def accept_ao3_tos_if_present(driver: webdriver.Remote, timeout: int) -> bool:
    """Accept the AO3 Terms of Service prompt if it is present."""
```
Return value:

- `True` if a prompt was detected and accepted;
- `False` if no prompt was present.

#### AO3 list readiness wait

Responsible for:

- waiting for `document.readyState == "complete"`;
- waiting for `body`;
- accepting TOS prompt if present;
- waiting for list content.

Suggested function:
```
python
def wait_for_ao3_list_page(driver: webdriver.Remote, timeout: int) -> dict:
    """Wait for an AO3 list page to be ready and return basic validation metadata."""
```
This function should wait for:
```
text
ol.work.index.group li.work
```
It should return validation metadata such as:
```
python
{
    "title": "...",
    "heading": "...",
    "work_items_detected": 20,
    "tos_prompt_handled": True
}
```
#### Single page capture

Responsible for:

- loading a URL;
- waiting for readiness;
- saving HTML;
- returning structured result.

Suggested function:
```
python
def capture_one_page(
    driver: webdriver.Remote,
    page_item: dict,
    timeout: int,
    max_retries: int,
    retry_delay: int
) -> dict:
    """Capture one AO3 list page and return a structured manifest result."""
```
#### Manifest writing

Responsible for writing:

- latest manifest;
- timestamped per-run manifest.

Suggested function:
```
python
def write_manifests(
    manifest: dict,
    manifest_file: Path,
    run_id: str
) -> tuple[Path, Path]:
    """Write latest and per-run manifest files."""
```
#### Main orchestration

Responsible for:

- coordinating all steps;
- logging;
- browser lifecycle;
- error handling;
- exit code.

Suggested function:
```
python
def main() -> int:
    """Run the batch AO3 list capture workflow and return an exit code."""
```
---

## 8. AO3 List Capture Behaviour

### 8.1 URL generation

The programme must generate URLs from the collection plan rather than storing every URL separately.

For each range and page number, it should combine:

- `base_url`;
- shared filters;
- date range;
- page number.

For example, for year 2025 page 1:
```
text
base_url = https://archiveofourown.org/works
date_from = 2025-01-01
date_to = 2025-12-31
page = 1
```
Generated URL:
```
text
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=F&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2025-01-01&work_search[date_to]=2025-12-31&work_search[query]=&work_search[language_id]=en&commit=Sort+and+Filter&tag_id=Original+Work&page=1
```
URL encoding can be handled by Python URL utilities.

### 8.2 Page identifier

The page ID must use the format:
```
text
<year>_<page:04d>
```
Examples:
```
text
2026_0001
2025_3132
2019_0531
```
The page ID is used for:

- output filename;
- manifest item ID;
- logging;
- `--start-page-id`.

### 8.3 Output filename

For page ID:
```
text
2025_0120
```
the output path must be:
```
text
corpus/01_ao3_list_pages/2025/2025_0120.html
```
### 8.4 Existing files

If the output HTML file already exists and `--reprocess` is not enabled:

- do not request the page from AO3;
- mark the page as `skipped_existing`;
- log the skip;
- include the page in the manifest.

If `--reprocess` is enabled:

- request the page again;
- overwrite the existing HTML file if capture succeeds.

### 8.5 Page readiness

For each page, the programme must wait until:

1. the browser reports:

   ```javascript
   document.readyState === "complete"
   ```

2. a `<body>` element is present;
3. AO3 Terms of Service prompt has been handled if present;
4. at least one AO3 work item is present:

   ```css
   ol.work.index.group li.work
   ```

If the expected selector does not appear before timeout, the page capture attempt fails.

### 8.6 Page validation

After readiness, the programme should collect minimal page validation details from the DOM:

- document title;
- main heading text, if available;
- number of `li.work` items;
- whether a TOS prompt was handled;
- current browser URL.

A page should be considered valid if:

- at least one `li.work` item exists;
- the main list container exists;
- the page title or heading is consistent with an AO3 works list.

For the Phase 1 ranges, a page with zero work items should be treated as a failure.

### 8.7 HTML saving

The programme must save `driver.page_source` as UTF-8 encoded HTML.

It should write to a temporary file first and then atomically replace the target file where possible.

Suggested pattern:
```
text
2025_0120.html.tmp
2025_0120.html
```
This reduces risk of corrupt partial files if the process is interrupted during file writing.

---

## 9. AO3 Terms of Service Consent Handling

AO3 may show a Terms of Service consent prompt.

The programme must handle this prompt automatically when it appears.

The consent handler should:

1. Check if `#tos_prompt` exists and is visible.
2. If present:
   - click the checkbox with ID `tos_agree`;
   - click the checkbox with ID `data_processing_agree`;
   - wait until the `accept_tos` button is enabled;
   - click the button with ID `accept_tos`;
   - wait until `#tos_prompt` disappears or is no longer visible.
3. Return whether the prompt was handled.

The programme should keep one browser session open for the whole run, so this prompt should usually only need handling once.

The manifest should record at page level whether the prompt was handled for that page:
```
json
"tos_prompt_handled": true
```
or:
```
json
"tos_prompt_handled": false
```
---

## 10. Browser and Selenium Behaviour

### 10.1 One browser session per run

The programme should create one Selenium browser session and reuse it across all planned pages.

Benefits:

- lower browser startup overhead;
- faster capture;
- AO3 consent status persists;
- fewer repeated browser initialisations;
- better EC2 performance.

### 10.2 Browser shutdown

The programme must call `driver.quit()` in all cases where a driver has been created, including:

- successful completion;
- page-level failures;
- configuration errors after browser creation;
- keyboard interruption;
- unexpected file-system errors.

### 10.3 Sequential capture

The first implementation must capture pages sequentially.

Parallel browser capture is out of scope for v1.

If `--workers` is not `1`, the programme must fail with a configuration error.

### 10.4 Chrome configuration

For Chrome in headless mode, use:
```
text
--headless=new
--disable-gpu
--window-size=1920,1080
```
When `--chrome-server-flags` is enabled, also use:
```
text
--no-sandbox
--disable-dev-shm-usage
```
### 10.5 Firefox configuration

For Firefox in headless mode, use:
```
text
--headless
```
### 10.6 Selenium Manager

The implementation may rely on Selenium Manager to locate or download the necessary browser driver.

If browser setup fails, the programme must exit with a configuration error.

---

## 11. Politeness and Rate Limiting

The programme must include rate limiting between page requests.

Default suggestion:
```
text
--request-delay 3
--request-jitter 1
```
The delay should be applied after every attempted page capture, whether successful or failed, unless the programme is exiting.

Effective wait time:
```
text
request_delay + random value between 0 and request_jitter
```
Example:
```
text
3.0 to 4.0 seconds
```
This is intended to reduce unnecessary load on AO3 and make the production run more respectful.

---

## 12. JSON Manifest Design

### 12.1 Manifest structure

The manifest must use this general structure:
```
json
{
  "run_metadata": {
    "run_id": "20261012T143012Z",
    "tool_name": "capture_ao3_lists.py",
    "tool_version": "v1",
    "start_time": "2026-10-12T14:30:12Z",
    "end_time": "2026-10-12T14:35:42Z",
    "test_mode": true,
    "test_limit": 5,
    "reprocess": false,
    "workers": 1,
    "collection_plan": "corpus/00_sources/ao3_list_collection_plan.json",
    "output_dir": "corpus/01_ao3_list_pages",
    "log_file": "corpus/01_ao3_list_pages/capture_ao3_lists.log",
    "manifest_file": "corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json",
    "interrupted": false,
    "config": {
      "browser": "chrome",
      "headless": true,
      "chrome_server_flags": true,
      "timeout_seconds": 30,
      "max_retries": 2,
      "retry_delay_seconds": 10,
      "request_delay_seconds": 3,
      "request_jitter_seconds": 1,
      "start_page_id": null
    },
    "plan_summary": {
      "range_order": "descending_year",
      "page_order_within_year": "ascending_page",
      "years": [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019],
      "total_pages_in_plan": 15044,
      "total_expected_works": 300819
    },
    "summary": {
      "selected_pages": 15044,
      "planned_attempts": 5,
      "attempted": 5,
      "succeeded": 5,
      "failed": 0,
      "skipped_existing": 0
    }
  },
  "pages": [
    {
      "page_id": "2026_0001",
      "year": 2026,
      "page": 1,
      "url": "https://archiveofourown.org/works?...",
      "current_url": "https://archiveofourown.org/works?...",
      "output_path": "corpus/01_ao3_list_pages/2026/2026_0001.html",
      "status": "success",
      "error": null,
      "retries": 0,
      "duration_seconds": 3.281,
      "start_time": "2026-10-12T14:30:15Z",
      "end_time": "2026-10-12T14:30:18Z",
      "validation": {
        "title": "Original Work - Works | Archive of Our Own",
        "heading": "1 - 20 of ... Works in Original Work",
        "work_items_detected": 20,
        "tos_prompt_handled": true
      }
    }
  ]
}
```
### 12.2 Required page statuses

The following statuses must be supported:

| Status | Meaning |
|---|---|
| `success` | Page was captured and saved successfully |
| `failed` | Page capture was attempted but failed |
| `failed_validation` | Page loaded but expected AO3 list content was missing |
| `skipped_existing` | Output HTML file already existed and `--reprocess` was not enabled |

### 12.3 Error field

The `error` field must be:

- `null` when there is no error;
- a short string when an error occurs.

Example:
```
json
{
  "page_id": "2026_0001",
  "status": "failed_validation",
  "error": "Expected selector ol.work.index.group li.work was not found before timeout"
}
```
### 12.4 Partial manifests

If interrupted, the manifest should include:
```
json
"interrupted": true
```
inside `run_metadata`.

Completed, failed, and skipped results collected before interruption must be written.

---

## 13. Logging Specification

The programme must write an append-only log file.

Default:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists.log
```
### Log format

Each line should follow this format:
```
text
[YYYY-MM-DD HH:MM:SS] LEVEL  message
```
Example:
```
text
[2026-10-12 14:30:12] INFO  Starting capture_ao3_lists.py run_id=20261012T143012Z
```
### Required log events

The programme must log:

- startup;
- run ID;
- collection plan path;
- output directory;
- log file path;
- manifest file path;
- selected browser;
- headless status;
- Chrome server flags status;
- test mode status;
- test limit;
- reprocess setting;
- start page ID, if provided;
- timeout;
- max retries;
- retry delay;
- request delay and jitter;
- collection plan summary;
- year order;
- total pages in plan;
- number of skipped existing pages;
- number of planned page captures;
- each skipped existing page;
- each page capture attempt;
- each AO3 TOS prompt handling event;
- each successful capture;
- each failed capture;
- each retry;
- manifest write paths;
- end-of-run summary;
- keyboard interrupts;
- validation/configuration errors;
- browser setup failures.

### Example log lines
```
text
[2026-10-12 14:30:12] INFO  Starting capture_ao3_lists.py run_id=20261012T143012Z
[2026-10-12 14:30:12] INFO  Collection plan: corpus/00_sources/ao3_list_collection_plan.json
[2026-10-12 14:30:12] INFO  Output directory: corpus/01_ao3_list_pages
[2026-10-12 14:30:12] INFO  Browser: chrome; headless=True
[2026-10-12 14:30:12] INFO  Test mode: True; test_limit=5
[2026-10-12 14:30:13] INFO  Loaded plan years: 2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019
[2026-10-12 14:30:13] INFO  Total pages in plan: 15044
[2026-10-12 14:30:14] INFO  Capturing 2026_0001 https://archiveofourown.org/works?...
[2026-10-12 14:30:18] INFO  AO3 Terms of Service prompt accepted
[2026-10-12 14:30:19] INFO  SUCCESS 2026_0001 -> corpus/01_ao3_list_pages/2026/2026_0001.html work_items=20
[2026-10-12 14:35:42] INFO  Wrote latest manifest: corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
[2026-10-12 14:35:42] INFO  Finished run: succeeded=5 failed=0 skipped_existing=0
```
---

## 14. Error Handling and Resiliency

### 14.1 Configuration errors

Configuration errors must stop the programme before page capture begins.

Examples:

- collection plan missing;
- invalid JSON;
- invalid page ranges;
- output directory cannot be created;
- invalid command-line arguments;
- unsupported browser;
- browser cannot be started;
- start page ID not found.

The programme must exit non-zero.

### 14.2 Per-page errors

Per-page errors must not stop the full run.

Examples:

- page load timeout;
- AO3 transient error;
- browser timeout;
- expected selector missing;
- TOS prompt cannot be accepted;
- file write error for one page;
- unexpected Selenium exception for one page.

For each per-page error:

- retry up to `--max-retries`;
- if still failing, mark the page as `failed` or `failed_validation`;
- log the error;
- continue to the next page.

### 14.3 Keyboard interruption

If the user interrupts the programme with `Ctrl+C`, the programme must:

- stop processing;
- quit the browser;
- mark the run as interrupted in the manifest;
- write a partial manifest with completed results so far;
- log the interruption;
- exit non-zero.

### 14.4 Exit codes

The programme must use the following exit-code conventions:

| Exit code | Meaning |
|---:|---|
| `0` | Completed with no failed attempted captures |
| `1` | Completed, but one or more attempted captures failed |
| `2` | Configuration or validation error |
| `130` | Interrupted by user |

Skipped existing files are not failures.

---

## 15. Docstrings and In-code Documentation

The implementation must include clear docstrings.

### 15.1 Module-level docstring

At the top of `capture_ao3_lists.py`, include a module-level docstring explaining:

- purpose of the programme;
- expected collection plan file;
- output HTML directory;
- use of Selenium;
- supported browsers;
- AO3 Terms of Service prompt handling;
- default test mode;
- resumability behaviour;
- example commands;
- manifest and logging outputs.

Suggested module docstring:
```
python
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
```
### 15.2 Function docstrings

All major functions must include docstrings describing:

- purpose;
- parameters;
- return values;
- whether the function performs I/O;
- error behaviour.

At minimum, docstrings are required for:

- `parse_args`
- `setup_logging`
- `validate_args`
- `load_collection_plan`
- `build_ao3_list_url`
- `plan_captures`
- `create_driver`
- `accept_ao3_tos_if_present`
- `wait_for_ao3_list_page`
- `capture_one_page`
- `write_manifests`
- `main`

---

## 16. Suggested Constants

The implementation should define constants near the top of the file:
```
python
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

DEFAULT_REQUEST_DELAY_SECONDS = 3
DEFAULT_REQUEST_JITTER_SECONDS = 1

AO3_LIST_READY_SELECTOR = "ol.work.index.group li.work"
AO3_TOS_PROMPT_SELECTOR = "#tos_prompt"
AO3_TOS_CHECKBOX_SELECTOR = "#tos_agree"
AO3_DATA_PROCESSING_CHECKBOX_SELECTOR = "#data_processing_agree"
AO3_TOS_ACCEPT_BUTTON_SELECTOR = "#accept_tos"

EXIT_SUCCESS = 0
EXIT_CAPTURE_FAILURE = 1
EXIT_CONFIGURATION_ERROR = 2
EXIT_INTERRUPTED = 130
```
---

## 17. Development Notes

### Initial implementation scope

The first implementation should prioritise:

- correct sequential execution;
- reliable URL generation from the JSON plan;
- stable Selenium capture;
- AO3 Terms of Service handling;
- page-specific readiness checks;
- safe resumability;
- append-only logging;
- robust manifest output;
- clear error handling;
- portability to EC2.

### Out of scope for v1

The following are out of scope for the first implementation:

- extracting AO3 work metadata;
- exporting JSONL or Excel metadata;
- scraping full works;
- extracting corpus text;
- parallel capture;
- browser session rotation;
- advanced Cloudflare/challenge handling;
- authenticated AO3 capture.

### Recommended implementation approach

Use Selenium plus Python standard-library modules where possible:

- `argparse`
- `json`
- `logging`
- `pathlib`
- `datetime`
- `time`
- `random`
- `sys`
- `urllib.parse`
- `typing`

Selenium is required for browser automation.

No Beautiful Soup dependency is required for `capture_ao3_lists.py` because the programme only performs minimal DOM validation through Selenium and saves HTML.

Metadata extraction should be implemented later in a separate offline parser.

---

## 18. Acceptance Criteria

The programme is considered complete when the following conditions are met:

1. Running:

   ```bash
   python capture_ao3_lists.py
   ```

   performs a test run of up to 5 planned missing pages.

2. The programme reads:

   ```text
   corpus/00_sources/ao3_list_collection_plan.json
   ```

3. The collection plan covers the Phase 1 range:

   ```text
   2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019
   ```

4. The programme preserves the range order defined in the collection plan.

5. The default Phase 1 plan processes years in descending order from 2026 to 2019.

6. Pages are processed in ascending order within each year.

7. The programme creates the output directory if needed:

   ```text
   corpus/01_ao3_list_pages/
   ```

8. The programme creates year subdirectories if needed.

9. Each captured page is saved as:

   ```text
   corpus/01_ao3_list_pages/<year>/<year>_<page:04d>.html
   ```

10. Existing `.html` files are skipped unless `--reprocess` is used.

11. The programme does not create `.txt` files.

12. The programme does not extract full work metadata.

13. The programme generates AO3 URLs from the collection plan rather than requiring every URL to be listed manually.

14. The programme supports Chrome by default.

15. The programme supports Firefox with:

   ```bash
   --browser firefox
   ```

16. The programme runs in headless mode by default.

17. The programme can run on EC2 using Chrome headless/server flags.

18. The programme handles AO3’s Terms of Service prompt when present.

19. The programme waits for AO3 list content using:

   ```text
   ol.work.index.group li.work
   ```

20. The programme records the number of detected work items for each captured page.

21. Failed page captures do not stop the full batch.

22. The programme retries failed captures according to `--max-retries`.

23. The programme supports starting from a specific page ID with:

   ```bash
   --start-page-id 2025_0120
   ```

24. If `--start-page-id` is not found in the planned page list, the programme exits with a configuration error.

25. The programme applies a configurable delay between requests.

26. The programme writes an append-only log file at:

   ```text
   corpus/01_ao3_list_pages/capture_ao3_lists.log
   ```

27. The programme writes a latest manifest at:

   ```text
   corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
   ```

28. A timestamped per-run manifest is also created for each execution.

29. The manifest records:
   - run metadata;
   - configuration;
   - collection plan path;
   - output directory;
   - year order;
   - page order;
   - per-page status;
   - generated URLs;
   - output paths;
   - validation metadata;
   - errors;
   - timings;
   - summary counts.

30. The programme exits with:
   - `0` if all attempted captures succeed or are skipped;
   - `1` if any attempted capture fails;
   - `2` for configuration errors;
   - `130` for keyboard interruption.

---

## 19. Short README Section

The following section can be added to project documentation.

### Capture AO3 list pages

The `capture_ao3_lists.py` programme captures AO3 list pages for Phase 1 data collection.

It reads the collection plan:
```
text
corpus/00_sources/ao3_list_collection_plan.json
```
The plan defines yearly AO3 list ranges for English works tagged as `Original Work`, excluding crossovers, from 2026 down to 2019.

Recent years are captured first because AO3 users are more active in recent periods, making those list ranges more susceptible to change.

Default test run:
```
bash
python capture_ao3_lists.py
```
This captures up to 5 planned missing list pages.

Full run:
```
bash
python capture_ao3_lists.py --no-test-mode
```
To resume from a specific page ID:
```
bash
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2025_0120
```
The programme saves rendered HTML files as:
```
text
corpus/01_ao3_list_pages/<year>/<year>_<page:04d>.html
```
Example:
```
text
corpus/01_ao3_list_pages/2025/2025_0001.html
```
The programme is safe to re-run: existing pages are skipped by default.

To force re-capture:
```
bash
python capture_ao3_lists.py --no-test-mode --reprocess
```
The programme writes:
```
text
corpus/01_ao3_list_pages/capture_ao3_lists.log
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```
A timestamped per-run manifest is also created for each execution.

For EC2:
```
bash
nohup bash run_python_ec2.sh \
  capture_ao3_lists.py \
    --no-test-mode \
    --browser chrome \
    --request-delay 3 \
    --request-jitter 1 \
> process_output.log 2>&1 &
```
This programme only captures list-page HTML. Metadata extraction is handled later by a separate offline processing step.
