## Me
Do you think cookies could increase the rate of success?

## AI Assistant
**Yes — cookies could plausibly increase the success rate**, but mostly by improving **session continuity and trust**, not by making AO3’s deep search pages inherently faster.

What you’re seeing is consistent with AO3/Cloudflare treating different sessions differently. Your normal browser has a long-lived, “human-looking” session; the Selenium browser is likely fresh, headless, and repetitive. Cookies may help reduce that gap.

## Why cookies might help

Cookies/local storage could help with:

1. **TOS consent persistence**  
   If every new Selenium session starts without accepted AO3 Terms, AO3 sees a fresh visitor. Persisting consent avoids repeatedly triggering the prompt.

2. **Cloudflare/session continuity**  
   If Cloudflare assigns benign session or clearance-like cookies, reusing them may make subsequent requests look less like a new automated client every run.

3. **Browser state continuity**  
   A persistent profile with cookies, local storage, cache, and normal browser state can look more like a regular browsing session than a disposable headless session.

4. **Reduced repeated friction**  
   AO3 may respond better when it sees a stable session over time rather than many short-lived sessions.

## But cookies are not a guaranteed fix

Cookies probably **will not fully solve**:

- AO3 `503 Page Responding Too Slowly` responses caused by server-side query generation;
- deep pagination cost;
- Cloudflare edge errors;
- rate or behaviour-based throttling from repeated requests;
- headless-browser fingerprinting;
- too-fast or too-regular request cadence.

If the key signal is behavioural — e.g. requesting hundreds of near-identical filtered pages in sequence — cookies alone may not help much.

## Best low-risk approach

I’d suggest using a **persistent Selenium browser profile**, rather than manually copying cookies from your personal browser.

That gives the Selenium run its own stable state:

- accepted TOS remains saved;
- cookies persist between runs;
- local storage persists;
- cache persists;
- the browser looks less “new” each time.

Conceptually:

```plain text
corpus/selenium_profiles/ao3_chrome/
```


Then Chrome uses that profile every run.

This is better than importing your personal cookies because it avoids mixing your normal browser identity/session with the collection tool.

## Ethical caution

I would **not** recommend using cookies to bypass explicit blocks, challenges, or access controls. But using a persistent browser profile to avoid re-accepting TOS and to keep stable session state is reasonable, especially since you are still:

- using a real browser;
- not logging in;
- not bypassing authentication;
- slowing down requests;
- recording diagnostics.

## My practical recommendation

Try this experiment:

1. Use a persistent Selenium profile.
2. Run one single-page diagnostic capture after an idle period.
3. Then run a short range of 5–10 pages with conservative delays.
4. Compare success rate against the fresh-profile/headless runs.

If success improves, the problem is likely session/fingerprint/trust related. If not, it is more likely AO3-side query cost or behaviour-based throttling from repeated pagination.

So: **yes, cookies/persistent browser state may help, but combine them with slower pacing and backoff; don’t rely on cookies alone.**

## Me
How to implement a persistent browser profile?

## AI Assistant
Yes. For Selenium, a **persistent browser profile** means telling Chrome/Firefox to use a fixed profile directory instead of a fresh temporary profile for every run.

That lets AO3-related state persist across runs, including:

- cookies;
- local storage;
- accepted TOS state;
- cache;
- some browser fingerprint/session continuity.

Below is a clean way to add this to `capture_ao3_lists.py`.

## 1. Add a default profile directory constant

```python
# ... existing code ...

DEFAULT_OUTPUT_DIR = "corpus/01_ao3_list_pages"
DEFAULT_LOG_FILE = "corpus/01_ao3_list_pages/capture_ao3_lists.log"
DEFAULT_MANIFEST_FILE = "corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json"
DEFAULT_BROWSER_PROFILE_DIR = "corpus/01_ao3_list_pages/browser_profiles"

DEFAULT_BROWSER = "chrome"
DEFAULT_HEADLESS = True
DEFAULT_CHROME_SERVER_FLAGS = True

# ... existing code ...
```


## 2. Add CLI arguments

Add these after the browser/headless options or near the other browser-related options.

