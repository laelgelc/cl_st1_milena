## Me
I agree with you. Now, moving on one step, from `Preliminary Phase 1` to `Phase 1 - Data Collection` (`README.md`). I'd like to organise the data collection (web scraping) into two subphases. In the first phase, since AO3 works with well-defined `URL Query Parameters`, I'd like to capture the list pages according to the `List URL ranges` in the selection. Each list page offers rich metadata for each work that can be post-processed and organised. The second phase would focus on scraping the works and capture further metadata if appropriate.

Focusing on the first subphase `List Collection`, I'd like to design a programme named `capture_ao3_lists.py` (not the one in `cl_st1_preph1_milena/capture_ao3_lists.py` because that one was a pre-phase 1 prototype) based on what we have discussed so far and implement a batch processing design similar to the `download_videos.md` and `download_videos.py` reference implementations from another project. The first task will be writing the `capture_ao3_lists.md` programme development specification following the `download_videos.md` reference. But before that, let's discuss a little bit.

In this subphase, the input is fixed, as can be seen in the selection - should we compile a JSON input document?

Also, please consider the parameter-based Chrome/Firefox mechanism in `getwebpageselenium.py`. There will be no need to deliver a text-scraped version of the web page lists because this can be dealt with afterwards.

It is important that the programme is portable, because the production run will be done on an EC2 instance.

Is it clear? What do you think?

## AI Assistant
Yes, it is clear. I think the proposed two-subphase structure is exactly the right move:

1. **List Collection**: capture stable, reproducible AO3 search/list pages as HTML.
2. **Works Collection**: later capture selected full works and richer/current metadata.

For the first subphase, the goal should be **HTML acquisition only**, not metadata extraction and not text extraction. Metadata extraction can be a separate deterministic post-processing step over saved HTML.

## Should we compile a JSON input document?

**Yes, I strongly recommend compiling a JSON input document**, even though the input is currently “fixed”.

The reason is not because the programme *needs* JSON to generate the URLs. It could generate the year ranges internally. The reason is that JSON gives you a **research-audit artifact**: it records exactly what was intended to be captured, with the date ranges, expected pages, expected counts, filters, and naming rules.

For reproducible corpus collection, that is valuable.

I would separate:

- **Programme logic**: generic AO3 list-page capture engine.
- **Collection plan**: JSON file describing this particular study’s list ranges.

That means `capture_ao3_lists.py` is reusable if the ranges change later, or if you decide to collect 2018 or 2026, or change `crossover`, language, date ranges, etc.

A good default input file could be something like:

```plain text
corpus/00_sources/ao3_list_ranges.json
```


or:

```plain text
corpus/00_sources/ao3_list_collection_plan.json
```


For Phase 1, I prefer the second name because it is explicit that this is the planned capture configuration, not extracted metadata.

---

## Proposed JSON structure

I would make the JSON slightly richer than just URLs. Instead of storing both first and last URL as raw strings, store the **query parameters and page range**, then let the programme build canonical URLs.

Example:

```json
{
  "collection_name": "ao3_original_work_english_lists",
  "created_on": "2026-10-12",
  "base_url": "https://archiveofourown.org/works",
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
    }
  ]
}
```


This is better than raw URL lists because it:

- avoids copying very long URLs repeatedly;
- reduces typo risk;
- makes filters auditable;
- makes future variations easy;
- allows the programme to verify expected page counts;
- enables `--start-page-id 2024_0123` or similar later.

However, I would also include the generated URL in the run manifest for each captured page, so the exact requested URL is still recorded.

---

## Which years should be in the first production plan?

The README currently says the main study focuses on **2020–2025**, while the selected URL ranges also include 2019 and 2026.

For `Phase 1 - Data Collection`, I would recommend making the **default collection plan match the study design**:

- **2020**
- **2021**
- **2022**
- **2023**
- **2024**
- **2025**

Then optionally include 2019 and 2026 in the JSON with an `"enabled": false` flag, or put them in a separate exploratory plan.

Example:

```json
{
  "year": 2026,
  "enabled": false,
  "reason": "Outside primary 2020-2025 study window"
}
```


This avoids ambiguity between “available ranges” and “chosen corpus collection window”.

---

## Directory layout

For portability and resumability, I would suggest a clear corpus layout:

```plain text
cl_st1_ph1_milena/
  capture_ao3_lists.md
  capture_ao3_lists.py
  corpus/
    00_sources/
      ao3_list_collection_plan.json
    01_ao3_list_pages/
      2020/
        2020_0001.html
        2020_0002.html
      2021/
        2021_0001.html
      ...
      capture_ao3_lists.log
      capture_ao3_lists_manifest.json
      capture_ao3_lists_manifest_20261012T143012Z.json
```


I prefer year subdirectories:

```plain text
corpus/01_ao3_list_pages/2025/2025_0001.html
```


rather than placing all list pages flat in one directory, because the full run may produce around:

- 2020: 822 pages
- 2021: 1,129 pages
- 2022: 1,460 pages
- 2023: 1,891 pages
- 2024: 2,286 pages
- 2025: 3,132 pages

Total for 2020–2025:

```plain text
10,720 HTML files
```


A flat directory with 10k+ files is manageable, but year folders are cleaner.

---

## Naming convention

Use predictable names:

```plain text
2025_0001.html
2025_0002.html
...
2025_3132.html
```


The zero-padding should be configurable but default to 4 digits, which covers up to 9999 pages.

I would define a page identifier:

```plain text
2025_0001
```


This can be used for:

- output filename;
- manifest item ID;
- `--start-page-id`;
- logs.

---

## Browser mechanism

Yes, preserve the existing browser choice:

```shell script
--browser chrome
--browser firefox
```


Default should probably remain:

```plain text
chrome
```


But for EC2, Chrome/Chromium tends to be easier to install and run headless in many environments, so the programme should explicitly support Chrome options useful for server contexts:

- `--headless`
- `--no-sandbox`
- `--disable-dev-shm-usage`
- `--window-size=1920,1080`

The existing Chrome mechanism is a good starting point, but for portability I would make this more configurable.

Suggested CLI options:

```shell script
--browser chrome|firefox
--headless
--no-headless
--timeout 30
--page-delay 2
--retry-delay 10
--max-retries 2
```


For production, `--headless` should be default.

---

## AO3-specific page readiness

For list capture, we should not rely only on generic DOM stability. The capture programme should wait specifically for list-page content:

- `main` area exists
- `ol.work.index.group` exists
- ideally at least one `li.work` exists, unless it is a valid empty result page
- page heading matches expected year range broadly, if possible
- URL page parameter matches requested page

For these known ranges, every page should contain works, including the last pages, so a missing `li.work` should probably count as failure.

Recommended readiness condition for this subphase:

```plain text
Wait until CSS selector "ol.work.index.group li.work" is present.
```


Then optionally wait briefly for any AO3 TOS prompt handling.

---

## Consent prompt handling

This is important.

Since the list pages can show AO3’s TOS consent overlay, the programme should include an AO3-specific consent handler. It should:

1. Detect `#tos_prompt`.
2. If visible:
   - click `#tos_agree`;
   - click `#data_processing_agree`;
   - click `#accept_tos`;
   - wait until the prompt disappears.
3. Continue to list-content wait.

Since AO3 stores acceptance in browser local storage/cookies, this should normally happen once per Selenium session. The programme should ideally keep **one browser session open** for the whole run, not create a new browser per page. This is also much faster.

---

## One browser session or one per page?

For production, definitely **one browser session per run**, not one browser per page.

Reasons:

- much faster;
- AO3 consent only needs handling once;
- less load on EC2;
- less overhead from Selenium Manager/browser startup;
- easier to preserve cookies/localStorage during a run.

The programme can still restart the browser after certain failures if needed, but normal operation should be:

```plain text
create driver once
for page in planned_pages:
    driver.get(url)
    wait
    save
quit driver
```


Potential option:

```shell script
--restart-browser-every N
```


But I would not include this in the first version unless necessary. Keep the first implementation sequential and simple.

---

## Test mode

Following the reference implementation, keep **test mode enabled by default**.

For this programme, test mode should probably mean:

- process first 5 planned pages by default;
- preserve year/page planning order;
- apply `--start-page-id` before test limit;
- skip existing files before counting test limit, or after?

I recommend:

1. build planned pages;
2. apply `--start-page-id` if provided;
3. skip existing unless `--reprocess`;
4. apply test limit to pages that would actually be attempted.

That makes test mode useful even when many pages are already captured.

Example:

```shell script
python capture_ao3_lists.py
```


captures up to 5 missing pages.

Full run:

```shell script
python capture_ao3_lists.py --no-test-mode
```


---

## Resumability

The programme should be safe to re-run.

Default behaviour:

- if output HTML file exists, skip it;
- if `--reprocess` is given, overwrite it;
- manifest records skipped pages.

