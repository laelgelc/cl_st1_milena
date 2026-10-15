# `capture_ao3_lists.py` troubleshooting

## `capture_ao3_lists.py` error

```shell
[2026-10-15 10:29:51] INFO  Capturing 2025_3048 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3048                                                             
[2026-10-15 10:31:20] INFO  SUCCESS 2025_3048 -> corpus/01_ao3_list_pages/2025/2025_3048.html work_items=20                                                                            
[2026-10-15 10:31:24] INFO  Capturing 2025_3049 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3049                                                             
[2026-10-15 10:31:56] INFO  SUCCESS 2025_3049 -> corpus/01_ao3_list_pages/2025/2025_3049.html work_items=20                                                                            
[2026-10-15 10:32:00] INFO  Capturing 2025_3050 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3050                                                             
[2026-10-15 10:32:31] WARNING Retrying 2025_3050 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>                                                                                
[2026-10-15 10:33:11] WARNING Retrying 2025_3050 after failed attempt 2/3: #17 0x723dd2d3f55c <unknown>                                                                                
[2026-10-15 10:34:22] ERROR FAILED 2025_3050 status=failed_validation error='#17 0x723dd2d3f55c <unknown>'                                                                             
[2026-10-15 10:34:25] INFO  Capturing 2025_3051 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3051                                                             
[2026-10-15 10:35:33] WARNING Retrying 2025_3051 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>                                                                                
[2026-10-15 10:36:07] INFO  SUCCESS 2025_3051 -> corpus/01_ao3_list_pages/2025/2025_3051.html work_items=20                                                                            
[2026-10-15 10:36:10] INFO  Capturing 2025_3052 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3052                                                             
[2026-10-15 10:38:07] WARNING Retrying 2025_3052 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:38:47] WARNING Retrying 2025_3052 after failed attempt 2/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:39:28] ERROR FAILED 2025_3052 status=failed_validation error='#17 0x723dd2d3f55c <unknown>'
[2026-10-15 10:39:31] INFO  Capturing 2025_3053 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3053
[2026-10-15 10:40:02] WARNING Retrying 2025_3053 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:40:42] WARNING Retrying 2025_3053 after failed attempt 2/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:41:23] ERROR FAILED 2025_3053 status=failed_validation error='#17 0x723dd2d3f55c <unknown>'
[2026-10-15 10:41:26] INFO  Capturing 2025_3054 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3054
[2026-10-15 10:42:36] WARNING Retrying 2025_3054 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:43:17] WARNING Retrying 2025_3054 after failed attempt 2/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:44:33] ERROR FAILED 2025_3054 status=failed_validation error='#17 0x723dd2d3f55c <unknown>'
[2026-10-15 10:44:36] INFO  Capturing 2025_3055 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3055
[2026-10-15 10:45:07] WARNING Retrying 2025_3055 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:46:36] WARNING Retrying 2025_3055 after failed attempt 2/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:47:16] ERROR FAILED 2025_3055 status=failed_validation error='#17 0x723dd2d3f55c <unknown>'
[2026-10-15 10:47:20] INFO  Capturing 2025_3056 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3056
[2026-10-15 10:47:50] WARNING Retrying 2025_3056 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:49:15] WARNING Retrying 2025_3056 after failed attempt 2/3: #17 0x723dd2d3f55c <unknown>
[2026-10-15 10:49:56] ERROR FAILED 2025_3056 status=failed_validation error='#17 0x723dd2d3f55c <unknown>'
[2026-10-15 10:49:59] INFO  Capturing 2025_3057 https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_
names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=2025-01-01&work_search%5Bdate_to%5
D=2025-12-31&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work&page=3057
[2026-10-15 10:50:30] WARNING Retrying 2025_3057 after failed attempt 1/3: #17 0x723dd2d3f55c <unknown>
Traceback (most recent call last):
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/connectionpool.py", line 540, in _make_request
    response = conn.getresponse()
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/connection.py", line 638, in getresponse
    httplib_response = super().getresponse()
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/http/client.py", line 1478, in getresponse
    response.begin()
    ~~~~~~~~~~~~~~^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/http/client.py", line 343, in begin
    version, status, reason = self._read_status()
                              ~~~~~~~~~~~~~~~~~^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/http/client.py", line 304, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/socket.py", line 723, in readinto
    return self._sock.recv_into(b)
           ~~~~~~~~~~~~~~~~~~~~^^^
TimeoutError: timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/ubuntu/cl_st1_milena/cl_st1_ph1_milena/capture_ao3_lists.py", line 1317, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/ubuntu/cl_st1_milena/cl_st1_ph1_milena/capture_ao3_lists.py", line 1188, in main
    result = capture_one_page(
        driver=driver,
    ...<4 lines>...
        logger=logger,
    )                                                                                                                                                                                  
  File "/home/ubuntu/cl_st1_milena/cl_st1_ph1_milena/capture_ao3_lists.py", line 880, in capture_one_page                                                                              
    driver.get(page_item["url"])
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/selenium/webdriver/remote/webdriver.py", line 524, in get
    self.execute(Command.GET, {"url": url})
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/selenium/webdriver/remote/webdriver.py", line 501, in execute
    response = cast(RemoteConnection, self.command_executor).execute(driver_command, params)
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/selenium/webdriver/remote/remote_connection.py", line 407, in execute
    return self._request(command_info[0], url, body=data)
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/selenium/webdriver/remote/remote_connection.py", line 431, in _request
    response = self._conn.request(method, url, body=body, headers=headers, timeout=self._client_config.timeout)
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/_request_methods.py", line 143, in request
    return self.request_encode_body(
           ~~~~~~~~~~~~~~~~~~~~~~~~^
        method, url, fields=fields, headers=headers, **urlopen_kw
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/_request_methods.py", line 278, in request_encode_body
    return self.urlopen(method, url, **extra_kw)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/poolmanager.py", line 459, in urlopen
    response = conn.urlopen(method, u.request_uri, **kw)
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/connectionpool.py", line 847, in urlopen
    retries = retries.increment(
        method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
    )
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/util/retry.py", line 510, in increment
    raise reraise(type(error), error, _stacktrace)
          ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/util/util.py", line 39, in reraise
    raise value
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/connectionpool.py", line 793, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/connectionpool.py", line 542, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/miniconda3/envs/my_env/lib/python3.13/site-packages/urllib3/connectionpool.py", line 373, in _raise_timeout
    raise ReadTimeoutError(
        self, url, f"Read timed out. (read timeout={timeout_value})"
    ) from err
urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(host='localhost', port=50889): Read timed out. (read timeout=120)
ubuntu@ip-172-31-4-218:~/cl_st1_milena/cl_st1_ph1_milena$ 
```

