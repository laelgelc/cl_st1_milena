## Me
Please have a look at this log file. Why are successes occasional?

## AI Assistant
The “successes” are only occasional because this particular run is **mostly not trying to fetch pages** — it is **skipping pages that already exist**, and only the **gaps** in the existing files are being attempted.

From the log:

- `Reprocess: False`
- Then thousands of lines like:

```plain text
SKIPPED_EXISTING 2026_0001 -> corpus/01_ao3_list_pages/2026/2026_0001.html
SKIPPED_EXISTING 2026_0002 -> corpus/01_ao3_list_pages/2026/2026_0002.html
...
```


That means the script sees an existing output HTML file and does **not** re-download it.

The key clue is that the skipped page sequence has holes. For example:

```plain text
SKIPPED_EXISTING 2026_3623 -> ...
SKIPPED_EXISTING 2026_3625 -> ...
```


`2026_3624` is missing from the skipped sequence, so that page probably **does not already exist** and would be captured. If it succeeds, you’ll see a `SUCCESS` line there.

Likewise:

```plain text
SKIPPED_EXISTING 2026_3638 -> ...
SKIPPED_EXISTING 2026_3640 -> ...
```


`2026_3639` is missing, so that is another likely attempted page.

So the pattern is probably:

1. The run resumes over the whole plan.
2. Existing files are skipped very quickly.
3. Only missing pages are fetched.
4. Therefore `SUCCESS` appears only occasionally, exactly where a page file was missing.

In other words, occasional successes are not necessarily AO3 behaving randomly; they are probably the script **backfilling missing pages** among an otherwise already-downloaded dataset.

A second thing to notice: all the `SKIPPED_EXISTING` lines have the exact same timestamp:

```plain text
[2026-10-15 17:55:34]
```


That confirms these are local filesystem checks, not network requests. The script is racing through existing files almost instantly.

If you want to confirm this, check whether these files are absent:

```plain text
corpus/01_ao3_list_pages/2026/2026_3624.html
corpus/01_ao3_list_pages/2026/2026_3639.html
```


If those are missing, then the occasional successes are simply the script filling gaps.

If your intention is to re-download everything, run with `--reprocess`. If your intention is to resume safely, the current behavior is correct.

## Me
What is the probable cause for the frequent timeout failures?

## AI Assistant
The probable cause is **AO3 intermittently delaying, throttling, or failing to fully serve pages to an automated/headless browser**, rather than a problem with individual page numbers.

The log/config points to a few things:

- You are making a very large crawl: **15,056 planned list pages**.
- The run uses only **1 worker**, with a **3s delay + 1s jitter**, so it is not highly parallel, but it is still a sustained automated sequence.
- Timeout is **30 seconds**.
- The project notes already show AO3 behaving unreliably for programmatic access, including **525 errors** and **read timeouts**.
- The successes are occasional because only missing pages are being retried; the failures likely occur when those missing pages are actually fetched and AO3 does not return usable content within the timeout.

So the most likely explanation is:

> **AO3/Cloudflare is sometimes slow or protective toward repeated automated requests, causing Selenium to wait for a page condition that never arrives before the 30-second timeout.**

This can happen even if the URL is valid. AO3 pages may intermittently return:

- a slow-loading response;
- a Cloudflare/protection/interstitial page;
- an AO3 error/maintenance page;
- a partially loaded page without the expected list content;
- a browser page that reaches `document.readyState == complete` but does not contain the expected AO3 results;
- or a response that simply takes longer than 30 seconds.

A secondary possibility is that the wait condition is stricter than “page loaded”. If the capture tool waits for AO3-specific list content, then pages that load into a **Terms**, **rate-limit**, **error**, or **challenge** page may still time out because the expected work-list elements never appear.

The strongest evidence is that the failures are frequent during a long AO3 scrape, while earlier documentation already recorded direct HTTP timeouts and server-side errors. That suggests the bottleneck is **AO3’s availability/protection/rate-limiting behavior under sustained access**, not bad page IDs.

Practical mitigations:

- Increase timeout, e.g. **60–90s**.
- Increase request delay, e.g. **8–15s plus jitter**.
- Add longer backoff after timeout failures.
- Save timeout page HTML/screenshots for diagnosis.
- Detect AO3 error/challenge/terms pages separately, instead of classifying everything as a generic timeout.
- Retry failed pages later in a separate pass.

In short: **frequent timeout failures are probably caused by sustained automated access triggering intermittent slow responses or protective behavior from AO3/Cloudflare, combined with a 30-second timeout that is too short for those cases.**

## Me
Is it possible to add a diagnosis mode?

## AI Assistant
Yes. A **diagnosis mode** would be very useful here.

The goal would be: when a page fails or times out, save enough evidence to tell *what actually loaded*:

- final browser URL;
- page title;
- main heading if any;
- body text preview;
- HTML snapshot of the failed page;
- screenshot;
- whether AO3 work-list container existed;
- whether TOS prompt existed;
- whether the page looked like Cloudflare / rate limit / error / maintenance / empty result;
- exception type and message.

That would turn a generic timeout like:

```plain text
FAILED 2025_0255 status=failed_validation error='TimeoutException'
```


into something diagnosable, e.g.:

```plain text
diagnosis_category=ao3_error_page
title="Archive of Our Own"
heading="Retry later"
body_preview="The Archive is down for maintenance..."
screenshot="corpus/01_ao3_list_pages/diagnostics/...png"
html="corpus/01_ao3_list_pages/diagnostics/...html"
```


Below is a minimal way to add it to `capture_ao3_lists.py`.

```python
# ... existing code ...

DEFAULT_REQUEST_DELAY_SECONDS = 3.0
DEFAULT_REQUEST_JITTER_SECONDS = 1.0

DEFAULT_DIAGNOSIS_MODE = False

AO3_LIST_READY_SELECTOR = "ol.work.index.group li.work"
AO3_LIST_CONTAINER_SELECTOR = "ol.work.index.group"
AO3_MAIN_HEADING_SELECTOR = "#main h2.heading"

# ... existing code ...
```


```python
# ... existing code ...

    parser.add_argument(
        "--request-jitter",
        type=float,
        default=DEFAULT_REQUEST_JITTER_SECONDS,
        help=f"Maximum random extra delay between requests. Default: {DEFAULT_REQUEST_JITTER_SECONDS}",
    )
    parser.add_argument(
        "--diagnosis-mode",
        action="store_true",
        default=DEFAULT_DIAGNOSIS_MODE,
        help=(
            "Save diagnostic HTML, screenshots, and page summaries when a capture "
            "attempt fails. Useful for investigating timeouts and AO3/Cloudflare pages."
        ),
    )
    parser.add_argument(
        "--diagnostics-dir",
        type=Path,
        default=None,
        help=(
            "Directory for diagnosis artifacts. Default: "
            "<output-dir>/diagnostics/<run-id>/"
        ),
    )

    return parser.parse_args()

# ... existing code ...
```


```python
# ... existing code ...

        logger.info("Request delay seconds: %s", args.request_delay)
        logger.info("Request jitter seconds: %s", args.request_jitter)
        logger.info("Start page ID: %s", args.start_page_id)
        logger.info("Diagnosis mode: %s", args.diagnosis_mode)
        logger.info("Diagnostics directory: %s", args.diagnostics_dir)
        logger.info("Loaded plan years: %s", ", ".join(str(year) for year in years))
        logger.info("Range order: %s", collection_plan.get("range_order"))
        logger.info("Page order within year: %s", collection_plan.get("page_order_within_year"))

# ... existing code ...
```


Add these helper functions near the existing error/HTML helper functions, for example after `write_html_atomic`.