```python
# ... existing code ...

    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Run browser with a visible window.",
    )
    parser.add_argument(
        "--persistent-browser-profile",
        action="store_true",
        help=(
            "Use a persistent Selenium browser profile so cookies, local storage, "
            "AO3 Terms consent, and browser cache survive across runs."
        ),
    )
    parser.add_argument(
        "--browser-profile-dir",
        type=Path,
        default=Path(DEFAULT_BROWSER_PROFILE_DIR),
        help=(
            "Base directory for persistent browser profiles. Used only when "
            "--persistent-browser-profile is provided. "
            f"Default: {DEFAULT_BROWSER_PROFILE_DIR}"
        ),
    )
    parser.add_argument(
        "--browser-profile-name",
        type=str,
        default="ao3_capture",
        help=(
            "Profile name under --browser-profile-dir. Used only when "
            "--persistent-browser-profile is provided. Default: ao3_capture"
        ),
    )
    parser.add_argument(
        "--chrome-server-flags",
        dest="chrome_server_flags",
        action="store_true",
        default=DEFAULT_CHROME_SERVER_FLAGS,
        help="Use Chrome flags suitable for headless Linux/EC2. This is the default.",
    )

# ... existing code ...
```


## 3. Validate the profile settings

```python
# ... existing code ...

    if args.start_page_id is not None and not args.start_page_id.strip():
        raise ConfigurationError("--start-page-id must not be empty when provided")
    if args.persistent_browser_profile and not args.browser_profile_name.strip():
        raise ConfigurationError("--browser-profile-name must not be empty when persistent profiles are enabled")

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        if args.diagnostics_dir is not None:
            args.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        if args.persistent_browser_profile:
            args.browser_profile_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Could not create required output directories: {exc}") from exc

# ... existing code ...
```


## 4. Update `create_driver()`

Change its signature and add profile support.

```python
# ... existing code ...

def create_driver(
        browser: str,
        headless: bool,
        chrome_server_flags: bool,
        timeout: int,
        persistent_browser_profile: bool = False,
        browser_profile_dir: Path | None = None,
        browser_profile_name: str = "ao3_capture",
) -> WebDriver:
    """Create a Selenium WebDriver for the requested browser."""
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

            if persistent_browser_profile:
                if browser_profile_dir is None:
                    raise ConfigurationError("browser_profile_dir is required when persistent profiles are enabled")
                chrome_profile_root = browser_profile_dir / "chrome" / browser_profile_name
                chrome_profile_root.mkdir(parents=True, exist_ok=True)
                options.add_argument(f"--user-data-dir={chrome_profile_root}")
                options.add_argument("--profile-directory=Default")

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout * 4)
            driver.set_script_timeout(timeout)
            return driver

        if browser == "firefox":
            options = FirefoxOptions()

            if headless:
                options.add_argument("--headless")

            if persistent_browser_profile:
                if browser_profile_dir is None:
                    raise ConfigurationError("browser_profile_dir is required when persistent profiles are enabled")
                firefox_profile_root = browser_profile_dir / "firefox" / browser_profile_name
                firefox_profile_root.mkdir(parents=True, exist_ok=True)
                options.profile = str(firefox_profile_root)

            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(timeout * 4)
            driver.set_script_timeout(timeout)
            return driver

    except WebDriverException as exc:
        raise ConfigurationError(f"Could not initialise Selenium {browser} driver: {exc}") from exc

    raise ConfigurationError(f"Unsupported browser: {browser}")

# ... existing code ...
```


## 5. Pass the new options from `main()`

```python
# ... existing code ...

        if planned_attempts > 0:
            logger.info("Creating Selenium browser session")
            driver = create_driver(
                browser=args.browser,
                headless=args.headless,
                chrome_server_flags=args.chrome_server_flags,
                timeout=args.timeout,
                persistent_browser_profile=args.persistent_browser_profile,
                browser_profile_dir=args.browser_profile_dir,
                browser_profile_name=args.browser_profile_name,
            )

# ... existing code ...
```


## 6. Log the profile configuration