Support resume from specific page:

```shell script
--start-page-id 2023_0450
```


or separate arguments:

```shell script
--start-year 2023 --start-page 450
```


I prefer `--start-page-id` because it mirrors the reference `--start-video-id` idea and maps to the filename.

Example:

```shell script
python capture_ao3_lists.py \
  --no-test-mode \
  --start-page-id 2023_0450
```


This should start from `2023_0450` and continue through later pages/years in the configured plan order.

---

## Should the programme accept cookies?

For AO3 list capture, I would not require cookies. Instead, it should handle the TOS prompt interactively via Selenium. But I would consider adding optional browser profile/cookies support later if EC2 gets challenged.

For the first implementation/spec, I would include:

```shell script
--user-data-dir PATH
```


as optional advanced support? Maybe not necessary.

For portability and simplicity, I would avoid external cookies in v1 unless there is a demonstrated need. The programme can accept AO3 TOS during runtime.

---

## Politeness and ethical collection controls

This is important for production, especially on EC2.

The programme should include a delay between page captures. Even if AO3 responds quickly, 10,720 list pages is substantial.

Suggested defaults:

```plain text
--request-delay 3
--jitter 1
```


Meaning: wait 3 seconds plus a random 0–1 second between successful page captures.

This will make the run slower, but more respectful and safer.

Approximate time at 3–4 seconds per page for 10,720 pages:

```plain text
10,720 * 3.5 seconds ≈ 10.4 hours
```


This is acceptable for EC2 overnight. It is slower than the earlier 4-hour estimate, but much more polite.

I would also include:

```shell script
--stop-after N
```


optional, for chunked production runs. But test mode already handles small chunks. For EC2, `--start-page-id` plus skip-existing may be enough.

---

## Manifest design

Mirror the reference style:

```json
{
  "run_metadata": {
    "run_id": "20261012T143012Z",
    "tool_name": "capture_ao3_lists.py",
    "tool_version": "v1",
    "start_time": "...",
    "end_time": "...",
    "test_mode": true,
    "test_limit": 5,
    "reprocess": false,
    "browser": "chrome",
    "timeout_seconds": 30,
    "request_delay_seconds": 3,
    "collection_plan": "corpus/00_sources/ao3_list_collection_plan.json",
    "output_dir": "corpus/01_ao3_list_pages",
    "summary": {
      "planned": 5,
      "attempted": 5,
      "succeeded": 5,
      "failed": 0,
      "skipped_existing": 0
    }
  },
  "pages": [
    {
      "page_id": "2025_0001",
      "year": 2025,
      "page": 1,
      "url": "https://archiveofourown.org/works?...",
      "output_path": "corpus/01_ao3_list_pages/2025/2025_0001.html",
      "status": "success",
      "error": null,
      "duration_seconds": 3.28,
      "work_items_detected": 20,
      "tos_prompt_handled": true
    }
  ]
}
```


Useful statuses:

| Status              | Meaning                                               |
|---------------------|-------------------------------------------------------|
| `success`           | HTML captured and saved                               |
| `failed`            | Capture attempted but failed                          |
| `skipped_existing`  | HTML already existed and `--reprocess` was not set    |
| `failed_validation` | Page loaded but expected AO3 list content was missing |

---

## Page validation

After loading a page, before saving it as successful, the programme should inspect the DOM minimally.

Validation should check:

1. There is an AO3 list container:
   - `ol.work.index.group`
2. There are work items:
   - `li.work`
3. The count is usually 20, except possibly a last page.
4. The page heading exists:
   - something like `"Works in Original Work"`
5. Optional: page number in pagination matches requested page.

The programme does not need to extract metadata yet, but it should record the number of work items detected in the manifest. This gives immediate quality-control signal.

If a page contains 0 work items in these known page ranges, mark as failure.

---

## EC2 portability

For EC2, the specification should address:

### System dependencies

- Python 3.10+ or 3.11+
- Google Chrome or Chromium
- Selenium Python package
- browser driver via Selenium Manager, or system chromedriver if Selenium Manager works
- optional Firefox/geckodriver

### Recommended EC2 command

Similar to the reference:

```shell script
nohup bash run_python_ec2.sh \
  capture_ao3_lists.py \
    --collection-plan corpus/00_sources/ao3_list_collection_plan.json \
    --output-dir corpus/01_ao3_list_pages \
    --browser chrome \
    --no-test-mode \
> process_output.log 2>&1 &
```


### Chrome flags