```python
# ... existing code ...

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


def get_page_diagnosis_category(
        title: str | None,
        heading: str | None,
        body_preview: str | None,
        has_list_container: bool,
        has_work_items: bool,
        has_tos_prompt: bool,
) -> str:
    """Classify the loaded page state for diagnostic reporting."""
    combined_text = " ".join(
        text for text in [title, heading, body_preview] if text
    ).lower()

    if has_work_items:
        return "ao3_list_ready"
    if has_list_container and not has_work_items:
        return "ao3_list_container_without_items"
    if has_tos_prompt:
        return "ao3_tos_prompt"
    if "cloudflare" in combined_text or "checking if the site connection is secure" in combined_text:
        return "cloudflare_or_browser_challenge"
    if "retry later" in combined_text or "temporarily unavailable" in combined_text:
        return "ao3_temporary_error"
    if "maintenance" in combined_text:
        return "ao3_maintenance"
    if "rate limit" in combined_text or "too many requests" in combined_text:
        return "rate_limited"
    if "archive of our own" in combined_text:
        return "ao3_unexpected_page"

    return "unknown_page_state"


def collect_page_diagnostics(
        driver: WebDriver,
        page_item: dict[str, Any],
        diagnostics_dir: Path,
        attempt_number: int,
        error: BaseException | str | None,
        logger: logging.Logger,
) -> dict[str, Any]:
    """Save diagnostic artifacts for a failed page capture attempt.

    Args:
        driver: Selenium WebDriver.
        page_item: Page metadata.
        diagnostics_dir: Base diagnostics output directory.
        attempt_number: Capture attempt number.
        error: Error that triggered diagnostics.
        logger: Logger for diagnostic warnings.

    Returns:
        Manifest-ready diagnostic metadata.
    """
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    artifact_stem = f"{page_item['page_id']}_attempt_{attempt_number}"
    html_path = diagnostics_dir / f"{artifact_stem}.html"
    screenshot_path = diagnostics_dir / f"{artifact_stem}.png"
    json_path = diagnostics_dir / f"{artifact_stem}.json"

    current_url = None
    title = None
    heading = None
    body_preview = None
    html_saved = False
    screenshot_saved = False
    has_list_container = False
    has_work_items = False
    has_tos_prompt = False

    try:
        current_url = driver.current_url
    except (WebDriverException, ReadTimeoutError):
        current_url = None

    try:
        title = driver.title or None
    except (WebDriverException, ReadTimeoutError):
        title = None

    try:
        heading = get_optional_text(driver, AO3_MAIN_HEADING_SELECTOR)
    except (WebDriverException, ReadTimeoutError):
        heading = None

    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text.strip()
        body_preview = body_text[:2000] if body_text else None
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException, ReadTimeoutError):
        body_preview = None

    try:
        has_list_container = bool(driver.find_elements(By.CSS_SELECTOR, AO3_LIST_CONTAINER_SELECTOR))
        has_work_items = bool(driver.find_elements(By.CSS_SELECTOR, AO3_LIST_READY_SELECTOR))
        has_tos_prompt = element_is_displayed(driver, AO3_TOS_PROMPT_SELECTOR)
    except (WebDriverException, ReadTimeoutError):
        has_list_container = False
        has_work_items = False
        has_tos_prompt = False

    try:
        html = driver.page_source
        write_html_atomic(html_path, html)
        html_saved = True
    except (OSError, WebDriverException, ReadTimeoutError) as exc:
        logger.warning("Could not save diagnostic HTML for %s: %s", page_item["page_id"], summarise_error(exc))

    try:
        driver.save_screenshot(str(screenshot_path))
        screenshot_saved = True
    except (WebDriverException, ReadTimeoutError) as exc:
        logger.warning("Could not save diagnostic screenshot for %s: %s", page_item["page_id"], summarise_error(exc))

    diagnosis_category = get_page_diagnosis_category(
        title=title,
        heading=heading,
        body_preview=body_preview,
        has_list_container=has_list_container,
        has_work_items=has_work_items,
        has_tos_prompt=has_tos_prompt,
    )

    diagnosis = {
        "diagnosis_category": diagnosis_category,
        "attempt_number": attempt_number,
        "page_id": page_item["page_id"],
        "source_url": page_item["url"],
        "current_url": current_url,
        "title": title,
        "heading": heading,
        "body_preview": body_preview,
        "has_list_container": has_list_container,
        "has_work_items": has_work_items,
        "has_tos_prompt": has_tos_prompt,
        "error_type": type(error).__name__ if error is not None else None,
        "error": summarise_error(error),
        "html_path": str(html_path) if html_saved else None,
        "screenshot_path": str(screenshot_path) if screenshot_saved else None,
        "json_path": str(json_path),
    }

    try:
        with json_path.open("w", encoding="utf-8") as output_file:
            json.dump(diagnosis, output_file, ensure_ascii=False, indent=2)
    except OSError as exc:
        logger.warning("Could not save diagnostic JSON for %s: %s", page_item["page_id"], summarise_error(exc))

    return diagnosis


def add_diagnosis_to_validation(
        validation: dict[str, Any] | None,
        diagnosis: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Attach diagnostic metadata to validation metadata."""
    if diagnosis is None:
        return validation

    merged_validation = validation.copy() if validation is not None else {
        "title": None,
        "heading": None,
        "work_items_detected": None,
        "tos_prompt_handled": False,
    }
    merged_validation["diagnosis"] = diagnosis
    return merged_validation


def make_failed_result(
        page_item: dict[str, Any],
        status: str,
        error: BaseException | str,

# ... existing code ...
```


