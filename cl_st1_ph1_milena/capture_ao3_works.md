# `capture_ao3_works.py` — Programme Specification for Development

## 1. High-level Functionality Specification

### Programme Summary

`capture_ao3_works.py` is a batch-processing programme that captures selected Archive of Our Own (AO3) work pages as rendered HTML files for the Phase 1 data collection workflow.

This programme implements the first stage of the **Works Collection** subphase:

1. **Capture AO3 work pages** — implemented by `capture_ao3_works.py`.
2. **Extract AO3 works text** — implemented later by a separate programme.

`capture_ao3_works.py` must not extract work text and must not produce text files. Its sole responsibility is to capture and save rendered AO3 full-work HTML pages in a reproducible, resumable, auditable way.

The programme reads a work collection plan generated from the selected works:

```text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```

The collection plan is produced upstream from the canonical AO3 works metadata. The work metadata remains the single source of information for deciding which works should be collected. The capture programme does not decide the corpus sample; it only executes the supplied plan.

Each NDJSON record in the collection plan represents one AO3 work to capture. The required fields are:

- `work_id`;
- `full_work_url`;
- `date_updated`.

The programme saves each captured work page as:

```text
corpus/02_ao3_work_pages/<year>/<work_id>.html
```

where `<year>` is derived from the `date_updated` field.

For example, a plan record with:

```json
{
  "work_id": "85198816",
  "full_work_url": "https://archiveofourown.org/works/85198816?view_adult=true&view_full_work=true",
  "date_updated": "2026-10-13"
}
```

must be captured to:

```text
corpus/02_ao3_work_pages/2026/85198816.html
```

The programme uses Selenium to run a real browser in headless mode. Chrome is the default browser, and Firefox is supported through a command-line option.

The programme must handle AO3’s Terms of Service consent prompt when it appears, wait for work-page content to be available, validate that the expected AO3 work structure is present, and then save the rendered HTML.

The programme must configure Selenium page-load and script timeouts from the command-line timeout setting. Local Selenium/WebDriver communication timeouts must be treated as retryable per-work failures rather than full-run crashes.

The programme must be safe to re-run: existing HTML files are skipped by default unless `--reprocess` is provided.

The programme writes an append-only log file and JSON manifests describing run-level metadata and work-level capture status.

---

## 2. Position in the Phase 1 Workflow

### 2.1 Upstream source of truth

The canonical upstream metadata is:

```text
corpus/00_sources/ao3_works_metadata/
```

The work metadata is the single source of information for the population of available works and their metadata.

The notebook:

```text
cl_st1_ph1_milena.ipynb
```

is responsible for selecting the subset of works to capture and for writing the collection plan.

### 2.2 Input collection plan

The capture programme reads:

```text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```

The NDJSON collection plan is the immediate input to `capture_ao3_works.py`.

The programme must not read directly from the full metadata output unless explicitly configured in a future version. For v1, it should only consume the prepared work collection plan.

### 2.3 Downstream output

The output of this programme is raw captured HTML:

```text
corpus/02_ao3_work_pages/
```

These HTML files are the input to the later **Extract AO3 works text** stage.

---

## 3. Key Behaviours

The programme must implement the following behaviours:

- Read an NDJSON work collection plan.
- Treat the work collection plan as the direct list of capture targets.
- Require each plan record to contain:
    - `work_id`;
    - `full_work_url`;
    - `date_updated`.
- Validate that `work_id` is a non-empty string or integer-like value.
- Validate that `full_work_url` is a non-empty AO3 URL.
- Validate that `date_updated` is an ISO-style date in `YYYY-MM-DD` format.
- Derive the output year from `date_updated`.
- Preserve the work order from the NDJSON plan.
- Capture rendered AO3 work pages with Selenium.
- Use the supplied `full_work_url` exactly as the URL to request.
- Expect `full_work_url` to include:
    - `view_adult=true`;
    - `view_full_work=true`.
- Do not construct work URLs from `work_id` in normal operation.
- Use Chrome by default.
- Support Firefox as an alternative browser.
- Run headless by default.
- Configure Selenium page-load and script timeouts from the command-line timeout setting.
- Use one browser session per run for efficiency and to preserve AO3 consent state.
- Handle the AO3 Terms of Service consent prompt if it appears.
- Wait for AO3 work-page content using work-specific readiness checks.
- Save only HTML files.
- Do not produce scraped `.txt` files.
- Do not extract work text in this programme.
- Do not re-extract or update metadata in this programme.
- Record basic validation information such as:
    - page title;
    - main heading or work title, if available;
    - byline, if available;
    - whether the work skin was detected;
    - whether the chapters container was detected;
    - number of detected chapter elements;
    - whether work metadata was detected;
    - whether a TOS prompt was handled.
- Skip existing HTML files by default.
- Reprocess existing HTML files only when `--reprocess` is provided.
- Use test mode by default, limiting capture to 5 planned works.
- Support starting from a specific work ID using `--start-work-id`.
- Fail fast if duplicate `work_id` values are found in the input plan.
- Continue processing remaining works if one work capture fails.
- Treat ordinary Selenium, browser, local WebDriver communication, page-load timeout, validation, and file-write failures as work-level failures rather than full-run crashes.
- Retry failed work captures according to the configured retry policy.
- Apply a configurable delay between work captures.
- Optionally apply random jitter to the inter-work delay.
- Record progress and errors in an append-only log file.
- Produce compact and meaningful error summaries for logs and manifests.
- Avoid reducing Selenium errors to unhelpful stack-frame fragments such as `#17 ... <unknown>`.
- Produce a JSON manifest with run-level metadata and work-level results.
- Write both:
    - a timestamped per-run manifest;
    - a latest manifest that is overwritten on each run.
- Exit with status code `0` only when all attempted captures succeed or are skipped.
- Exit with a non-zero status code if:
    - one or more attempted captures fail;
    - there is a configuration error;
    - there is an input validation error;
    - the run is interrupted.

---

## 4. Input / Output Specification

## 4.1 Input

### Work collection plan file

Default path:

```text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```

The collection plan is an NDJSON file: one JSON object per line.

Each line represents one planned AO3 work-page capture.

### Required fields

Each record must contain:

| Field           | Required | Type                         | Description                                                                                  |
|-----------------|---------:|------------------------------|----------------------------------------------------------------------------------------------|
| `work_id`       |      yes | string or integer-like value | AO3 work identifier. Used as the stable capture identifier and output filename stem.         |
| `full_work_url` |      yes | string                       | URL to the full AO3 work page. Should already include `view_adult=true&view_full_work=true`. |
| `date_updated`  |      yes | string                       | Machine-readable date in `YYYY-MM-DD` format. Used to derive the output year.                |

### Optional fields

The plan may contain additional metadata fields, such as:

- `title`;
- `author_name`;
- `work_url`;
- `collection_year`;
- `language`;
- `words`;
- `chapters_current`;
- `chapters_total`;
- `source_page_id`;
- `source_html_path`;
- `extraction_run_id`.

The programme may include selected optional values in the manifest for provenance, but it must not require them.

### Example input record

```json
{"work_id":"85198816","full_work_url":"https://archiveofourown.org/works/85198816?view_adult=true&view_full_work=true","date_updated":"2026-10-13","title":"Boys Don't Cry","author_name":"sol_starzz"}
```

### Input order

The programme must preserve the record order from the NDJSON file.

The plan generation process is responsible for deciding the selection and ordering strategy. `capture_ao3_works.py` must not reorder the input by year, work ID, title, or any other field.

### Duplicate work IDs

For v1, duplicate `work_id` values are treated as a configuration/input error.

If duplicate work IDs are found:

- the programme must fail fast before creating a browser session;
- no network capture should begin;
- the error message must report at least:
    - the duplicated `work_id`;
    - the first line number where it appeared;
    - the later line number where it appeared again.

This avoids ambiguous overwriting because the output path is based on `work_id`.

---

## 4.2 Output

### HTML output directory

Default path:

```text
corpus/02_ao3_work_pages/
```

The programme must create this directory if it does not already exist.

### Per-year output directories

The programme must save pages under year-specific subdirectories derived from `date_updated`:

```text
corpus/02_ao3_work_pages/2026/
corpus/02_ao3_work_pages/2025/
corpus/02_ao3_work_pages/2024/
corpus/02_ao3_work_pages/2023/
corpus/02_ao3_work_pages/2022/
corpus/02_ao3_work_pages/2021/
corpus/02_ao3_work_pages/2020/
corpus/02_ao3_work_pages/2019/
```

The programme must not hard-code the set of valid years. It should accept any valid four-digit year derived from `date_updated`, while still recording the years encountered in the manifest.

### Per-work HTML output

Each captured work page must be saved as:

```text
<output_dir>/<year>/<work_id>.html
```

Examples:

```text
corpus/02_ao3_work_pages/2026/85198816.html
corpus/02_ao3_work_pages/2025/76796521.html
corpus/02_ao3_work_pages/2020/12345678.html
```

### No text output

The programme must **not** save `.txt` versions of the works.

Text extraction is outside the scope of `capture_ao3_works.py`.

### Log file

Default path:

```text
corpus/02_ao3_work_pages/capture_ao3_works.log
```

The log file must be:

- plain text;
- UTF-8 encoded;
- append-only;
- line-oriented.

### Manifest files

The programme must write two manifest files.

#### Latest manifest

Default path:

```text
corpus/02_ao3_work_pages/capture_ao3_works_manifest.json
```

This file is overwritten at the end of each run.

#### Per-run manifest

A timestamped copy must also be written using the run ID.

Filename pattern:

```text
capture_ao3_works_manifest_<run_id>.json
```

Example:

```text
corpus/02_ao3_work_pages/capture_ao3_works_manifest_20261014T143012Z.json
```

---

## 5. Command-line Interface

## 5.1 Default usage

```bash
python capture_ao3_works.py
```

Default behaviour:

- collection plan: `corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson`
- output directory: `corpus/02_ao3_work_pages/`
- log file: `corpus/02_ao3_work_pages/capture_ao3_works.log`
- manifest file: `corpus/02_ao3_work_pages/capture_ao3_works_manifest.json`
- browser: `chrome`
- headless mode: enabled
- Chrome server flags: enabled
- test mode: enabled
- test limit: 5 works
- reprocess: disabled
- existing `.html` files are skipped
- workers: 1 / sequential processing
- timeout: 30 seconds for AO3 readiness checks
- Selenium page-load timeout: derived from `--timeout`
- Selenium script timeout: derived from `--timeout`
- request delay: enabled
- AO3 Terms of Service prompt handling: enabled
- no start-work filter

---

## 5.2 Required arguments

There are no required command-line arguments if all default paths are used.

However, all important paths and processing controls must be configurable.

---

## 5.3 Optional arguments

### Collection plan path

```bash
--collection-plan PATH
```

Default:

```text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```

Description:

Path to the NDJSON work collection plan file.

---

### Output directory

```bash
--output-dir PATH
```

Default:

```text
corpus/02_ao3_work_pages/
```

Description:

Directory where captured AO3 work HTML files will be saved.

---

### Browser

```bash
--browser chrome
--browser firefox
```

Default:

```text
chrome
```

Description:

Browser to use for Selenium capture.

Supported values:

- `chrome`
- `firefox`

---

### Headless mode

```bash
--headless
--no-headless
```

Default:

```text
--headless
```

Description:

Run the browser in headless mode by default. This is required for production use on EC2.

---

### Chrome server flags

```bash
--chrome-server-flags
--no-chrome-server-flags
```

Default:

```text
--chrome-server-flags
```

Description:

When using Chrome, include options suitable for headless Linux/EC2 execution, such as:

```text
--no-sandbox
--disable-dev-shm-usage
--disable-gpu
--window-size=1920,1080
```

---

### Test mode

```bash
--test-mode
--no-test-mode
```

Default:

```text
--test-mode
```

Description:

When test mode is enabled, the programme processes only a limited number of planned missing work captures.

---

### Test limit

```bash
--test-limit N
```

Default:

```text
5
```

Description:

Maximum number of works to attempt when test mode is enabled.

Must be a positive integer.

Example:

```bash
python capture_ao3_works.py --test-limit 10
```

---

### Reprocess existing works

```bash
--reprocess
```

Default:

```text
False
```