```python
# ... existing code ...

    logger.info("Browser: %s; headless=%s", args.browser, args.headless)
    logger.info("Chrome server flags: %s", args.chrome_server_flags)
    logger.info("Persistent browser profile: %s", args.persistent_browser_profile)
    logger.info("Browser profile directory: %s", args.browser_profile_dir)
    logger.info("Browser profile name: %s", args.browser_profile_name)
    logger.info("Test mode: %s; test_limit=%s", args.test_mode, args.test_limit)

# ... existing code ...
```


## 7. Record it in the manifest

```python
# ... existing code ...

            "config": {
                "browser": args.browser,
                "headless": args.headless,
                "chrome_server_flags": args.chrome_server_flags,
                "persistent_browser_profile": args.persistent_browser_profile,
                "browser_profile_dir": str(args.browser_profile_dir),
                "browser_profile_name": args.browser_profile_name,
                "timeout_seconds": args.timeout,
                "max_retries": args.max_retries,
                "retry_delay_seconds": args.retry_delay,
                "request_delay_seconds": args.request_delay,

# ... existing code ...
```


## Example usage

### First run: create and warm up the profile

Use a visible browser once if you want to watch what happens:

```shell script
python capture_ao3_lists.py \
  --start-page-id 2026_3624 \
  --test-limit 1 \
  --reprocess \
  --timeout 60 \
  --persistent-browser-profile \
  --no-headless
```


If AO3 shows the TOS prompt, the script should accept it. That state should persist.

### Later runs: headless with same profile

```shell script
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2026_3625 \
  --limit-pages 10 \
  --timeout 90 \
  --request-delay 60 \
  --request-jitter 30 \
  --persistent-browser-profile \
  --diagnosis-mode
```


## Important cautions

- Do **not** use the same profile simultaneously in two running Selenium processes.
- Do **not** point Selenium at your personal everyday Chrome profile.
- Keep this profile project-specific, e.g.:

```plain text
corpus/01_ao3_list_pages/browser_profiles/chrome/ao3_capture/
```


- If the profile becomes corrupted or starts behaving strangely, delete the profile directory and let Selenium recreate it.
- This may improve success rate, but it will not replace conservative pacing/backoff.

## Me
Can I have the entire revised programme?

## AI Assistant
Below is the full revised `capture_ao3_lists.py` with:

- persistent browser profile support;
- diagnosis mode;
- improved AO3/Cloudflare diagnosis categories;
- `--limit-pages`;
- `--stop-page-id`;
- `--transient-error-backoff`;
- manifest/log updates.

```python
#omitted
```

## Me
Regarding your caution notes, does it harm if I run the programme and let it save a persistent profile and then move the processing to an EC2 instance with the same profile? Should I delete the profile on the EC2 instance before starting the processing?

## AI Assistant
It **can work**, but I would **not move a warmed browser profile from your laptop to EC2 as the default approach**. I’d usually start EC2 with a **fresh EC2-local persistent profile** and let it warm up there.

## Short answer

- **Does it harm to copy the profile from laptop to EC2?**  
  Not necessarily, but it can create confusing or counterproductive signals.

- **Should you delete the profile on EC2 before starting?**  
  If the EC2 profile was copied from your laptop, **I would delete it and let EC2 create its own persistent profile**, unless you have a specific reason to preserve it.

## Why copying a profile may be problematic

A browser profile is not just AO3 cookies. It can include:

- cookies;
- local storage;
- cache;
- browser preferences;
- profile metadata;
- extension state;
- HSTS/security state;
- hardware/platform-related state;
- possibly browser-version-specific files.

Moving that from a **local desktop environment** to **EC2 headless Linux** changes many things at once:

| Signal                 | Laptop              | EC2             |
|------------------------|---------------------|-----------------|
| IP address             | home/university/ISP | cloud provider  |
| OS/browser environment | desktop Linux       | server Linux    |
| display/headless       | possibly visible    | headless        |
| profile state          | created locally     | reused remotely |
| network geography      | local               | data-centre     |

From a trust/fingerprint perspective, that can look odd: **same cookies/profile state suddenly appearing from a different machine and cloud IP**.

That does not mean AO3/Cloudflare will punish it, but it may reduce the benefit of the persistent profile.