Then extend `capture_one_page()` so it can receive diagnosis settings and save artifacts on each failed attempt.

```python
# ... existing code ...

def capture_one_page(
        driver: WebDriver,
        page_item: dict[str, Any],
        timeout: int,
        max_retries: int,
        retry_delay: float,
        logger: logging.Logger,
        diagnosis_mode: bool = False,
        diagnostics_dir: Path | None = None,
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
        diagnosis_mode: Whether to save diagnostic artifacts for failed attempts.
        diagnostics_dir: Directory where diagnostic artifacts should be written.

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
    last_diagnosis: dict[str, Any] | None = None

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

        if diagnosis_mode and diagnostics_dir is not None:
            last_diagnosis = collect_page_diagnostics(
                driver=driver,
                page_item=page_item,
                diagnostics_dir=diagnostics_dir,
                attempt_number=attempt_number,
                error=last_error,
                logger=logger,
            )
            last_validation = add_diagnosis_to_validation(last_validation, last_diagnosis)
            logger.warning(
                "DIAGNOSIS %s attempt=%s category=%s title=%r current_url=%r",
                page_item["page_id"],
                attempt_number,
                last_diagnosis.get("diagnosis_category"),
                last_diagnosis.get("title"),
                last_diagnosis.get("current_url"),
            )

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

# ... existing code ...
```


Finally, pass those settings from `main()`.

```python
# ... existing code ...

            for item in planned:
                logger.info("Capturing %s %s", item["page_id"], item["url"])

                diagnostics_dir = None
                if args.diagnosis_mode:
                    diagnostics_dir = args.diagnostics_dir
                    if diagnostics_dir is None:
                        diagnostics_dir = args.output_dir / "diagnostics" / run_id

                result = capture_one_page(
                    driver=driver,
                    page_item=item,
                    timeout=args.timeout,
                    max_retries=args.max_retries,
                    retry_delay=args.retry_delay,
                    logger=logger,
                    diagnosis_mode=args.diagnosis_mode,
                    diagnostics_dir=diagnostics_dir,
                )
                results.append(result)

                if result["status"] == "success":

# ... existing code ...
```


You could then run a small diagnostic pass like this:

```textmate
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2025_0255 \
  --test-limit 5 \
  --timeout 60 \
  --max-retries 1 \
  --diagnosis-mode
```


Or, for a single problematic page with reprocessing:

```textmate
python capture_ao3_lists.py \
  --start-page-id 2026_3624 \
  --test-limit 1 \
  --reprocess \
  --timeout 60 \
  --diagnosis-mode
```


The resulting artifacts would be under something like:

```plain text
corpus/01_ao3_list_pages/diagnostics/20261017T123456Z/
```


This should make it much clearer whether the failures are caused by **AO3 slowness**, **Cloudflare/challenge pages**, **TOS prompts**, **maintenance pages**, **empty AO3 pages**, or a selector/wait-condition mismatch.

## Me
Can I have the entire revised programme?

> omitted

## Me
Please have a look at the attached documents.

## AI Assistant
Yes — the diagnostic output is very clear now.

## Main finding