Description:

When omitted, the programme skips any work whose output `.html` file already exists.

When provided, the programme captures the work again and overwrites the existing output file if capture succeeds.

Example:

```bash
python capture_ao3_works.py --reprocess
```

---

### Start work ID

```bash
--start-work-id WORK_ID
```

Default:

```text
None
```

Description:

Optional work identifier from which to start planning captures.

When `--start-work-id` is provided, the programme must preserve the collection plan order but ignore all works that occur before the specified work ID. The specified work itself must be included in the planning step.

Example:

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --start-work-id 85198816
```

If the requested work ID is not found in the planned work list, the programme must fail fast with a configuration error.

---

### Log file

```bash
--log-file PATH
```

Default:

```text
corpus/02_ao3_work_pages/capture_ao3_works.log
```

Description:

Path to the append-only log file.

---

### Manifest file

```bash
--manifest-file PATH
```

Default:

```text
corpus/02_ao3_work_pages/capture_ao3_works_manifest.json
```

Description:

Path to the latest manifest file. The per-run timestamped manifest should be written next to this file.

---

### Workers

```bash
--workers N
```

Default:

```text
1
```

Description:

Number of worker processes.

For the current implementation, sequential execution with `--workers 1` is required. The architecture may allow parallel execution later, but parallel browser-based scraping is not recommended in the first production version.

Must be a positive integer.

If `--workers` is not `1`, the programme must fail with a configuration error.

---

### Timeout

```bash
--timeout SECONDS
```

Default suggestion:

```text
30
```

Description:

Maximum allowed time, in seconds, for AO3 work-page readiness checks and related browser interactions.

The value is also used to configure Selenium browser timeouts:

- the page-load timeout should be derived from `--timeout`, for example `timeout * 4`;
- the script timeout should be set to `--timeout`.

If a page load, WebDriver command, local WebDriver communication, or readiness check times out:

- treat the failure as a retryable per-work failure;
- retry according to `--max-retries`;
- if all attempts fail, mark the work as failed;
- log a compact error summary;
- continue with the next work.

---

### Maximum retries

```bash
--max-retries N
```

Default suggestion:

```text
2
```

Description:

Number of retry attempts after a failed capture.

For example, with `--max-retries 2`, each failed work may be attempted three times in total:

1. initial attempt;
2. first retry;
3. second retry.

Must be zero or a positive integer.

---

### Retry delay

```bash
--retry-delay SECONDS
```

Default suggestion:

```text
10
```

Description:

Delay between failed capture attempts.

Must be zero or a positive number.

---

### Request delay

```bash
--request-delay SECONDS
```

Default suggestion:

```text
3
```

Description:

Delay after each attempted work capture before the next work is requested.

This is a politeness control to avoid placing unnecessary load on AO3.

---

### Request jitter

```bash
--request-jitter SECONDS
```

Default suggestion:

```text
1
```

Description:

Maximum random additional delay added to `--request-delay`.

For example, with:

```bash
--request-delay 3 --request-jitter 1
```

the programme waits between 3 and 4 seconds between work requests.

---

## 5.4 Example commands

### Small default test run

```bash
python capture_ao3_works.py
```

Captures up to 5 planned missing works using the default collection plan.

---

### Test run with 10 works

```bash
python capture_ao3_works.py --test-limit 10
```

---

### Test run from a specific work ID

```bash
python capture_ao3_works.py \
  --test-limit 10 \
  --start-work-id 85198816
```

---

### Full production run

```bash
python capture_ao3_works.py --no-test-mode
```

---

### Full production run from a specific work ID

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --start-work-id 85198816
```

---

### Full production run with explicit paths

```bash
python capture_ao3_works.py \
  --collection-plan corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson \
  --output-dir corpus/02_ao3_work_pages \
  --no-test-mode
```

---

### Full production run with Firefox

```bash
python capture_ao3_works.py \
  --browser firefox \
  --no-test-mode
```

---

### Re-capture works even if files already exist

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --reprocess
```

---

### More conservative production run

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --request-delay 5 \
  --request-jitter 2 \
  --max-retries 3 \
  --retry-delay 20
```

---

### Resume after transient AO3 or WebDriver instability

If a production run encounters repeated transient page-load or local WebDriver timeouts, resume from the first missing or failed work with slower request pacing and more retries:

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --start-work-id 85198816 \
  --request-delay 6 \
  --request-jitter 4 \
  --max-retries 4 \
  --retry-delay 20 \
  --timeout 45
```

Existing successfully captured works will still be skipped unless `--reprocess` is provided.

---

### EC2 full run with `nohup`

```bash
nohup bash run_python_ec2.sh \
  capture_ao3_works.py \
    --no-test-mode \
    --browser chrome \
    --request-delay 3 \
    --request-jitter 1 \
> process_output.log 2>&1 &
```

---

### EC2 full run from a specific work ID

```bash
nohup bash run_python_ec2.sh \
  capture_ao3_works.py \
    --no-test-mode \
    --browser chrome \
    --start-work-id 85198816 \
    --request-delay 3 \
    --request-jitter 1 \