## Better approach

Use a **persistent profile, but create it on the machine where it will be used**.

### Recommended EC2 workflow

1. **Delete any copied profile on EC2**.
2. Start the programme on EC2 with `--persistent-browser-profile`.
3. Run a very small warm-up capture, e.g. one page.
4. Let it accept AO3 TOS and store state locally.
5. Continue future EC2 runs with the same EC2-local profile.

For example:

```shell script
python capture_ao3_lists.py \
  --start-page-id 2026_3624 \
  --test-limit 1 \
  --reprocess \
  --timeout 90 \
  --persistent-browser-profile \
  --diagnosis-mode
```


Then later:

```shell script
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2026_3625 \
  --request-delay 60 \
  --request-jitter 30 \
  --timeout 90 \
  --persistent-browser-profile \
  --diagnosis-mode
```


## When copying might be acceptable

Copying the profile might be okay if:

- it is a **dedicated Selenium profile**, not your personal browser profile;
- it contains no logged-in AO3 account;
- it contains no sensitive unrelated cookies;
- Chrome/Firefox versions are similar enough;
- you are prepared to delete it if behaviour gets worse.

But I still think EC2-local warm-up is cleaner and more reproducible.

## What I would not do

I would avoid:

- copying your personal everyday browser profile;
- copying a profile containing logged-in sessions;
- running the same profile simultaneously on laptop and EC2;
- switching the same profile back and forth between laptop and EC2 repeatedly;
- storing browser profiles in Git;
- sharing browser profiles between multiple EC2 instances.

## Important operational note

A persistent profile should be treated as **runtime state**, like logs or cache.

It should usually live in something like:

```plain text
corpus/01_ao3_list_pages/browser_profiles/
```


but it should **not** be version-controlled or moved casually.

If you have a `.gitignore`, add something like:

```plain text
corpus/01_ao3_list_pages/browser_profiles/
```


## My recommendation

For your case:

1. **Do not copy your laptop profile to EC2.**
2. If you already copied it, **delete it on EC2**.
3. Create a fresh EC2-local persistent profile.
4. Use conservative delays and diagnosis mode.
5. Keep using that same EC2-local profile for future EC2 runs.

That gives you the benefits of cookies/session continuity without introducing cross-machine fingerprint inconsistency.

## Me
Is the warm-up mandatory or could I start a full run straight away?

## AI Assistant
The warm-up is **not mandatory**. You *can* start a full run straight away with a fresh persistent profile.

However, I’d still recommend doing a **tiny warm-up run first**, because it is a cheap way to reduce uncertainty before launching a long EC2 job.

## Why warm-up helps

A warm-up run lets the profile establish:

- AO3 Terms of Service consent;
- cookies;
- local storage;
- basic browser cache;
- confirmation that Chrome/Selenium works correctly on EC2;
- confirmation that the profile directory is writable;
- confirmation that diagnosis/log/manifest paths are correct.

If something is wrong, you discover it after **one page**, not after starting an 11,000-page run.

## If you skip warm-up

If you start the full run immediately, it should still work in principle. The first page in the run should handle the TOS prompt if it appears, then the same browser session should retain that state for the rest of the run.

The risk is only practical:

- if the TOS handling fails, the run may fail early;
- if the profile path is not writable, the run may fail during browser startup;
- if AO3/Cloudflare reacts badly to the fresh headless profile, you may get many failures before noticing;
- if your pacing is too aggressive, the run may start producing 503/525 failures.

## Best compromise

Run a tiny test first:

```shell script
python capture_ao3_lists.py \
  --start-page-id 2026_3624 \
  --test-limit 1 \
  --reprocess \
  --timeout 90 \
  --persistent-browser-profile \
  --diagnosis-mode
```


Then start the full/resume run:

```shell script
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2026_3625 \
  --request-delay 60 \
  --request-jitter 30 \
  --timeout 90 \
  --persistent-browser-profile \
  --diagnosis-mode
```


## Bottom line

- **Mandatory?** No.
- **Recommended?** Yes.
- **Reason:** It verifies the EC2-local persistent profile and AO3 consent/session state before committing to a long run.
