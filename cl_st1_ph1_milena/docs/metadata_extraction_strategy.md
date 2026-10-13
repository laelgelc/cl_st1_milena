## Me
This list page contains 20 works. Which metadata is available for capturing?

## AI Assistant
The 20-work AO3 list page provides **rich per-work metadata** that can be captured directly from each list item/blurb, without opening the full work pages.

Available metadata includes:

| Metadata field | Available on list page? | Notes |
|---|---:|---|
| **Work ID** | Yes | From the `<li id="work_...">` value and work URL. |
| **Title** | Yes | Linked in each work heading. |
| **Work URL** | Yes | Relative URL such as `/works/85198816`; can be converted to full AO3 URL. |
| **Author / pseud** | Yes | Usually shown after `by`. |
| **Author URL** | Yes | From the author/pseud link. |
| **Fandom(s)** | Yes | Displayed under each title. |
| **Rating** | Yes | From required tag icons/titles, e.g. `Explicit`, `Teen And Up Audiences`. |
| **Archive warnings** | Yes | From required tags and repeated in tag list. |
| **Category** | Yes | e.g. `F/F`, `F/M`, `M/M`, `Gen`, `Multi`, `Other`, `No category`. |
| **Completion status** | Yes | From required tag icon/title: `Complete Work` or `Work in Progress`. |
| **Date shown / updated date** | Yes | Displayed as `13 Oct 2026` in each blurb. Given the current sort/filter, this corresponds to the list’s date basis, i.e. updated/revised date. |
| **Language** | Yes | In stats block, e.g. `English`. |
| **Word count** | Yes | In stats block. |
| **Chapters** | Yes | Current/total format, e.g. `3/?`, `1/1`, `17/17`. |
| **Collections count** | Sometimes | Only shown when nonzero/present. |
| **Comments count** | Sometimes | Only shown when nonzero/present. |
| **Kudos count** | Sometimes | Only shown when nonzero/present. |
| **Bookmarks count** | Sometimes | Only shown when nonzero/present. |
| **Hits count** | Yes | Shown in stats block, including zero. |
| **Relationship tags** | Yes | When present, in the tags list. |
| **Character tags** | Yes | When present, in the tags list. |
| **Additional/freeform tags** | Yes | When present, in the tags list. |
| **Series membership** | Sometimes | When present, includes part number and series title/link. |
| **Summary** | Sometimes | Present for many works, absent for some. |
| **Chapter URL** | Sometimes | When current chapter count is linked, e.g. `/works/.../chapters/...`. |
| **Series URL** | Sometimes | When the work belongs to a series. |
| **Tag URLs** | Yes | Each tag link includes its AO3 tag URL. |

At the **page/list level**, the page also provides:

- **Result range:** `1 - 20`
- **Total works in the filtered result set:** `76,106`
- **Tag/search context:** `Original Work`
- **Applied filters**, including:
  - language: English
  - date range: 2026-01-01 to 2026-12-31
  - crossover exclusion
  - sort by date updated/revised
- **Pagination metadata:**
  - current page: `1`
  - next page URL
  - final visible page: `3806`
- **Facet/filter counts** for ratings, warnings, categories, characters, relationships, and additional tags.

For the planned list-page metadata extraction, the strongest core fields to capture are probably:

1. `year`
2. `list_page`
3. `work_id`
4. `title`
5. `author`
6. `author_url`
7. `fandoms`
8. `rating`
9. `warnings`
10. `category`
11. `completion_status`
12. `date_updated`
13. `language`
14. `words`
15. `chapters_current`
16. `chapters_total`
17. `collections`
18. `comments`
19. `kudos`
20. `bookmarks`
21. `hits`
22. `relationships`
23. `characters`
24. `freeforms`
25. `summary`
26. `series`
27. `work_url`

Some numeric fields should be treated as **nullable or zero-normalised**, because AO3 omits some stats when they are absent, especially comments, kudos, bookmarks, and collections.

## Me
Please examine this one just to check for anything new.

## AI Assistant
I examined this list page. **No fundamentally new metadata category appears** beyond what we already identified, but this page confirms several important **edge cases** the extractor should handle.

## New or confirmed edge cases