> process_output.log 2>&1 &
```

---

## 6. Argument and Input Validation

The programme must fail fast with a clear message if:

- the collection plan file does not exist;
- the collection plan path is not a file;
- the collection plan is empty;
- the collection plan contains invalid JSON on any line;
- any plan record is not a JSON object;
- any plan record is missing one of:
    - `work_id`;
    - `full_work_url`;
    - `date_updated`;
- `work_id` is empty;
- `work_id` contains path separators or unsafe filename characters;
- duplicate `work_id` values are present;
- `full_work_url` is empty;
- `full_work_url` is not an HTTP/HTTPS URL;
- `full_work_url` does not point to `archiveofourown.org` or an accepted AO3 host;
- `full_work_url` does not appear to reference an AO3 work path;
- `date_updated` is empty;
- `date_updated` is not in `YYYY-MM-DD` format;
- the year cannot be derived from `date_updated`;
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
- `--start-work-id` is provided but empty;
- `--start-work-id` is provided but not found in the planned work list;
- Selenium cannot initialise the selected browser.

A validation error should:

- be printed clearly to the console;
- be written to the log if logging has already been configured;
- cause the programme to exit with a non-zero status code.

---

## 7. Environment and Configuration

### Required Python packages

The programme requires Python, Selenium, and urllib3.

Suggested Python dependencies:

```text
selenium
urllib3
```

`urllib3` is used so that local Selenium/WebDriver read timeouts can be caught explicitly and treated as retryable work-level failures.

The programme otherwise uses Python standard-library modules where possible.

Suggested standard-library modules:

- `argparse`;
- `json`;
- `logging`;
- `pathlib`;
- `datetime`;
- `time`;
- `random`;
- `re`;
- `sys`;
- `urllib.parse`;
- `typing`.

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

```text
--headless=new
--no-sandbox
--disable-dev-shm-usage
--disable-gpu
--window-size=1920,1080
```

For Firefox on EC2, the browser should run with:

```text
--headless
```

### Secrets and credentials

This programme does not require API keys or secret credentials.

For this first implementation, AO3 cookies are not required. AO3 Terms of Service consent should be handled through Selenium interaction.

Authenticated AO3 capture is out of scope for v1.

---

## 8. Core Processing Architecture

## 8.1 High-level flow

The programme must follow this workflow:

1. **Startup**
    - Parse command-line arguments.
    - Generate a UTC run ID.
    - Set up logging.
    - Validate command-line arguments.
    - Load and validate the NDJSON work collection plan.
    - Ensure output, log, and manifest directories exist.

2. **Planning**
    - Build the ordered list of planned works from the NDJSON input.
    - Preserve input order.
    - Validate every planned work.
    - Derive the output year from `date_updated`.
    - Compute output path as:

      ```text
      <output_dir>/<year>/<work_id>.html
      ```

    - If `--start-work-id` is provided:
        - locate the specified work ID;
        - ignore all works before it;
        - include the specified work and all following works;
        - fail fast if the specified work ID is not found.
    - For each selected work:
        - decide whether to skip or attempt capture.
    - If the file exists and `--reprocess` is not enabled:
        - mark the work as `skipped_existing`.
    - If the file does not exist or `--reprocess` is enabled:
        - plan the work for capture.
    - If test mode is enabled:
        - limit attempted captures to `--test-limit`.

3. **Browser setup**
    - Create one Selenium WebDriver instance for the run.
    - Use the selected browser.
    - Configure headless mode.
    - Configure EC2-safe Chrome flags when applicable.
    - Configure Selenium page-load timeout from the command-line timeout setting.
    - Configure Selenium script timeout from the command-line timeout setting.

4. **Execution**
    - For each planned work:
        - request `full_work_url` with Selenium;
        - wait for browser-level readiness;
        - handle AO3 Terms of Service prompt if it appears;
        - wait for AO3 work-page content;
        - validate expected work-page structure;
        - save HTML;
        - record work-level result.
    - If a work capture fails:
        - retry according to `--max-retries`;
        - if all attempts fail, mark the work as failed;
        - record a compact error summary;
        - continue to the next work.
    - Apply request delay and jitter between works.

5. **End-of-run summary**
    - Count:
        - total works in plan;
        - selected works after start-work filtering;
        - skipped existing works;
        - attempted works;
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

## 8.2 Separation of concerns

The implementation should be organised around the following responsibilities.

### CLI parsing

Responsible for:

- defining command-line arguments;
- applying defaults;
- returning a configuration object or namespace.

Suggested function:

```python
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the AO3 work capture programme."""
```

### Logging setup

Responsible for:

- creating the log directory;
- configuring append-only file logging;
- configuring console logging.

Suggested function:

```python
def setup_logging(log_file: Path) -> logging.Logger:
    """Configure append-only file logging and console logging."""
```

### Argument validation

Responsible for:

- checking paths;
- checking numeric arguments;
- checking supported browser selection;
- checking worker count;
- checking start work ID.

Suggested function:

```python
def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments before processing."""
```

### Collection plan loading

Responsible for:

- reading NDJSON;
- validating line-level JSON;
- validating required fields;
- detecting duplicate work IDs;
- preserving input order.

Suggested function:

```python
def load_collection_plan(plan_path: Path) -> list[dict]:
    """Load and validate the AO3 work collection plan from NDJSON."""
```

### Work date and path derivation

Responsible for:

- validating `date_updated`;
- deriving the output year;
- creating safe output paths.

Suggested functions:

```python
def derive_year_from_date_updated(date_updated: str) -> int:
    """Derive the four-digit year from an ISO-style date_updated value."""
```

```python
def make_output_path(output_dir: Path, work_id: str, date_updated: str) -> Path:
    """Create the target HTML path for a planned work."""
```

### Planning

Responsible for:

- applying `--start-work-id`;
- checking existing files;
- applying test limit.

Suggested function:

```python
def plan_captures(
    work_plan: list[dict],
    output_dir: Path,
    test_mode: bool,
    test_limit: int,
    reprocess: bool,
    start_work_id: str | None = None
) -> tuple[list[dict], list[dict], int]:
    """Create planned and skipped work capture records."""
```

### Browser creation

Responsible for:

- creating a Selenium WebDriver;
- selecting Chrome or Firefox;
- setting headless options;
- setting EC2/server-safe Chrome flags;
- setting a page-load timeout derived from `--timeout`;
- setting a script timeout derived from `--timeout`.

Suggested function:

```python
def create_driver(browser: str, headless: bool, chrome_server_flags: bool, timeout: int) -> webdriver.Remote:
    """Create a Selenium WebDriver for the requested browser."""
```

### AO3 consent handling

Responsible for:

- detecting AO3 Terms of Service prompt;
- clicking both checkboxes;
- clicking the accept button;
- waiting for the prompt to disappear.

Suggested function:

```python
def accept_ao3_tos_if_present(driver: webdriver.Remote, timeout: int) -> bool:
    """Accept the AO3 Terms of Service prompt if it is present."""
```

Return value:

- `True` if a prompt was detected and accepted;
- `False` if no prompt was present.

### AO3 work readiness wait

Responsible for:

- waiting for `document.readyState == "complete"`;
- waiting for `body`;
- accepting TOS prompt if present;
- waiting for work content.

Suggested function:

```python
def wait_for_ao3_work_page(driver: webdriver.Remote, timeout: int) -> dict:
    """Wait for an AO3 work page to be ready and return basic validation metadata."""