The failures are **not mysterious Selenium timeouts** and not bad page URLs.

The failed list-page attempts are receiving a real AO3 error page:

```plain text
Page Responding Too Slowly | Archive of Our Own
Error 503
The page was responding too slowly.
```


So the probable cause is:

> **AO3 is returning HTTP-style 503 “page responding too slowly” pages for those deep search-result/list pages.**

Your script then waits for normal AO3 list-page content:

```plain text
ol.work.index.group li.work
```


…but the loaded page is an AO3 error page, not a results page. Therefore no list container or work items appear:

```json
"has_list_container": false,
"has_work_items": false,
"has_tos_prompt": false
```


That leads to the `TimeoutException`.

So the timeout is a **secondary symptom**. The actual cause is AO3 serving an **Error 503 slow-response page**.

## Important detail

Both examples show the same pattern:

- `current_url` is still the intended AO3 list URL.
- `title` is `"Page Responding Too Slowly | Archive of Our Own"`.
- `heading` is `"Error 503"`.
- body says: `"The page was responding too slowly."`
- no list results are present.

That means AO3 accepted the URL but failed to generate the search result page quickly enough.

## Why these particular pages?

The pages are very deep in the 2026 result range:

```plain text
page=3625
page=3626
```


For AO3 search/list pages, deep pagination plus filters can be expensive server-side. Even if earlier pages load, later pages may be harder/slower for AO3 to compute. So this is likely not caused by your local browser; AO3 itself is timing out internally while generating the result page.

## The diagnosis category should be improved

The current diagnosis says:

```json
"diagnosis_category": "ao3_unexpected_page"
```


But based on the HTML, this should really be classified as something like:

```plain text
ao3_503_slow_response
```


or at least:

```plain text
ao3_temporary_error
```


The classifier missed it because it looked for phrases like `"retry later"` and `"temporarily unavailable"`, but AO3’s actual phrase here is:

```plain text
The page was responding too slowly.
```


So I would add checks for:

- `"error 503"`
- `"page responding too slowly"`
- `"responding too slowly"`

## Practical implication

For these failures, simply increasing Selenium’s wait may not help much, because the browser has already received the final AO3 error page. It is not waiting for a slow page to finish; it has loaded an error response.

Better mitigations are:

1. **Slow down between requests** substantially.
2. **Use long backoff after 503 pages**, e.g. 5–15 minutes.
3. **Retry failed pages in a later run**, not immediately.
4. **Classify 503 pages explicitly** so they are not treated as generic validation timeouts.
5. Consider reducing pressure on very deep pages, especially around high-volume recent-year ranges.

## Suggested operational change

For this kind of error, I would use a different retry strategy:

- normal validation failure: retry after 10–30 seconds;
- AO3 503 slow-response page: retry after several minutes;
- repeated 503 on same page: stop retrying during this run and record it for a later backfill pass.

For example:

```plain text
attempt 1 -> 503 slow response
wait 5 min
attempt 2 -> 503 slow response
wait 15 min
attempt 3 -> 503 slow response
mark as ao3_503_slow_response and retry tomorrow/later
```


## Bottom line

The diagnostic mode did its job: the frequent failures are caused by **AO3 serving “Error 503 — The page was responding too slowly”** for deep filtered list pages. The script reports a timeout because it is waiting for work-list elements that never appear on that error page.

## Me
Please have a look at the logs. Anything interesting?

## AI Assistant
Yes — several interesting things stand out.

## 1. `--test-limit 1` did **not** limit the run

The command was:

```textmate
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2026_3624 \
  --test-limit 1 \
  --reprocess \
  --timeout 60 \
  --diagnosis-mode
```


But the log says:

```plain text
Test mode: False; test_limit=1
Planned capture attempts: 11433
```


Because `--no-test-mode` disables test mode, `--test-limit 1` is ignored. So instead of planning one page, the run planned every page from `2026_3624` through the end of the full plan: **11,433 pages**.

That is why it continued after `2026_3624`.

If you want only one page, use either:

```textmate
python capture_ao3_lists.py \
  --start-page-id 2026_3624 \
  --test-limit 1 \
  --reprocess \
  --timeout 60 \
  --diagnosis-mode
```