On EC2, Chrome usually needs:

```plain text
--headless=new
--no-sandbox
--disable-dev-shm-usage
--disable-gpu
--window-size=1920,1080
```


The programme should include these for Chrome by default or via a `--server-mode` option. I would make them default for headless Chrome because they are harmless in most environments and helpful on servers.

---

## Should metadata extraction be included?

For this subphase: **no**.

But do minimal validation only:

- count work blurbs;
- verify page type;
- maybe record page title and heading.

Do not parse and export all work metadata yet. That should be a separate programme, perhaps:

```plain text
extract_ao3_list_metadata.py
```


This separation is clean:

1. `capture_ao3_lists.py`: network/Selenium/browser concerns.
2. `extract_ao3_list_metadata.py`: deterministic offline parsing.
3. `capture_ao3_works.py`: network/Selenium/browser for selected full works.
4. `extract_ao3_work_text.py`: deterministic offline extraction.

---

## My recommendation for the first specification

The `capture_ao3_lists.md` should follow the same broad structure as the video spec, but adapted:

1. High-level functionality
2. Key behaviours
3. Input/output specification
4. Command-line interface
5. Argument validation
6. Environment and configuration
7. Core processing architecture
8. AO3 list-page capture behaviour
9. Selenium/browser behaviour
10. TOS consent handling
11. JSON manifest design
12. Logging specification
13. Error handling and resiliency
14. Docstrings and in-code documentation
15. Suggested constants
16. Development notes
17. Acceptance criteria
18. Short README section

---

## Main design decisions I would lock in now

I would design `capture_ao3_lists.py` with the following decisions:

| Decision            | Recommendation                                           |
|---------------------|----------------------------------------------------------|
| Input source        | JSON collection plan                                     |
| Default plan path   | `corpus/00_sources/ao3_list_collection_plan.json`        |
| Output              | HTML only                                                |
| Output layout       | `corpus/01_ao3_list_pages/<year>/<year>_<page:04d>.html` |
| Browser             | Chrome by default, Firefox optional                      |
| Session model       | one browser session per run                              |
| Text extraction     | no                                                       |
| Metadata extraction | no, except validation counts                             |
| Consent handling    | yes, AO3-specific                                        |
| Page readiness      | wait for `ol.work.index.group li.work`                   |
| Test mode           | enabled by default, 5 pages                              |
| Re-run behaviour    | skip existing by default                                 |
| Resume              | `--start-page-id YEAR_NNNN`                              |
| Manifest            | latest + per-run timestamped                             |
| Logging             | append-only                                              |
| Rate limiting       | request delay + optional jitter                          |
| Workers             | sequential only in v1                                    |
| EC2 support         | explicit Chrome headless/server flags                    |

---

## One question before writing the specification

The only point I would clarify before drafting `capture_ao3_lists.md` is:

**Should Phase 1 List Collection include 2019 and 2026, or should the production collection plan be limited to 2020–2025?**

My recommendation:

- Primary plan: **2020–2025**
- Optional/disabled or separate plan: **2019 and 2026**

Everything else is clear enough to proceed to the specification.

## Me
Since the 2020-2025 definition was in the preliminary phase 1, please consider the 2026-2019 range in this phase 1.

## AI Assistant
Understood. For **Phase 1 - Data Collection**, we should treat the list collection range as:

```plain text
2019–2026 inclusive
```


organised in descending order if following the current README/list-range presentation:

```plain text
2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019
```


or ascending order if prioritising chronological corpus organisation:

```plain text
2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
```


For batch execution and resuming, either is fine, but I would recommend **descending order only if the data collection strategy is newest-first**. Otherwise, **ascending order is cleaner analytically**.

Given your list ranges are currently documented newest-first, the specification can define the JSON plan as the source of truth and preserve the order in that file. That way, if the plan lists `2026` first, the programme processes `2026` first.

## Updated recommendation

The first subphase should use:

```plain text
corpus/00_sources/ao3_list_collection_plan.json
```


as the fixed input plan for the Phase 1 list capture.

It should include all eight yearly strata:

| Year | Pages |
|-----:|------:|
| 2026 | 3,793 |
| 2025 | 3,132 |
| 2024 | 2,286 |
| 2023 | 1,891 |
| 2022 | 1,460 |
| 2021 | 1,129 |
| 2020 |   822 |
| 2019 |   531 |

Total pages:

```plain text
15,044 list pages
```