```

This function should wait for work-page selectors such as:

```text
#main.works-show
#workskin
#chapters
```

At least one robust work-content selector should be required. Recommended minimum readiness requirement:

```text
#workskin
```

The validation metadata should include values such as:

```python
{
    "title": "...",
    "work_title": "...",
    "byline": "...",
    "workskin_detected": True,
    "chapters_detected": True,
    "chapter_count_detected": 3,
    "work_metadata_detected": True,
    "tos_prompt_handled": True
}
```

### Error summarisation

Responsible for:

- converting exceptions into compact one-line strings suitable for logs and manifests;
- preferring meaningful exception text;
- avoiding unhelpful Selenium or ChromeDriver stack-frame fragments such as `#17 ... <unknown>`;
- falling back to the exception type name when no useful message is available.

Suggested function:

```python
def summarise_error(error: BaseException | str | None, max_length: int = 500) -> str:
    """Create a compact one-line error summary."""
```

### Single work capture

Responsible for:

- loading a URL;
- waiting for readiness;
- saving HTML;
- catching ordinary per-work failures;
- retrying failed attempts according to the configured retry policy;
- returning a structured result instead of raising for expected work-level failures.

Expected retryable per-work failures include:

- Selenium validation timeouts;
- Selenium browser or WebDriver exceptions;
- local Selenium/WebDriver read timeouts;
- JavaScript execution failures;
- file-write failures for the work.

Suggested function:

```python
def capture_one_work(
    driver: webdriver.Remote,
    work_item: dict,
    timeout: int,
    max_retries: int,
    retry_delay: float,
    logger: logging.Logger
) -> dict:
    """Capture one AO3 work page and return a structured manifest result."""
```

### Manifest writing

Responsible for writing:

- latest manifest;
- timestamped per-run manifest.

Suggested function:

```python
def write_manifests(
    manifest: dict,
    manifest_file: Path,
    run_id: str
) -> tuple[Path, Path]:
    """Write latest and per-run manifest files."""
```

### Main orchestration

Responsible for:

- coordinating all steps;
- logging;
- browser lifecycle;
- error handling;
- exit code.

Suggested function:

```python
def main() -> int:
    """Run the batch AO3 work capture workflow and return an exit code."""
```

---

## 9. AO3 Work Capture Behaviour

## 9.1 URL usage

The programme must use `full_work_url` from the collection plan as the URL to capture.

It must not normally reconstruct URLs from `work_id`.

The expected URL form is:

```text
https://archiveofourown.org/works/<work_id>?view_adult=true&view_full_work=true
```

However, the programme should not require exact query parameter order.

The programme should warn, but not necessarily fail, if `full_work_url` does not include `view_adult=true` or `view_full_work=true`, because the collection plan generation process is responsible for constructing the final URL. For v1, recommended behaviour is:

- fail if `full_work_url` is missing or malformed;
- warn if expected query parameters are missing;
- still use the supplied `full_work_url` exactly as the source of truth for capture.

### Rationale for `view_adult=true`

AO3 may show an adult-content warning for some works. Including:

```text
view_adult=true
```

acknowledges the warning in the URL and avoids a blocking interstitial page.

### Rationale for `view_full_work=true`

AO3 multi-chapter works can be displayed chapter-by-chapter or as a full work. Including:

```text
view_full_work=true
```

requests the entire work in one HTML page, which is required for later text extraction.

---

## 9.2 Work identifier

The work ID must be based on the `work_id` field.

The work ID is used for:

- output filename;
- manifest item ID;
- logging;
- `--start-work-id`.

Examples:

```text
85198816
76796521
65469301
```

The implementation should normalise `work_id` to a string internally.

The implementation must reject work IDs that contain unsafe filename characters, including:

```text
/
\
:
*
?
"
<
>
|
```

---

## 9.3 Output filename

For a work with:

```text
work_id = 85198816
date_updated = 2026-10-13
```

the output path must be:

```text
corpus/02_ao3_work_pages/2026/85198816.html
```

---

## 9.4 Existing files

If the output HTML file already exists and `--reprocess` is not enabled:

- do not request the work from AO3;
- mark the work as `skipped_existing`;
- log the skip;
- include the work in the manifest.

If `--reprocess` is enabled:

- request the work again;
- overwrite the existing HTML file if capture succeeds.

---

## 9.5 Work-page readiness

For each work, the programme must wait until:

1. the browser reports:

   ```javascript
   document.readyState === "complete"
   ```

2. a `<body>` element is present;
3. AO3 Terms of Service prompt has been handled if present;
4. the work page has the expected work-page structure.

Recommended selectors:

| Purpose                          | Selector             |
|----------------------------------|----------------------|
| Main work page region            | `#main.works-show`   |
| Work skin / work content wrapper | `#workskin`          |
| Chapter container                | `#chapters`          |
| Individual chapter blocks        | `#chapters .chapter` |
| Work title                       | `h2.title.heading`   |
| Author/byline                    | `h3.byline.heading`  |
| Work metadata                    | `dl.work.meta`       |

The minimum required selector for a successful work-page capture should be:

```text
#workskin
```

If the expected selector does not appear before timeout, the work capture attempt fails with status `failed_validation`.

---

## 9.6 Work-page validation

After readiness, the programme should collect minimal validation details from the DOM:

- document title;
- current browser URL;
- work title, if available;
- author/byline text, if available;
- whether `#workskin` exists;
- whether `#chapters` exists;
- number of detected `.chapter` elements under `#chapters`;
- whether `dl.work.meta` exists;
- whether a TOS prompt was handled.

A work page should be considered valid if:

- `#workskin` exists; and
- the page is not an AO3 error/interstitial page; and
- the saved page corresponds to a work page rather than a list page, login page, or unrelated page.

For v1, absence of `#chapters` should be treated as suspicious. Recommended behaviour:

- if `#workskin` exists but `#chapters` does not, mark the capture as `success` only if other work-specific selectors are present;
- record `chapters_detected: false` in validation;
- leave final text-extraction quality control to the later extraction stage.

---

## 9.7 HTML saving

The programme must save `driver.page_source` as UTF-8 encoded HTML.