| Case | Example on this page | Capture implication |
|---|---|---|
| **Anonymous works** | `Seven Years` by `Anonymous` | Author may be plain text, not an `<a rel="author">` link. Store `author = "Anonymous"` and `author_url = null`. |
| **Anonymous blurb class** | `<li class="anonymous work blurb ...">` | Optional boolean field could be useful: `is_anonymous = true/false`. |
| **Missing summary** | `Nostalgia is your parents' pain`; `Titsicles and Fire` | `summary` must be nullable/empty. |
| **No category** | `No category` appears in required tags | Category should accept `"No category"` as a real value, not missing data. |
| **Multiple required categories in one icon** | `F/F, F/M, Multi`; `F/F, F/M, Gen, M/M, Multi, Other` | Split category values into a list rather than storing only one category. |
| **Multiple warnings in one required warning icon** | e.g. `Graphic Depictions Of Violence, Rape/Non-Con, Underage Sex` | Required warning icon title should also be splittable into multiple values. |
| **Work has zero hits** | Several works show `Hits: 0` | Distinguish present zero from missing stat. |
| **Stats omitted when zero/absent** | Comments/kudos/bookmarks/collections often omitted | Treat omitted stats as either `null` or normalise to `0`, but do so consistently. |
| **Series metadata** | `Part 20 of Simplify Your Life`, `Part 1 of Meet Me Under the Treetops` | Series can include part number, title, and URL. |
| **Very long tag lists** | Several works have extensive freeform tags | Extraction should not assume a small tag count. |
| **HTML-rich summaries** | Summary with `<p>`, `<br>`, `<strong>`, `<em>`, paragraphs | Preserve plain text and optionally raw/HTML summary if useful. |
| **Non-Original fandom despite filtered context** | Example: `Own universe - Fandom` appears as fandom on one work | Fandom should be captured as shown; later QC can flag non-`Original Work` fandoms. |
| **Page-level range** | `181 - 200 of 76,106 Works` | Confirms page-level range/total is useful for QC. |

## Recommended additions to the metadata schema

I would add or explicitly support these fields:

| Field | Reason |
|---|---|
| `is_anonymous` | Anonymous works do not expose author links. |
| `author_url` nullable | Required for anonymous/plain-text authors. |
| `author_pseud` nullable | If author text is anonymous or otherwise unlinked. |
| `categories` as list | Required category icon can contain multiple categories. |
| `archive_warnings` as list | Required warning icon can contain multiple warnings. |
| `summary_text` nullable | Some works have no summary. |
| `summary_html` optional | Useful if preserving formatting matters. |
| `series` as list | A work can belong to multiple series. |
| `stats_present` or per-stat nullable policy | To distinguish omitted from zero if needed. |

## Bottom line

This page does **not** introduce a new major metadata class, but it confirms the extractor must be robust to:

- anonymous authors;
- missing summaries;
- omitted stats;
- multi-valued required tags;
- series membership;
- very long tag lists;
- works whose fandom is not literally `Original Work` despite appearing in the filtered results.

## Me
Let's consider those and let's focus on the work-level metadata. Add a `full_work_url` metadata field based on `work_url` (position it to the right of `work_url`) including the automatic "Adult Content" acknowledgement and full work visualisation, e.g. `https://archiveofourown.org/works/76796521?view_adult=true&view_full_work=true`. Order them in the same order they appear on the list. What is the suggested metadata list?

## AI Assistant
Suggested **work-level metadata list**, ordered according to the order in which each work’s information appears in the AO3 list blurb:

| Order | Metadata field | Notes |
|---:|---|---|
| 1 | `work_id` | Numeric AO3 work ID, e.g. `76796521`. Extractable from `li id="work_..."` and from the work link. |
| 2 | `title` | Work title as displayed in the heading. |
| 3 | `work_url` | Canonical work URL, e.g. `https://archiveofourown.org/works/76796521`. |
| 4 | `full_work_url` | Full-work capture URL with adult-content acknowledgement and full-work view, e.g. `https://archiveofourown.org/works/76796521?view_adult=true&view_full_work=true`. |
| 5 | `author_name` | Displayed author/pseud text. For anonymous works: `Anonymous`. |
| 6 | `author_url` | Author/pseud URL when available. For anonymous works: `null`. |
| 7 | `is_anonymous` | Boolean derived from whether the author is shown as `Anonymous` / anonymous blurb class. |
| 8 | `gift_recipient` | Optional. Some works show `for <recipient>`. |
| 9 | `gift_recipient_url` | Optional recipient gift URL when present. |
| 10 | `fandoms` | List of fandom names as shown. Important for QC because some works may show non-`Original Work` fandoms. |
| 11 | `fandom_urls` | Parallel list of AO3 fandom tag URLs. Optional but useful. |
| 12 | `rating` | Required rating value, e.g. `Explicit`, `Mature`, `Teen And Up Audiences`, `Not Rated`. |
| 13 | `archive_warnings` | List of warning values. Must support multiple values. |
| 14 | `categories` | List of category values, e.g. `["F/F", "F/M", "Multi"]`; supports `No category`. |
| 15 | `completion_status` | `Complete Work` or `Work in Progress`. |
| 16 | `date_updated` | Date displayed in the blurb, e.g. `13 Oct 2026`. Given the current sorting/filtering, this should be interpreted as the list’s updated/revised date. |
| 17 | `warning_tags` | Warning tags repeated in the main tag list. |
| 18 | `relationship_tags` | Relationship tags from the tag list. |
| 19 | `character_tags` | Character tags from the tag list. |
| 20 | `freeform_tags` | Additional/freeform tags from the tag list. |
| 21 | `tag_urls` | Optional structured mapping/list preserving tag URLs for warnings, relationships, characters, and freeforms. |
| 22 | `summary_text` | Plain-text summary. Nullable/empty if no summary appears. |
| 23 | `summary_html` | Optional. Useful if preserving paragraphs, `<br>`, emphasis, or other formatting matters. |
| 24 | `series` | Optional list of series memberships. Each item should include at least series title, URL, and part number when present. |
| 25 | `language` | Work language as displayed in stats, e.g. `English`. |
| 26 | `language_code` | Optional, from the `lang` attribute when present, e.g. `en`. |
| 27 | `words` | Integer word count. |
| 28 | `chapters_current` | Current chapter count. |
| 29 | `chapters_total` | Total planned chapters. Nullable for `?`. |
| 30 | `latest_chapter_url` | Optional. Present when the chapter count links to a chapter URL. |
| 31 | `collections` | Collection count. Nullable or `0` if omitted, depending on chosen normalization policy. |
| 32 | `comments` | Comment count. Nullable or `0` if omitted. |
| 33 | `kudos` | Kudos count. Nullable or `0` if omitted. |
| 34 | `bookmarks` | Bookmark count. Nullable or `0` if omitted. |
| 35 | `hits` | Hit count. Usually present, including `0`. |

## Recommended final column order

For a flat JSONL/CSV/Excel export, I would use:

```plain text
work_id
title
work_url
full_work_url
author_name
author_url
is_anonymous
gift_recipient
gift_recipient_url
fandoms
fandom_urls
rating
archive_warnings
categories
completion_status
date_updated
warning_tags
relationship_tags
character_tags
freeform_tags
tag_urls
summary_text
summary_html
series
language
language_code
words
chapters_current
chapters_total
latest_chapter_url
collections
comments
kudos
bookmarks
hits
```


## `full_work_url` construction rule

Given:

```plain text
work_url = https://archiveofourown.org/works/76796521
```


derive:

```plain text
full_work_url = https://archiveofourown.org/works/76796521?view_adult=true&view_full_work=true
```


This should be generated for every work, whether or not adult-content acknowledgement is actually needed, because AO3 will simply ignore it when not applicable.

## Me
Can we make `date_updated` machine readable because we could derive `year` or `decade` for example if needed?

## AI Assistant
Yes. I would make `date_updated` **machine-readable in ISO 8601 date format**:

```plain text
YYYY-MM-DD
```


So AO3 display dates like:

```plain text
13 Oct 2026
31 Dec 2025
```


should become:

```plain text
2026-10-13
2025-12-31
```


That makes derived fields such as `year`, `month`, `decade`, or chronological sorting trivial and unambiguous.

## Recommendation

Use:

```plain text
date_updated
```


as the **machine-readable canonical field**, and optionally keep the original display value as:

```plain text
date_updated_raw
```


This gives both reproducibility and easy analysis.

## Updated suggested metadata order

```plain text
work_id
title
work_url
full_work_url
author_name
author_url
is_anonymous
gift_recipient
gift_recipient_url
fandoms
fandom_urls
rating
archive_warnings
categories
completion_status
date_updated
date_updated_raw
warning_tags
relationship_tags
character_tags
freeform_tags
tag_urls
summary_text
summary_html
series
language
language_code
words
chapters_current
chapters_total
latest_chapter_url
collections
comments
kudos
bookmarks
hits
```


## Example

For a work displayed as:

```plain text
13 Oct 2026
```


capture:

```json
{
  "date_updated": "2026-10-13",
  "date_updated_raw": "13 Oct 2026"
}
```


Then derived values can be computed later:

```json
{
  "year": 2026,
  "decade": "2020s"
}
```


## Note on `year`

Since the list collection already has a planned year stratum, you could still keep a separate field such as:

```plain text
collection_year
```


This would represent the **date-range stratum used to capture the list page**, while `date_updated` represents the **actual work date shown on the blurb**. In most cases they should agree, but keeping them separate is useful for QC.

## Me
Please refer to the attached AI Assistant chat. Let's work on the `extract_ao3_works_metadata.py` programme development specification, titled `# `extract_ao3_works_metadata.py` — Programme Specification for Development`. Consider the suggested `collection_year` field, to the right of the `date_updated_raw` field. Should the input be the `cl_st1_ph1_milena/corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json` file? The output could be the `cl_st1_ph1_milena/corpus/00_sources/ao3_works_metadata` file in NDJSON, TSV and XLSX formats. Is it clear? Am I missing something?

## AI Assistant
Yes — it is clear, and your proposed design is sensible.

## Short answer

The input should be:

```plain text
cl_st1_ph1_milena/corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


because that manifest is the best **source-of-truth index** for the captured list pages. It tells `extract_ao3_works_metadata.py`:

- which HTML files exist or were attempted;
- their `page_id`;
- their `year`;
- their AO3 list page number;
- their original/requested URL;
- their `output_path`;
- whether capture succeeded.

The extractor should then read only manifest pages with:

```plain text
status == "success"
```


and parse each corresponding saved HTML file.

The output should go under something like:

```plain text
cl_st1_ph1_milena/corpus/00_sources/ao3_works_metadata/
```


not as a single “file” path, because you want multiple output formats.

For example:

```plain text
cl_st1_ph1_milena/corpus/00_sources/ao3_works_metadata/
  ao3_works_metadata.ndjson
  ao3_works_metadata.tsv
  ao3_works_metadata.xlsx
  extract_ao3_works_metadata_manifest.json
  extract_ao3_works_metadata.log
```


## About `collection_year`

Yes, I would include `collection_year`, positioned immediately to the right of `date_updated_raw`.

The relevant date fields would therefore be:

```plain text
date_updated
date_updated_raw
collection_year
```


Where:

| Field              | Meaning                                                              |
|--------------------|----------------------------------------------------------------------|
| `date_updated`     | Machine-readable parsed AO3 blurb date, e.g. `2026-10-13`.           |
| `date_updated_raw` | Original AO3 display date, e.g. `13 Oct 2026`.                       |
| `collection_year`  | The yearly stratum from the manifest/list capture plan, e.g. `2026`. |

This is useful because `collection_year` represents the **query stratum**, while `date_updated` represents the **actual date displayed in the work blurb**. They should normally match, but keeping both supports QC.

## Suggested input/output specification

### Input

Primary input:

```plain text
--manifest corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


The programme should read:

```json
{
  "pages": [
    {
      "page_id": "2026_0001",
      "year": 2026,
      "page": 1,
      "url": "...",
      "current_url": "...",
      "output_path": "corpus/01_ao3_list_pages/2026/2026_0001.html",
      "status": "success"
    }
  ]
}
```


For each successful page, it should parse:

```plain text
output_path
```


and add page/list provenance to every extracted work row.

### Output

Recommended default output directory:

```plain text
--output-dir corpus/00_sources/ao3_works_metadata
```


Recommended files:

```plain text
ao3_works_metadata.ndjson
ao3_works_metadata.tsv
ao3_works_metadata.xlsx
extract_ao3_works_metadata_manifest.json
extract_ao3_works_metadata.log
```


The **NDJSON** should be the canonical machine-readable output. TSV and XLSX are convenient analysis/inspection exports.

## Suggested metadata column order

With `collection_year` inserted after `date_updated_raw`, I would use this final order:

```plain text
work_id
title
work_url
full_work_url
author_name
author_url
is_anonymous
gift_recipient
gift_recipient_url
fandoms
fandom_urls
rating
archive_warnings
categories
completion_status
date_updated
date_updated_raw
collection_year
warning_tags
relationship_tags
character_tags
freeform_tags
tag_urls
summary_text
summary_html
series
language
language_code
words
chapters_current
chapters_total
latest_chapter_url
collections
comments
kudos
bookmarks
hits
source_page_id
source_list_page
source_list_url
source_html_path
extraction_run_id
```