or add a new `--stop-page-id` / `--limit-pages` option later.

## 2. `2026_3624` succeeded, and accepted the AO3 TOS prompt

This line is important:

```plain text
SUCCESS 2026_3624 -> ... work_items=20
AO3 Terms of Service prompt accepted
```


So the session started cleanly, handled the TOS prompt, and captured a valid page with 20 work items.

That confirms the browser, cookies/local storage, selectors, and URL format are all basically working.

## 3. `2026_3625` looks persistently bad

`2026_3625` failed three times in a row:

```plain text
2026_3625 attempt=1 -> Page Responding Too Slowly
2026_3625 attempt=2 -> Page Responding Too Slowly
2026_3625 attempt=3 -> Page Responding Too Slowly
FAILED 2026_3625
```


The diagnostic JSON/HTML confirms AO3 returned:

```plain text
Error 503
The page was responding too slowly.
```


This is not Selenium “being confused”; AO3 is serving an error page instead of the list page.

Since all three attempts failed for the same page, `2026_3625` may be an especially expensive/deep result page for AO3 to generate.

## 4. But the problem is partly transient: `2026_3626` eventually succeeded

`2026_3626` first got the same slow-response page:

```plain text
2026_3626 attempt=1 -> Page Responding Too Slowly
2026_3626 attempt=2 -> Page Responding Too Slowly
```


Then:

```plain text
SUCCESS 2026_3626 -> ... work_items=20
```


So these errors are not necessarily permanent. AO3 may fail to generate a page once or twice, then succeed later.

That suggests retrying later is valuable — but immediate retries with only a 10-second delay are probably too aggressive for 503 cases.

## 5. There was also a Cloudflare / SSL failure, but it recovered

For `2026_3627`:

```plain text
category=cloudflare_or_browser_challenge
title='archiveofourown.org | 525: SSL handshake failed'
```


Then the retry succeeded:

```plain text
SUCCESS 2026_3627 -> ... work_items=20
```


So you are seeing at least two distinct failure modes:

1. **AO3 application error:** `Error 503`, “page responding too slowly”.
2. **Cloudflare/edge error:** `525: SSL handshake failed`.

Both can be transient.

## 6. The diagnostic classifier should be refined

The current category for AO3 503 pages is:

```plain text
ao3_unexpected_page
```


But the evidence is specific enough to classify it as:

```plain text
ao3_503_slow_response
```


That would make log summaries much clearer.

## 7. Some “successful” pages are still slow

For example:

```plain text
Capturing 2026_3629 at 09:13:11
SUCCESS at 09:15:01
```


That success took about **110 seconds**.

So even when AO3 eventually returns a valid page, deep pages can be very slow. This reinforces that the main issue is AO3 server-side generation time, not just browser waiting.

## 8. The timeout behavior is longer than `--timeout 60`

Some failed attempts took around 100+ seconds. That is because the browser page-load timeout appears to be longer than the content-readiness timeout. So `--timeout 60` does not necessarily mean each failed attempt ends after exactly 60 seconds.

Operationally, that means three retries can take several minutes per bad page.

## Bottom line

The logs show:

- The diagnostic mode is working.
- The URL/query is valid.
- TOS handling works.
- AO3 deep result pages around `2026_3625+` are unstable/slow.
- `2026_3625` is a persistent AO3 503 case in this run.
- `2026_3626` and `2026_3627` demonstrate that retries can recover transient AO3/Cloudflare failures.
- The command unintentionally planned **11,433 pages** because `--no-test-mode` made `--test-limit 1` irrelevant.

I’d recommend adding:

1. an explicit `ao3_503_slow_response` diagnosis category;
2. longer backoff for that category;
3. a true `--limit-pages` option that works independently of test mode.

## Me
I tried the failed links manually on the browser and the pages load very quickly. This is puzzling because it seems that AO3 is not struggling internally... Do you think this behaviour is a subtle defence against automated scraping?

## AI Assistant
Yes — **it could very plausibly be an automated-access defence or throttling behaviour**, but I would phrase it carefully:

> The evidence is consistent with AO3/Cloudflare treating the Selenium session differently from your ordinary browser session. It is not proof of an intentional anti-scraping block, but it strongly suggests that request context matters: browser fingerprint, session state, cookies, request cadence, and/or accumulated access pattern.

A few reasons this is plausible:

## What looks suspicious

### 1. Manual browser loads quickly, Selenium gets 503

The exact same URL loading quickly in your normal browser, while Selenium receives:

```plain text
Page Responding Too Slowly | Archive of Our Own
Error 503
The page was responding too slowly.
```


suggests this is **not simply that page 3625 is inherently impossible for AO3 to generate**.

If it were purely an internal AO3 query-cost issue, you would expect manual access to be slow or intermittently fail too.

### 2. The failures occur in an automated sequence

The Selenium run is not a one-off human visit. It is a sequence of repeated page requests, even with delays. That gives AO3/Cloudflare a behavioural signal:

- same browser session;
- repeated similar URLs;
- predictable pagination;
- short regular intervals;
- headless Chrome;
- many prior requests in the broader collection history.

That pattern is easy to distinguish from ordinary browsing.

### 3. You also saw a Cloudflare-style failure

The log included:

```plain text
archiveofourown.org | 525: SSL handshake failed
```


That points to infrastructure/proxy-layer instability or intervention, not only AO3 application slowness.

### 4. The error page may be a polite throttle

AO3 may not show a blunt “you are rate limited” message. It may instead surface a generic 503 / slow-response page when a request is deprioritized, times out upstream, or hits protective infrastructure.

So yes, it could be a **subtle defensive degradation** rather than a hard block.

## But there are non-defensive explanations too

I would not conclude “definitely anti-scraping” because there are other differences between your manual browser and Selenium:

### Normal browser has a richer trusted session

Your manual browser likely has:

- long-lived cookies;
- normal browsing history;
- non-headless fingerprint;
- extensions/fonts/GPU/window metrics;
- a human interaction trail;
- established AO3/Cloudflare trust.

The Selenium browser may be a fresh, headless, short-lived session.

### Manual test is isolated

When you try one URL manually, it is a single request. The script is part of a sequence. AO3 may behave differently after several consecutive filtered result requests.

### Timing variance

`2026_3626` failed twice and then succeeded. That means some failures are transient. If you happened to test manually during a good interval, it would look normal.

## One very important extra observation

Your plan may already be stale. The attached successful list-page example for 2025 says:

```plain text
81 - 100 of 70,947 Works
```


But the collection plan says 2025 expected works:

```json
"expected_works": 62614
```


So AO3’s live result counts have shifted since the plan was made. That does not explain the 503s directly, but it means the query ranges are volatile and the tail pages may not correspond exactly to the original assumptions anymore.

## My interpretation

The most likely picture is:

1. AO3 list/search pages are expensive, especially filtered/deep pagination.
2. Your Selenium run produces a repeated, machine-like access pattern.
3. AO3/Cloudflare sometimes gives that session a low-trust or throttled path.
4. Instead of returning an explicit “bot detected” page, it returns generic 503 / slow-response pages.
5. A normal manual browser session, with better trust signals and isolated access, loads the same URL quickly.

So yes: **this looks compatible with subtle anti-automation throttling or bot mitigation**, even if it is not a formal hard block.

## What I would do next

Ethically and practically, I would avoid trying to “defeat” the protection. Instead:

- Treat 503/525 as a signal to **pause longer**.
- Use much longer delays, e.g. **30–120 seconds**, not 3–4 seconds.
- Use exponential backoff for 503s, e.g. **5 min → 15 min → retry in next run**.
- Capture in smaller batches.
- Avoid deep continuous pagination runs.
- Keep diagnosis artifacts.
- Consider documenting this as a limitation of AO3 collection.
- If this is for formal research, consider checking AO3/OTW guidance or contacting them if large-scale collection is essential.

A useful next experiment would be to run **one Selenium request only**, after a long idle period, for the failed page. If that succeeds quickly, but it fails after a sequence of requests, that would strongly support the “behavioural throttling” hypothesis.
