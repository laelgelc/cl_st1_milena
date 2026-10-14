## Me
Moving on to `Works Collection` (README.md), we will break it up into two stages: `Capture AO3 work pages` and `Extract AO3 works text`. We are going to design the `capture_ao3_works.py` programme to handle the first stage. We could reuse the logic from `capture_ao3_lists.py` adapting it to the following scenario:

- The `ao3_works_metadata` information should be kept as the single source of information. We will use the `cl_st1_ph1_milena.ipynb` Jupyter notebook to select the works that are going to be captured as pages. Currently, there is a placeholder in the notebook and a bypass that creates the `corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson` collection plan.
- This collection plan should be the input to the `capture_ao3_works.py` programme. The relevant columns should be `work_id`, `full_work_url`, and `date_updated`.
- The output directory should be `corpus/02_ao3_work_pages`. The work pages should be saved in subdirectories named after the `year` captured from the `date_updated` field. The work pages should be named after the `work_id` plus the `.html` file extension.

Is it clear enough for writing the `capture_ao3_works.md` programme development specification?

## AI Assistant
Yes — it is clear enough to write the **`capture_ao3_works.md` programme development specification**.

The intended design is well-defined:

## Confirmed design

### Phase / stage

Under **Works Collection**, there will be two stages:

1. **Capture AO3 work pages**
   - implemented by `capture_ao3_works.py`
   - specified in `capture_ao3_works.md`

2. **Extract AO3 works text**
   - separate later programme/specification
   - out of scope for `capture_ao3_works.py`

### Source of truth

The canonical upstream source remains:

```plain text
corpus/00_sources/ao3_works_metadata/
```


The notebook:

```plain text
cl_st1_ph1_milena.ipynb
```


is responsible for selecting the works to capture and producing the work collection plan.

### Collection plan input

`capture_ao3_works.py` should read:

```plain text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```


The relevant required fields are:

- `work_id`
- `full_work_url`
- `date_updated`

The programme should treat that NDJSON file as the direct capture plan, not regenerate the selection itself.

### Output location

Captured work HTML pages should be saved under:

```plain text
corpus/02_ao3_work_pages/
```


### Output organisation

The output should be grouped by year extracted from `date_updated`:

```plain text
corpus/02_ao3_work_pages/<year>/<work_id>.html
```


For example, if:

```json
{
  "work_id": "85198816",
  "full_work_url": "https://archiveofourown.org/works/85198816?view_adult=true&view_full_work=true",
  "date_updated": "2026-10-13"
}
```


then the captured page should be saved as:

```plain text
corpus/02_ao3_work_pages/2026/85198816.html
```


### Reuse from list capture programme

It is also clear that `capture_ao3_works.py` should reuse the same architectural pattern as the list capture programme:

- Selenium-based capture;
- Chrome by default;
- Firefox optional;
- headless by default;
- EC2-compatible Chrome flags;
- AO3 Terms of Service prompt handling;
- one browser session per run;
- test mode by default;
- safe resumability by skipping existing HTML files unless `--reprocess` is used;
- append-only log;
- latest manifest plus timestamped per-run manifest;
- retries, request delay, jitter, and non-fatal per-work failures.

## Points I would make explicit in the specification

The request is clear enough, but the specification should explicitly settle these details:

1. **Default input path**

```plain text
corpus/00_sources/ao3_work_collection_plan/ao3_work_collection_plan.ndjson
```


2. **Default output paths**

```plain text
corpus/02_ao3_work_pages/
   corpus/02_ao3_work_pages/capture_ao3_works.log
   corpus/02_ao3_work_pages/capture_ao3_works_manifest.json
```


3. **Work identifier**

   Use `work_id` as the stable item ID and filename stem.

4. **Year derivation**

   Derive `year` from the first four characters of ISO-formatted `date_updated`, after validating that it matches something like:

```plain text
YYYY-MM-DD
```


5. **Readiness checks**

   For AO3 work pages, the selector should differ from list pages. The spec should require the page to contain work-page content, for example:

```plain text
#workskin
```


   and/or:

```plain text
#chapters
```


   plus general checks such as:

```plain text
document.readyState === "complete"
   body exists
```


6. **Adult content**

   Since `full_work_url` should already include:

```plain text
view_adult=true&view_full_work=true
```


   `capture_ao3_works.py` does not need to construct work URLs. It should use `full_work_url` exactly as supplied by the plan, after validating it is non-empty.

7. **Duplicate work IDs**

   The specification should decide what to do if the plan contains duplicate `work_id` values. Recommended behaviour:

   - fail fast by default, or
   - keep the first occurrence and mark later duplicates as skipped/duplicate.

   For reproducibility, I would recommend **fail fast by default**, unless duplicates are expected from the notebook selection process.

8. **Start/resume argument naming**

   For works, use:

```shell script
--start-work-id WORK_ID
```


   rather than `--start-page-id`.

9. **Manifest terminology**

   The manifest should have a top-level key such as:

```json
{
     "works": []
   }
```


   rather than `"pages"`.

10. **Out of scope**

   The spec should clearly state that this programme:

   - does not extract text;
   - does not parse metadata;
   - does not modify the notebook selection;
   - does not write `.txt` files;
   - only captures rendered AO3 work-page HTML.

## Suggested title

```markdown
# `capture_ao3_works.py` — Programme Specification for Development
```


## Conclusion

Yes, this is sufficiently clear to draft the full `capture_ao3_works.md` specification. The only small design choices to lock down are duplicate handling, work-page readiness selectors, and the exact resume argument name, but the overall input/output model and processing flow are already clear.

## Me
I agree with your remarks. Please go ahead and write the `capture_a3_works.md` specification document.