## Me
Please help me troubleshoot `capture_ao3_lists.py`. The error messages are in the attached Markdown document.

## AI Assistant
## Diagnosis

There are **two related problems** in the log:

1. **Many page validations start failing intermittently** around `2025_3050`.
   - The repeated `#17 0x723dd2d3f55c <unknown>` messages are likely Selenium/ChromeDriver stack-trace fragments being reduced poorly by `summarise_error()`.
   - The actual failure is probably a page-load or readiness timeout, but your logger is only preserving the last unhelpful stack-frame line.

2. The run finally **crashes instead of returning a failed page result** because this exception is **not caught** by `capture_one_page()`:

```plain text
urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(host='localhost', port=50889): Read timed out. (read timeout=120)
```


That timeout is not AO3 directly. It is Python/Selenium waiting for a response from the **local ChromeDriver HTTP server** on `localhost`. In practice, this often means Chrome/ChromeDriver got stuck during `driver.get(...)`, probably because AO3/Cloudflare/page loading stalled.

Your `capture_one_page()` catches:

```python
TimeoutException
(WebDriverException, OSError, JavascriptException)
```


…but `urllib3.exceptions.ReadTimeoutError` is **not one of those**, so it escapes the retry loop and aborts the whole script.

---

## Most important fix

Catch `urllib3.exceptions.ReadTimeoutError` inside `capture_one_page()` and treat it as a retryable page failure.

Add this import:

```python
from urllib.parse import urlencode

from urllib3.exceptions import ReadTimeoutError

from selenium import webdriver
from selenium.common.exceptions import (
    JavascriptException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
```


Then update the retryable exception handler:

```python
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
```


This alone should prevent the full run from crashing when ChromeDriver stops responding for a single page.

---

## Strongly recommended: set Selenium page-load timeout

Right now `driver.get(...)` can hang until Selenium’s internal command timeout, which is what you see as `read timeout=120`.

Add this in `create_driver()` after creating the driver, instead of returning immediately.