It should write to a temporary file first and then atomically replace the target file where possible.

Suggested pattern:

```text
85198816.html.tmp
85198816.html
```

This reduces risk of corrupt partial files if the process is interrupted during file writing.

---

## 10. AO3 Terms of Service Consent Handling

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

The manifest should record at work level whether the prompt was handled for that work:

```json
"tos_prompt_handled": true
```

or:

```json
"tos_prompt_handled": false
```

---

## 11. Browser and Selenium Behaviour

## 11.1 One browser session per run

The programme should create one Selenium browser session and reuse it across all planned works.

Benefits:

- lower browser startup overhead;
- faster capture;
- AO3 consent status persists;
- fewer repeated browser initialisations;
- better EC2 performance.

## 11.2 Browser shutdown

The programme must call `driver.quit()` in all cases where a driver has been created, including:

- successful completion;
- work-level failures;
- configuration errors after browser creation;
- keyboard interruption;
- unexpected file-system errors.

## 11.3 Sequential capture

The first implementation must capture works sequentially.

Parallel browser capture is out of scope for v1.

If `--workers` is not `1`, the programme must fail with a configuration error.

## 11.4 Chrome configuration

For Chrome in headless mode, use:

```text
--headless=new
--disable-gpu
--window-size=1920,1080
```

When `--chrome-server-flags` is enabled, also use:

```text
--no-sandbox
--disable-dev-shm-usage
```

## 11.5 Firefox configuration

For Firefox in headless mode, use:

```text
--headless
```

## 11.6 Selenium Manager

The implementation may rely on Selenium Manager to locate or download the necessary browser driver.

If browser setup fails, the programme must exit with a configuration error.

## 11.7 Selenium timeout configuration

The programme must configure Selenium timeouts after creating the WebDriver.

The configured values should be derived from the command-line `--timeout` setting:

- page-load timeout: a multiple of `--timeout`, for example `timeout * 4`;
- script timeout: `timeout`.

This is required because long AO3 or browser stalls may otherwise surface as local Selenium/WebDriver communication timeouts. Those failures should be caught as work-level failures, retried, logged, and recorded in the manifest, rather than crashing the whole run.

---

## 12. Politeness and Rate Limiting

The programme must include rate limiting between work requests.

Default suggestion:

```text
--request-delay 3
--request-jitter 1
```

The delay should be applied after every attempted work capture, whether successful or failed, unless the programme is exiting.

Effective wait time:

```text
request_delay + random value between 0 and request_jitter
```

Example:

```text
3.0 to 4.0 seconds
```

This is intended to reduce unnecessary load on AO3 and make the production run more respectful.

For larger production captures, a more conservative delay may be used.

---

## 13. JSON Manifest Design

## 13.1 Manifest structure

The manifest must use this general structure:

```json
{
  "run_metadata": {
    "run_id": "20261014T143012Z",
    "tool_name": "capture_ao3_works.py",
    "tool_version": "v1",
    "start_time": "2026-10-14T14:30:12Z",
    "end_time": "2026-10-14T14:35:42Z",
    "test_mode": true,
    "test_limit": 5,
    "reprocess": false,
    "workers": 1,
    "collection_plan": "corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson",
    "output_dir": "corpus/02_ao3_work_pages",
    "log_file": "corpus/02_ao3_work_pages/capture_ao3_works.log",
    "manifest_file": "corpus/02_ao3_work_pages/capture_ao3_works_manifest.json",
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
      "start_work_id": null
    },
    "plan_summary": {
      "total_works_in_plan": 6000,
      "selected_works": 6000,
      "years_detected": [2026, 2025, 2024, 2023, 2022, 2021],
      "input_order_preserved": true,
      "duplicate_work_ids_detected": 0
    },
    "summary": {
      "planned_attempts": 5,
      "attempted": 5,
      "succeeded": 5,
      "failed": 0,
      "skipped_existing": 0
    }
  },
  "works": [
    {
      "work_id": "85198816",
      "year": 2026,
      "date_updated": "2026-10-13",
      "url": "https://archiveofourown.org/works/85198816?view_adult=true&view_full_work=true",
      "current_url": "https://archiveofourown.org/works/85198816?view_adult=true&view_full_work=true",
      "output_path": "corpus/02_ao3_work_pages/2026/85198816.html",
      "status": "success",
      "error": null,
      "retries": 0,
      "duration_seconds": 3.281,
      "start_time": "2026-10-14T14:30:15Z",
      "end_time": "2026-10-14T14:30:18Z",
      "source_plan_line": 1,
      "validation": {
        "title": "Boys Don't Cry - sol_starzz - Original Work [Archive of Our Own]",
        "work_title": "Boys Don't Cry",
        "byline": "sol_starzz",
        "workskin_detected": true,
        "chapters_detected": true,
        "chapter_count_detected": 3,
        "work_metadata_detected": true,
        "tos_prompt_handled": true
      },
      "metadata": {
        "plan_title": "Boys Don't Cry",
        "plan_author_name": "sol_starzz"
      }
    }
  ]
}
```

## 13.2 Required work statuses

The following statuses must be supported:

| Status              | Meaning                                                            |
|---------------------|--------------------------------------------------------------------|
| `success`           | Work page was captured and saved successfully                      |
| `failed`            | Work capture was attempted but failed                              |
| `failed_validation` | Page loaded but expected AO3 work content was missing              |
| `skipped_existing`  | Output HTML file already existed and `--reprocess` was not enabled |

## 13.3 Error field

The `error` field must be:

- `null` when there is no error;
- a short string when an error occurs.

Error strings should be concise and useful for diagnosis. The programme should prefer meaningful exception messages and avoid recording unhelpful Selenium or ChromeDriver stack-frame fragments such as:

```text
#17 0x723dd2d3f55c <unknown>
```

If an exception message contains only unhelpful stack-frame lines, the programme should fall back to the exception type name.

Example validation error:

```json
{
  "work_id": "85198816",
  "status": "failed_validation",
  "error": "Expected AO3 work content selector #workskin was not found."
}
```

Example timeout-related error:

```json
{
  "work_id": "85198816",
  "status": "failed",
  "error": "Read timed out. (read timeout=120)"
}
```