At approximately 3–4 seconds per page, this is likely a **12–17 hour** production run, depending on AO3 response times, EC2 performance, browser overhead, and politeness delay.

## JSON plan should not disable any of these years

So rather than using `"enabled": false` for 2019/2026, the Phase 1 plan should treat all ranges as enabled:

```json
{
  "collection_name": "ao3_original_work_english_lists_2019_2026",
  "created_on": "2026-10-12",
  "base_url": "https://archiveofourown.org/works",
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
    }
  ]
}
```


The full file would include 2026 through 2019.

## Important detail: page count vs expected works

The page count should be derived from `page_to`, not recalculated from `expected_works`, because AO3’s count can shift over time and the documented final page is the actual target.

Still, the manifest can record both:

- expected works count from the plan;
- planned page count;
- captured page count;
- detected work blurbs per page.

## Specification implication

In `capture_ao3_lists.md`, the programme should be described as:

> `capture_ao3_lists.py` captures AO3 list/search result pages for English works tagged as `Original Work`, excluding crossovers, across the Phase 1 collection window 2019–2026 inclusive. It reads the fixed collection plan from `corpus/00_sources/ao3_list_collection_plan.json`, generates canonical AO3 URLs from the plan’s query parameters and page ranges, and saves rendered HTML pages for later metadata extraction.

That gives us a clear Phase 1 scope.

I’m ready to draft `capture_ao3_lists.md` next with this 2019–2026 plan as the baseline.

## Me
I agree! Would it be possible to run the capture of lists in descending order? The reason is that the more recent years are more susceptible to list range redefinition because AO3 users are more active.

## AI Assistant
Yes — running the **List Collection** in **descending year order** is not only possible, it is the better choice for your reason.

AO3 list ranges are most volatile for recent years because users are actively posting, updating, deleting, orphaning, locking, and editing works. Since the lists are sorted by `revised_at`, the newest years — especially **2026** and then **2025** — are most likely to shift during a long production run. Capturing them first reduces the risk that the documented page ranges become stale before they are collected.

## Recommended capture order

Use this order in `ao3_list_collection_plan.json` and preserve it during planning:

```plain text
2026 → 2025 → 2024 → 2023 → 2022 → 2021 → 2020 → 2019
```


Within each year, I would still capture pages in ascending page order:

```plain text
2026_0001 → 2026_0002 → ... → 2026_3793
2025_0001 → 2025_0002 → ... → 2025_3132
...
```


This gives the most sensible combination:

- newest years first, because they are most volatile;
- first pages first within each year, because they are usually the most active/recent within that year’s filtered result set;
- predictable page IDs and resumability.

## Make the JSON plan the source of processing order

The programme specification should say:

> The programme must preserve the order of ranges in `ao3_list_collection_plan.json`. The Phase 1 plan lists years in descending order from 2026 to 2019, so the capture process prioritises the most volatile recent-year lists first.

This avoids hardcoding the order in the programme. The JSON plan controls it.

## Add an explicit order field if desired

Not strictly necessary, but you could include it for auditability:

```json
{
  "collection_name": "ao3_original_work_english_lists_2026_2019",
  "range_order": "descending_year",
  "page_order_within_year": "ascending_page",
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
    }
  ]
}
```


The programme can still simply process `ranges` in file order. The order fields are documentation/validation hints.

## Optional CLI override

For flexibility, the specification could include an optional argument:

```shell script
--range-order plan|ascending-year|descending-year
```


Default:

```plain text
plan
```


But I would avoid implementing this in v1 unless you expect frequent reordering. Simpler and more reproducible is:

```plain text
The JSON plan order is the run order.
```


That is the best design for a research pipeline.

## Important consequence for resume

With descending year order, `--start-page-id` should follow the plan order. For example:

```shell script
python capture_ao3_lists.py --no-test-mode --start-page-id 2025_0120
```


should process:

```plain text
2025_0120 → ... → 2025_3132
2024_0001 → ... → 2024_2286
...
2019_0531
```


It should **not** go back to 2026, because in the plan order 2026 comes before `2025_0120`.

## Summary

I recommend locking in this design:

| Aspect                 | Decision                               |
|------------------------|----------------------------------------|
| Year order             | Descending: 2026 to 2019               |
| Page order within year | Ascending: page 1 to final page        |
| Source of truth        | `ao3_list_collection_plan.json` order  |
| Resume logic           | Resume from page ID in plan order      |
| Rationale              | Capture most volatile AO3 ranges first |

This should be explicitly stated in `capture_ao3_lists.md`.