I would add the final provenance fields even though they are not “AO3 work metadata” strictly speaking. They are extremely useful for debugging, reproducibility, and later QC.

## Things you might be missing

Only a few design details should be clarified in the specification.

### 1. Directory vs file naming

You wrote:

> output could be the `cl_st1_ph1_milena/corpus/00_sources/ao3_works_metadata` file

I would define this as a **directory**, not a file, because it will contain several outputs.

Better:

```plain text
cl_st1_ph1_milena/corpus/00_sources/ao3_works_metadata/
```


### 2. Array/list fields in TSV and XLSX

Several fields are naturally lists:

```plain text
fandoms
archive_warnings
categories
relationship_tags
character_tags
freeform_tags
series
tag_urls
```


In NDJSON they can remain proper JSON arrays/objects.

But in TSV/XLSX, you need a policy. I recommend serialising list/object fields as compact JSON strings rather than joining with semicolons, because AO3 tags can themselves contain punctuation.

Example TSV/XLSX cell:

```json
["Graphic Depictions Of Violence","Rape/Non-Con"]
```


### 3. Missing stats policy

AO3 sometimes omits zero-valued stats such as comments, kudos, bookmarks, and collections.

You should decide whether omitted stats become:

```plain text
null
```


or:

```plain text
0
```


For analysis, `0` is often convenient. For strict representation, `null` means “not present in page HTML”.

My recommendation:

- use `0` for omitted count fields when AO3 conventionally omits zero values;
- optionally include no extra “present” fields unless needed.

So:

```plain text
collections
comments
kudos
bookmarks
```


would be integers defaulting to `0` if absent.

`hits` should also be an integer and is usually present, including `0`.

### 4. Duplicate work handling

Because AO3 list pages can shift over time, duplicate works could theoretically appear across captured pages, especially in volatile years.

The extractor should either:

1. output every occurrence and flag duplicates later; or
2. deduplicate by `work_id`.

For the first version, I recommend **do not silently deduplicate**. Instead:

- output all rows;
- include `source_page_id`;
- include an extraction manifest summary with duplicate counts by `work_id`.

That preserves auditability.

### 5. Extraction manifest

Besides the data files, create a manifest such as:

```plain text
extract_ao3_works_metadata_manifest.json
```


It should record:

- extraction run ID;
- input manifest path;
- output files;
- number of pages in input manifest;
- number of successful pages selected;
- number of pages parsed;
- number of works extracted;
- pages with parse errors;
- duplicate `work_id` count;
- tool version;
- timestamp.

### 6. Error handling

The specification should say what happens if:

- an HTML file listed in the manifest is missing;
- a page has no work blurbs;
- a work blurb is partially malformed;
- a date cannot be parsed;
- a number cannot be parsed.

Recommended policy:

- page-level failures go into the extraction manifest/log;
- malformed individual works should still produce a partial row if `work_id` and `title` are recoverable;
- unparseable fields become `null`;
- parsing warnings are counted.

### 7. Naming of `date_updated`

Since the AO3 list is sorted/filtered by `revised_at`, `date_updated` is appropriate. The raw field protects against any ambiguity.

### 8. Current manifest vs timestamped manifest

Using:

```plain text
capture_ao3_lists_manifest.json
```


as the default is fine because it is the “latest/current” manifest.

But the CLI should allow using a timestamped manifest too:

```plain text
--manifest corpus/01_ao3_list_pages/capture_ao3_lists_manifest_20261013T075915Z.json
```


That helps reproduce a specific capture run.

## Recommended clarification sentence for the spec

You could phrase the programme scope like this:

> `extract_ao3_works_metadata.py` is an offline metadata extraction programme. It reads the AO3 list capture manifest, selects successfully captured list pages, parses the corresponding saved HTML files, extracts work-level metadata in list order, and exports the result to NDJSON, TSV, and XLSX under `corpus/00_sources/ao3_works_metadata/`. The programme does not make network requests.

## Bottom line

You are not missing anything major. I would only tighten three points:

1. Treat `ao3_works_metadata` as an **output directory**, not a single file.
2. Add provenance fields and an extraction manifest.
3. Define serialisation and missing-value policies for list fields and omitted stats.

Otherwise, yes: **manifest in, metadata files out** is exactly the right architecture.

## Me
I agree with your recommendations. I think we've got it covered enough. Please go ahead and write the programme development specification.