## 13.4 Partial manifests

If interrupted, the manifest should include:

```json
"interrupted": true
```

inside `run_metadata`.

Completed, failed, and skipped results collected before interruption must be written.

---

## 14. Logging Specification

The programme must write an append-only log file.

Default:

```text
corpus/02_ao3_work_pages/capture_ao3_works.log
```

### Log format

Each line should follow this format:

```text
[YYYY-MM-DD HH:MM:SS] LEVEL  message
```

Example:

```text
[2026-10-14 14:30:12] INFO  Starting capture_ao3_works.py run_id=20261014T143012Z
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
- start work ID, if provided;
- timeout;
- configured Selenium page-load and script timeout behaviour;
- max retries;
- retry delay;
- request delay and jitter;
- collection plan summary;
- total works in plan;
- years detected in plan;
- URL warnings for missing expected query parameters;
- number of skipped existing works;
- number of planned work captures;
- each skipped existing work;
- each work capture attempt;
- each AO3 TOS prompt handling event;
- each successful capture;
- each failed capture;
- each retry;
- compact and meaningful error summaries;
- manifest write paths;
- end-of-run summary;
- keyboard interrupts;
- validation/configuration errors;
- browser setup failures.

### Example log lines

```text
[2026-10-14 14:30:12] INFO  Starting capture_ao3_works.py run_id=20261014T143012Z
[2026-10-14 14:30:12] INFO  Collection plan: corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
[2026-10-14 14:30:12] INFO  Output directory: corpus/02_ao3_work_pages
[2026-10-14 14:30:12] INFO  Browser: chrome; headless=True
[2026-10-14 14:30:12] INFO  Chrome server flags: True
[2026-10-14 14:30:12] INFO  Test mode: True; test_limit=5
[2026-10-14 14:30:12] INFO  Timeout seconds: 30
[2026-10-14 14:30:13] INFO  Total works in plan: 6000
[2026-10-14 14:30:13] INFO  Years detected: 2026, 2025, 2024, 2023, 2022, 2021
[2026-10-14 14:30:14] INFO  Capturing work_id=85198816 https://archiveofourown.org/works/85198816?view_adult=true&view_full_work=true
[2026-10-14 14:30:18] INFO  AO3 Terms of Service prompt accepted
[2026-10-14 14:30:19] INFO  SUCCESS work_id=85198816 -> corpus/02_ao3_work_pages/2026/85198816.html chapters=3
[2026-10-14 14:35:42] INFO  Wrote latest manifest: corpus/02_ao3_work_pages/capture_ao3_works_manifest.json
[2026-10-14 14:35:42] INFO  Finished run: succeeded=5 failed=0 skipped_existing=0
```

---

## 15. Error Handling and Resiliency

## 15.1 Configuration and input errors

Configuration and input errors must stop the programme before work capture begins.

Examples:

- collection plan missing;
- invalid NDJSON;
- required fields missing;
- duplicate work IDs;
- invalid `date_updated`;
- invalid `full_work_url`;
- output directory cannot be created;
- invalid command-line arguments;
- unsupported browser;
- browser cannot be started;
- start work ID not found.

The programme must exit non-zero.

## 15.2 Per-work errors

Per-work errors must not stop the full run.

Examples:

- page load timeout;
- AO3 transient error;
- browser timeout;
- local Selenium/WebDriver communication timeout;
- expected selector missing;
- TOS prompt cannot be accepted;
- file write error for one work;
- JavaScript execution error during readiness checks;
- unexpected Selenium exception for one work.

For each per-work error:

- retry up to `--max-retries`;
- use `--retry-delay` between attempts;
- if still failing, mark the work as `failed` or `failed_validation`;
- log a compact, meaningful error summary;
- avoid logging only unhelpful Selenium stack-frame fragments;
- continue to the next work.

A local WebDriver read timeout, such as a timeout while Python is waiting for ChromeDriver on `localhost`, must be treated as a retryable per-work failure rather than an uncaught exception that aborts the entire run.

## 15.3 Keyboard interruption

If the user interrupts the programme with `Ctrl+C`, the programme must:

- stop processing;
- quit the browser;
- mark the run as interrupted in the manifest;
- write a partial manifest with completed results so far;
- log the interruption;
- exit non-zero.

## 15.4 Exit codes

The programme must use the following exit-code conventions:

| Exit code | Meaning                                              |
|----------:|------------------------------------------------------|
|       `0` | Completed with no failed attempted captures          |
|       `1` | Completed, but one or more attempted captures failed |
|       `2` | Configuration or validation error                    |
|     `130` | Interrupted by user                                  |

Skipped existing files are not failures.

---

## 16. Docstrings and In-code Documentation

The implementation must include clear docstrings.

## 16.1 Module-level docstring

At the top of `capture_ao3_works.py`, include a module-level docstring explaining:

- purpose of the programme;
- expected NDJSON collection plan file;
- output HTML directory;
- use of Selenium;
- supported browsers;
- AO3 Terms of Service prompt handling;
- default test mode;
- resumability behaviour;
- example commands;
- manifest and logging outputs.

Suggested module docstring:

```python
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
```

## 16.2 Function docstrings

All major functions must include docstrings describing:

- purpose;
- parameters;
- return values;
- whether the function performs I/O;
- error behaviour.

At minimum, docstrings are required for:

- `parse_args`;
- `setup_logging`;
- `validate_args`;
- `normalise_work_id`;
- `derive_year_from_date_updated`;
- `validate_full_work_url`;
- `make_output_path`;
- `load_collection_plan`;
- `make_manifest_metadata`;
- `plan_captures`;
- `create_driver`;
- `accept_ao3_tos_if_present`;
- `wait_for_ao3_work_page`;
- `summarise_error`;
- `capture_one_work`;
- `write_manifests`;
- `main`.

---

## 17. Suggested Constants

The implementation should define constants near the top of the file:

```python
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
```

---

## 18. Development Notes

## 18.1 Initial implementation scope

The first implementation should prioritise:

- correct sequential execution;
- reliable NDJSON plan loading;
- strict input validation;
- duplicate `work_id` detection;
- stable Selenium capture;
- explicit Selenium page-load and script timeout configuration;
- AO3 Terms of Service handling;
- work-specific readiness checks;
- safe resumability;
- append-only logging;
- robust manifest output;
- clear error handling;
- retryable handling of local WebDriver read timeouts;
- meaningful error summaries;
- portability to EC2.

## 18.2 Out of scope for v1

The following are out of scope for the first implementation:

- selecting works for the collection plan;
- modifying the notebook;
- reading directly from the full AO3 works metadata dataset;
- extracting AO3 work text;
- extracting or updating full work metadata;
- exporting text files;
- exporting JSONL or Excel text outputs;
- deduplicating the corpus sample;
- parallel capture;
- browser session rotation;
- advanced Cloudflare/challenge handling;
- authenticated AO3 capture.

## 18.3 Recommended implementation approach

Use Selenium plus Python standard-library modules where possible:

- `argparse`;
- `json`;
- `logging`;
- `pathlib`;
- `datetime`;
- `time`;
- `random`;
- `re`;
- `sys`;
- `urllib.parse`;
- `typing`.

Selenium is required for browser automation.

`urllib3` is also required so the programme can explicitly catch local Selenium/WebDriver read timeouts and handle them as retryable work-level failures.

No Beautiful Soup dependency is required for `capture_ao3_works.py` because the programme only performs minimal DOM validation through Selenium and saves HTML.

Text extraction should be implemented later in a separate offline parser.

---

## 19. Acceptance Criteria

The programme is considered complete when the following conditions are met:

1. Running:

   ```bash
   python capture_ao3_works.py
   ```

   performs a test run of up to 5 planned missing works.

2. The programme reads:

   ```text
   corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
   ```

3. The programme requires each plan record to contain:

   ```text
   work_id
   full_work_url
   date_updated
   ```

4. The programme preserves the NDJSON input order.

5. The programme fails fast if duplicate `work_id` values are present.

6. The programme derives the output year from `date_updated`.

7. The programme creates the output directory if needed:

   ```text
   corpus/02_ao3_work_pages/
   ```

8. The programme creates year subdirectories if needed.

9. Each captured work is saved as:

   ```text
   corpus/02_ao3_work_pages/<year>/<work_id>.html
   ```

10. Existing `.html` files are skipped unless `--reprocess` is used.

11. The programme does not create `.txt` files.

12. The programme does not extract work text.

13. The programme does not update or re-extract metadata.

14. The programme uses `full_work_url` from the plan as the capture URL.

15. The programme warns when `full_work_url` is missing `view_adult=true` or `view_full_work=true`.

16. The programme supports Chrome by default.

17. The programme supports Firefox with:

```bash
--browser firefox
```

18. The programme runs in headless mode by default.

19. The programme can run on EC2 using Chrome headless/server flags.

20. The programme handles AO3’s Terms of Service prompt when present.

21. The programme waits for AO3 work content using a work-page selector such as:

```text
#workskin
```

22. The programme records work-page validation metadata for each captured work.

23. Failed work captures do not stop the full batch.

24. The programme retries failed captures according to `--max-retries`.

25. The programme catches local Selenium/WebDriver read timeouts as work-level failures rather than allowing them to crash the full run.

26. The programme configures Selenium page-load and script timeouts from the command-line timeout setting.

27. The programme records meaningful compact error summaries in logs and manifests.

28. The programme avoids reducing Selenium errors to unhelpful stack-frame fragments such as `#17 ... <unknown>`.