```python
def create_driver(browser: str, headless: bool, chrome_server_flags: bool) -> WebDriver:
    """Create a Selenium WebDriver for the requested browser.

    Args:
        browser: Browser name, either "chrome" or "firefox".
        headless: Whether to run in headless mode.
        chrome_server_flags: Whether to use Chrome options suitable for EC2.

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
            driver.set_page_load_timeout(DEFAULT_TIMEOUT_SECONDS * 4)
            driver.set_script_timeout(DEFAULT_TIMEOUT_SECONDS)
            return driver

        if browser == "firefox":
            options = FirefoxOptions()

            if headless:
                options.add_argument("--headless")

            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(DEFAULT_TIMEOUT_SECONDS * 4)
            driver.set_script_timeout(DEFAULT_TIMEOUT_SECONDS)
            return driver

    except WebDriverException as exc:
        raise ConfigurationError(f"Could not initialise Selenium {browser} driver: {exc}") from exc

    raise ConfigurationError(f"Unsupported browser: {browser}")
```


This uses `DEFAULT_TIMEOUT_SECONDS * 4`, which is currently `120`, matching the Selenium client timeout you hit. A better design would pass `args.timeout` into `create_driver()`, but this minimal change is safer.

If you want page loads to fail sooner, use:

```python
driver.set_page_load_timeout(DEFAULT_TIMEOUT_SECONDS * 2)
```


That would be `60` seconds with your defaults.

---

## Improve the useless `#17 ... <unknown>` error messages

Your `summarise_error()` currently chooses the **last non-empty line** of the exception string. Selenium stack traces often end with unhelpful ChromeDriver frames like:

```plain text
#17 0x723dd2d3f55c <unknown>
```


Change it so it prefers the first meaningful line and ignores stack-frame-looking lines.

```python
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
```


After this, your logs should show errors closer to:

```plain text
Timed out receiving message from renderer
```


or:

```plain text
Read timed out. (read timeout=120)
```


instead of only:

```plain text
#17 0x723dd2d3f55c <unknown>
```


---

## Operational recommendation for this specific failed run

Because pages before and after the failures succeeded, this looks like **intermittent AO3/Cloudflare/browser instability**, not a bad URL or bad selector.

After applying the catch/logging fixes, resume from the first missing failed page:

```textmate
python capture_ao3_lists.py \
    --no-test-mode \
    --start-page-id 2025_3050 \
    --request-delay 6 \
    --request-jitter 4 \
    --max-retries 4 \
    --retry-delay 20 \
    --timeout 45
```


Why these values:

- `--request-delay 6 --request-jitter 4`: gentler crawling after AO3 starts behaving slowly.
- `--max-retries 4`: more chances for transient Cloudflare/AO3 failures.
- `--retry-delay 20`: lets temporary throttling cool down.
- `--timeout 45`: gives list pages a little more validation time.

Existing successfully captured pages will be skipped automatically unless you use `--reprocess`.

---

## Optional but useful: add `view_adult=true` to list URLs

Your saved AO3 HTML shows AO3 itself appending `view_adult=true` into pagination links. It probably does not hurt to include it in list URLs from the start. It may also reduce interstitial/adult-warning weirdness if AO3 applies it to list pages.

In `build_ao3_list_url()`, add:

```python
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
```


This is not the primary crash fix, but it makes the generated URLs closer to the URLs AO3 uses after interaction.

---

## Summary

The immediate bug is that `driver.get(...)` can raise `urllib3.exceptions.ReadTimeoutError`, and `capture_one_page()` does **not catch it**, so the full batch crashes.

Apply these fixes in order:

1. **Import and catch `ReadTimeoutError`**.
2. **Improve `summarise_error()`** so logs show real causes.
3. **Set Selenium page-load/script timeouts**.
4. Resume with slower delays and more retries from `2025_3050`.

The failed pages are likely recoverable by rerunning; the current script just needs to handle Selenium/ChromeDriver stalls more defensively.

## Me
I agree with your suggestions. Can I have the entire revised programme?

## AI Assistant
Below is the complete revised `capture_ao3_lists.py` incorporating:

- `ReadTimeoutError` handling
- clearer error summaries
- Selenium page-load/script timeouts
- `view_adult=true` in generated AO3 list URLs
- slightly safer driver timeout configuration using the user-provided `--timeout`