29. The programme supports starting from a specific work ID with:

```bash
--start-work-id 85198816
```

30. If `--start-work-id` is not found in the planned work list, the programme exits with a configuration error.

31. The programme applies a configurable delay between requests.

32. The programme writes an append-only log file at:

```text
corpus/02_ao3_work_pages/capture_ao3_works.log
```

33. The programme writes a latest manifest at:

```text
corpus/02_ao3_work_pages/capture_ao3_works_manifest.json
```

34. A timestamped per-run manifest is also created for each execution.

35. The manifest records:
- run metadata;
- configuration;
- collection plan path;
- output directory;
- total works in plan;
- detected years;
- per-work status;
- work IDs;
- source URLs;
- output paths;
- validation metadata;
- errors;
- timings;
- summary counts.

36. The programme exits with:
- `0` if all attempted captures succeed or are skipped;
- `1` if any attempted capture fails;
- `2` for configuration or validation errors;
- `130` for keyboard interruption.

---

## 20. Short README Section

The following section can be added to project documentation.

### Capture AO3 work pages

The `capture_ao3_works.py` programme captures selected AO3 full-work pages for Phase 1 data collection.

It reads the work collection plan:

```text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```

The collection plan is generated from the AO3 works metadata and contains the selected works to capture. The required fields are:

```text
work_id
full_work_url
date_updated
```

Default test run:

```bash
python capture_ao3_works.py
```

This captures up to 5 planned missing work pages.

Full run:

```bash
python capture_ao3_works.py --no-test-mode
```

To resume from a specific work ID:

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --start-work-id 85198816
```

To resume more conservatively after transient AO3, browser, or WebDriver instability:

```bash
python capture_ao3_works.py \
  --no-test-mode \
  --start-work-id 85198816 \
  --request-delay 6 \
  --request-jitter 4 \
  --max-retries 4 \
  --retry-delay 20 \
  --timeout 45
```

The programme saves rendered HTML files as:

```text
corpus/02_ao3_work_pages/<year>/<work_id>.html
```

Example:

```text
corpus/02_ao3_work_pages/2026/85198816.html
```

The year is derived from the work’s `date_updated` field.

The programme is safe to re-run: existing work pages are skipped by default.

To force re-capture:

```bash
python capture_ao3_works.py --no-test-mode --reprocess
```

The programme writes:

```text
corpus/02_ao3_work_pages/capture_ao3_works.log
corpus/02_ao3_work_pages/capture_ao3_works_manifest.json
```

A timestamped per-run manifest is also created for each execution.

For EC2:

```bash
nohup bash run_python_ec2.sh \
  capture_ao3_works.py \
    --no-test-mode \
    --browser chrome \
    --request-delay 3 \
    --request-jitter 1 \
> process_output.log 2>&1 &
```

This programme only captures work-page HTML. Work text extraction is handled later by a separate offline processing step.