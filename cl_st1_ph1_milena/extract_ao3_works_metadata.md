# `extract_ao3_works_metadata.py` — Programme Specification for Development

## 1. High-level Functionality Specification

### Programme Summary

`extract_ao3_works_metadata.py` is an offline post-processing programme that extracts work-level metadata from captured Archive of Our Own (AO3) list-page HTML files.

This programme implements the **metadata extraction step** after the AO3 list pages have already been captured by `capture_ao3_lists.py`.

It reads the AO3 list capture manifest:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


selects pages whose capture status is:

```plain text
success
```


then parses the corresponding saved HTML files listed in each manifest page record.

The programme does **not** make network requests. It works entirely from local saved HTML files.

The programme extracts work-level metadata from each AO3 list-page work blurb and exports the resulting dataset in three formats:

```plain text
corpus/00_sources/ao3_works_metadata/ao3_works_metadata.ndjson
corpus/00_sources/ao3_works_metadata/ao3_works_metadata.tsv
corpus/00_sources/ao3_works_metadata/ao3_works_metadata.xlsx
```


The canonical machine-readable output is the **NDJSON** file. The TSV and XLSX files are convenience exports for inspection and analysis.

The programme must also write:

```plain text
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest.json
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata.log
```


The metadata extraction should preserve the order in which works appear in the list pages:

1. manifest page order;
2. work order within each HTML list page.

The programme should not silently deduplicate works. If duplicate `work_id` values are encountered, all occurrences should be exported, and duplicate counts should be reported in the extraction manifest.

---

## 2. Key Behaviours

The programme must:

- read an AO3 list capture manifest;
- select only pages with `status == "success"`;
- read each page’s `output_path`;
- parse each saved AO3 list-page HTML file;
- extract work-level metadata from each `li.work` blurb;
- preserve manifest order and page-internal work order;
- export work metadata to NDJSON, TSV, and XLSX;
- treat NDJSON as the canonical structured output;
- serialise list/object fields as JSON strings in TSV and XLSX;
- add page/list provenance fields to every extracted work record;
- add extraction run provenance fields to every extracted work record;
- log extraction progress and parsing warnings;
- create an extraction manifest summarising the run;
- continue processing other pages if one page cannot be parsed;
- continue processing other works if one work blurb is partially malformed;
- record duplicate `work_id` counts without dropping duplicates;
- avoid any network access.

---

## 3. Input / Output Specification

## 3.1 Input

### Primary input manifest

Default input:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


The input manifest is expected to contain:

```json
{
  "run_metadata": {
    "run_id": "20261013T075915Z",
    "tool_name": "capture_ao3_lists.py",
    "tool_version": "v1"
  },
  "pages": [
    {
      "page_id": "2026_0001",
      "year": 2026,
      "page": 1,
      "url": "https://archiveofourown.org/works?...",
      "current_url": "https://archiveofourown.org/works?...",
      "output_path": "corpus/01_ao3_list_pages/2026/2026_0001.html",
      "status": "success"
    }
  ]
}
```


The programme should process only page records where:

```plain text
status == "success"
```


All other page statuses should be ignored for extraction, but counted in the extraction manifest.

### Supported manifest variants

The programme should accept either the latest manifest:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


or a timestamped capture manifest, for example:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest_20261013T075915Z.json
```


This allows extraction from a specific capture run.

---

## 3.2 HTML input files

Each successful page record must provide an HTML path in:

```plain text
output_path
```


Example:

```plain text
corpus/01_ao3_list_pages/2026/2026_0001.html
```


The extractor should resolve this path relative to the current working directory unless it is already absolute.

If an HTML file listed in the manifest is missing, the page should be recorded as a page-level extraction failure, but the run should continue.

---

## 3.3 Output directory

Default output directory:

```plain text
corpus/00_sources/ao3_works_metadata/
```


The programme must create this directory if it does not exist.

---

## 3.4 Output files

The programme must write the following files by default:

```plain text
corpus/00_sources/ao3_works_metadata/ao3_works_metadata.ndjson
corpus/00_sources/ao3_works_metadata/ao3_works_metadata.tsv
corpus/00_sources/ao3_works_metadata/ao3_works_metadata.xlsx
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest.json
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata.log
```


A timestamped extraction manifest should also be written:

```plain text
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest_<run_id>.json
```


Example:

```plain text
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest_20261013T101530Z.json
```


---

## 4. Extracted Metadata Schema

## 4.1 Final column order

The exported dataset should use the following field order:

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


---

## 4.2 Field definitions

| Field                |           Type | Description                                                                                 |
|----------------------|---------------:|---------------------------------------------------------------------------------------------|
| `work_id`            | integer/string | AO3 work ID, extracted from `li id="work_..."` or the work URL. Prefer integer if possible. |
| `title`              |    string/null | Work title as displayed in the list blurb.                                                  |
| `work_url`           |    string/null | Canonical full AO3 work URL, e.g. `https://archiveofourown.org/works/76796521`.             |
| `full_work_url`      |    string/null | Full-work URL with adult acknowledgement and full-work view parameters.                     |
| `author_name`        |    string/null | Displayed author/pseud text. For anonymous works: `Anonymous`.                              |
| `author_url`         |    string/null | Full AO3 author/pseud URL when available. `null` for anonymous/plain-text authors.          |
| `is_anonymous`       |        boolean | Whether the work appears anonymous.                                                         |
| `gift_recipient`     |    string/null | Gift recipient display name when present.                                                   |
| `gift_recipient_url` |    string/null | Full AO3 gift recipient URL when present.                                                   |
| `fandoms`            |   list[string] | Fandom names as shown in the blurb.                                                         |
| `fandom_urls`        |   list[string] | Full AO3 URLs for fandom tag links.                                                         |
| `rating`             |    string/null | Rating from required tags.                                                                  |
| `archive_warnings`   |   list[string] | Archive warning values from required tags. Must support multiple values.                    |
| `categories`         |   list[string] | Category values from required tags. Must support multiple values and `No category`.         |
| `completion_status`  |    string/null | `Complete Work` or `Work in Progress`.                                                      |
| `date_updated`       |    string/null | Machine-readable date in `YYYY-MM-DD` format.                                               |
| `date_updated_raw`   |    string/null | Raw AO3 displayed date, e.g. `13 Oct 2026`.                                                 |
| `collection_year`    |   integer/null | Year stratum from the input manifest page record.                                           |
| `warning_tags`       |   list[string] | Warning tags repeated in the main tags list.                                                |
| `relationship_tags`  |   list[string] | Relationship tags from the main tags list.                                                  |
| `character_tags`     |   list[string] | Character tags from the main tags list.                                                     |
| `freeform_tags`      |   list[string] | Additional/freeform tags from the main tags list.                                           |
| `tag_urls`           |    object/list | Structured tag URL information. See below.                                                  |
| `summary_text`       |    string/null | Plain-text summary.                                                                         |
| `summary_html`       |    string/null | HTML summary content, preserving formatting where possible.                                 |
| `series`             |   list[object] | Series memberships.                                                                         |
| `language`           |    string/null | Work language as displayed, e.g. `English`.                                                 |
| `language_code`      |    string/null | Language code from `lang` attribute when present, e.g. `en`.                                |
| `words`              |   integer/null | Word count.                                                                                 |
| `chapters_current`   |   integer/null | Current chapter count.                                                                      |
| `chapters_total`     |   integer/null | Total planned chapters. `null` when AO3 shows `?`.                                          |
| `latest_chapter_url` |    string/null | Latest chapter URL if the chapter count is linked.                                          |
| `collections`        |        integer | Collections count. Default `0` if omitted.                                                  |
| `comments`           |        integer | Comments count. Default `0` if omitted.                                                     |
| `kudos`              |        integer | Kudos count. Default `0` if omitted.                                                        |
| `bookmarks`          |        integer | Bookmarks count. Default `0` if omitted.                                                    |
| `hits`               |   integer/null | Hits count. Usually present, including `0`.                                                 |
| `source_page_id`     |         string | Page ID from manifest, e.g. `2026_0001`.                                                    |
| `source_list_page`   |        integer | AO3 list page number from manifest.                                                         |
| `source_list_url`    |    string/null | Original list URL from manifest. Prefer `current_url` if available, otherwise `url`.        |
| `source_html_path`   |         string | Path to source HTML file.                                                                   |
| `extraction_run_id`  |         string | Run ID for this extraction execution.                                                       |

---

## 4.3 `full_work_url` construction

Given:

```plain text
work_url = https://archiveofourown.org/works/76796521
```


derive:

```plain text
full_work_url = https://archiveofourown.org/works/76796521?view_adult=true&view_full_work=true
```


Rules:

- Always generate `full_work_url` when `work_url` is available.
- Include both query parameters:
  - `view_adult=true`
  - `view_full_work=true`
- If the URL already contains query parameters, append the new parameters correctly.
- The generated URL should acknowledge AO3’s adult content interstitial and request full-work view.

---

## 4.4 `date_updated` and `collection_year`

The AO3 list blurb displays a date such as:

```plain text
13 Oct 2026
```


The extractor must preserve it as:

```plain text
date_updated_raw = "13 Oct 2026"
```


and parse it into ISO date format:

```plain text
date_updated = "2026-10-13"
```


The extractor must also include:

```plain text
collection_year = 2026
```


from the input manifest page record.

These fields have different meanings:

| Field              | Meaning                                           |
|--------------------|---------------------------------------------------|
| `date_updated`     | Parsed date actually displayed in the work blurb. |
| `date_updated_raw` | Original AO3 date string as captured.             |
| `collection_year`  | Year stratum used to capture the list page.       |

This separation supports quality control because a work’s displayed updated date should normally fall within its `collection_year`, but mismatches may reveal list volatility, parsing issues, or AO3 edge cases.

---

## 4.5 List and object fields

The following fields are naturally list or object fields:

```plain text
fandoms
fandom_urls
archive_warnings
categories
warning_tags
relationship_tags
character_tags
freeform_tags
tag_urls
series
```


In NDJSON, these fields must be written as native JSON arrays/objects.

In TSV and XLSX, these fields must be serialised as compact JSON strings.

Example TSV/XLSX cell:

```json
["Graphic Depictions Of Violence","Rape/Non-Con"]
```


Do **not** join lists with semicolons, because AO3 tags may contain punctuation.

---

## 4.6 Suggested `tag_urls` structure

The `tag_urls` field may be represented as an object containing tag categories:

```json
{
  "warnings": [
    {
      "name": "Graphic Depictions Of Violence",
      "url": "https://archiveofourown.org/tags/Graphic%20Depictions%20Of%20Violence/works"
    }
  ],
  "relationships": [],
  "characters": [],
  "freeforms": []
}
```


This preserves both tag text and AO3 tag links without creating many extra flat columns.

---

## 4.7 Suggested `series` structure

The `series` field should be a list of objects.

Example:

```json
[
  {
    "part": 9,
    "title": "The Lingering World",
    "url": "https://archiveofourown.org/series/4633069"
  }
]
```


A work may belong to multiple series, so this must be a list.

---

## 4.8 Missing-value policy

Use the following missing-value policy:

| Field category                     | Missing value                                                       |
|------------------------------------|---------------------------------------------------------------------|
| Text fields                        | `null`                                                              |
| URL fields                         | `null`                                                              |
| Boolean fields                     | `false` where derivable, otherwise `null` only if genuinely unknown |
| List fields                        | empty list `[]`                                                     |
| Object fields                      | empty object `{}` or structured empty object                        |
| Numeric stat fields omitted by AO3 | `0` for collections/comments/kudos/bookmarks                        |
| Hits                               | integer if present, `null` if unparseable/missing                   |
| `chapters_total` shown as `?`      | `null`                                                              |
| Unparseable dates                  | `date_updated = null`, preserve `date_updated_raw`                  |

---

## 5. Command-line Interface

## 5.1 Default usage

```shell script
python extract_ao3_works_metadata.py
```


Default behaviour:

- input manifest: `corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json`
- output directory: `corpus/00_sources/ao3_works_metadata`
- output base name: `ao3_works_metadata`
- process only successful captured pages;
- export NDJSON, TSV, and XLSX;
- write extraction manifest;
- write extraction log;
- do not deduplicate works;
- continue after page-level parse failures;
- exit non-zero if any page-level extraction failures occur.

---

## 5.2 Optional arguments

### Input manifest

```shell script
--input-manifest PATH
```


Default:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


Description:

Path to the AO3 list capture manifest produced by `capture_ao3_lists.py`.

---

### Output directory

```shell script
--output-dir PATH
```


Default:

```plain text
corpus/00_sources/ao3_works_metadata
```


Description:

Directory where NDJSON, TSV, XLSX, log, and extraction manifest files are written.

---

### Output base name

```shell script
--output-basename NAME
```


Default:

```plain text
ao3_works_metadata
```


Description:

Base filename for data outputs.

With default settings, output files are:

```plain text
ao3_works_metadata.ndjson
ao3_works_metadata.tsv
ao3_works_metadata.xlsx
```


---

### Log file

```shell script
--log-file PATH
```


Default:

```plain text
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata.log
```


Description:

Path to the append-only extraction log.

---

### Extraction manifest file

```shell script
--manifest-file PATH
```


Default:

```plain text
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest.json
```


Description:

Path to the latest extraction manifest. A timestamped per-run copy should also be written.

---

### Output formats

```shell script
--formats ndjson tsv xlsx
```


Default:

```plain text
ndjson tsv xlsx
```


Description:

Output formats to write.

Allowed values:

```plain text
ndjson
tsv
xlsx
```


Examples:

```shell script
python extract_ao3_works_metadata.py --formats ndjson
```


```shell script
python extract_ao3_works_metadata.py --formats ndjson tsv
```


---

### Limit pages

```shell script
--limit-pages N
```


Default:

```plain text
None
```


Description:

Optional development/testing control. Limits the number of successful manifest pages to parse.

Example:

```shell script
python extract_ao3_works_metadata.py --limit-pages 10
```


---

### Start page ID

```shell script
--start-page-id PAGE_ID
```


Default:

```plain text
None
```


Description:

Start extraction from a specific page ID in manifest order.

Example:

```shell script
python extract_ao3_works_metadata.py --start-page-id 2026_0500
```


The specified page is included. All successful pages before it are skipped.

If the page ID is not found among successful manifest pages, the programme must exit with a configuration error.

---

### End page ID

```shell script
--end-page-id PAGE_ID
```


Default:

```plain text
None
```


Description:

Stop extraction after a specific page ID in manifest order.

The specified page is included.

Example:

```shell script
python extract_ao3_works_metadata.py \
  --start-page-id 2026_0500 \
  --end-page-id 2026_0600
```


---

### Overwrite outputs

```shell script
--overwrite
```


Default:

```plain text
False
```


Description:

If omitted and output data files already exist, the programme should fail fast to avoid accidentally overwriting data.

If provided, existing output data files may be overwritten.

Logs remain append-only.

---

### Strict mode

```shell script
--strict
```


Default:

```plain text
False
```


Description:

In strict mode, any page-level parse failure or malformed work record causes the run to exit non-zero.

Without strict mode, the programme continues after recoverable parse errors and reports them in the manifest.

---

## 5.3 Example commands

### Default extraction

```shell script
python extract_ao3_works_metadata.py
```


### Extract from a timestamped capture manifest

```shell script
python extract_ao3_works_metadata.py \
  --input-manifest corpus/01_ao3_list_pages/capture_ao3_lists_manifest_20261013T075915Z.json
```


### Development test on first 10 successful pages

```shell script
python extract_ao3_works_metadata.py \
  --limit-pages 10 \
  --overwrite
```


### Extract only NDJSON

```shell script
python extract_ao3_works_metadata.py \
  --formats ndjson \
  --overwrite
```


### Extract a page range

```shell script
python extract_ao3_works_metadata.py \
  --start-page-id 2026_0500 \
  --end-page-id 2026_0600 \
  --overwrite
```


---

## 6. Argument Validation

The programme must fail fast with a clear message if:

- the input manifest file does not exist;
- the input manifest path is not a file;
- the input manifest contains invalid JSON;
- the input manifest is missing the top-level `pages` list;
- no successful pages are available for extraction;
- `--formats` contains unsupported values;
- `--limit-pages` is provided and is less than or equal to zero;
- `--start-page-id` is provided but not found among successful pages;
- `--end-page-id` is provided but not found among successful pages;
- `--end-page-id` occurs before `--start-page-id`;
- output directory cannot be created;
- output files already exist and `--overwrite` is not provided;
- XLSX output is requested but the required Excel writing dependency is unavailable.

A validation error should:

- be printed clearly to the console;
- be written to the log if logging has already been configured;
- cause the programme to exit with status code `2`.

---

## 7. Environment and Dependencies

## 7.1 Required Python version

Recommended:

```plain text
Python 3.10+
```


## 7.2 Required packages

The programme should use Beautiful Soup for HTML parsing.

Suggested dependency:

```plain text
beautifulsoup4
```


For XLSX output, use one of:

```plain text
openpyxl
```


or:

```plain text
pandas
openpyxl
```


Recommended simple dependency set:

```plain text
beautifulsoup4
openpyxl
```


The programme should not require Selenium because it does not open a browser or access the network.

## 7.3 Suggested standard-library modules

```plain text
argparse
csv
datetime
html
json
logging
pathlib
re
sys
time
urllib.parse
collections
typing
```


---

## 8. Core Processing Architecture

## 8.1 High-level flow

The programme must follow this workflow:

1. **Startup**
   - Parse command-line arguments.
   - Generate a UTC extraction run ID.
   - Set up logging.
   - Validate arguments.
   - Load the input capture manifest.
   - Select successful pages.
   - Apply `--start-page-id`, `--end-page-id`, and `--limit-pages`.

2. **Output preparation**
   - Create output directory if needed.
   - Check whether output files already exist.
   - Fail unless `--overwrite` is provided.

3. **Extraction**
   - For each selected page:
     - read local HTML;
     - parse with Beautiful Soup;
     - locate AO3 work blurbs;
     - extract metadata for each work;
     - add source page provenance;
     - add extraction run provenance;
     - append records to in-memory list or streaming writer;
     - record page-level extraction status.

4. **Duplicate analysis**
   - Count duplicate `work_id` values.
   - Do not remove duplicates.
   - Record duplicate summary in extraction manifest.

5. **Output writing**
   - Write NDJSON if requested.
   - Write TSV if requested.
   - Write XLSX if requested.
   - Write latest extraction manifest.
   - Write timestamped extraction manifest.
   - Log final summary.

6. **Exit**
   - Exit `0` if extraction completed with no page-level failures.
   - Exit `1` if extraction completed but recoverable page-level failures occurred.
   - Exit `2` for configuration/validation errors.
   - Exit `130` for keyboard interruption.

---

## 8.2 Suggested functions

### CLI parsing

```python
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for AO3 work metadata extraction."""
```


### Logging setup

```python
def setup_logging(log_file: Path) -> logging.Logger:
    """Configure append-only file logging and console logging."""
```


### Input manifest loading

```python
def load_capture_manifest(manifest_path: Path) -> dict:
    """Load and validate the AO3 list capture manifest."""
```


### Page selection

```python
def select_successful_pages(
    capture_manifest: dict,
    start_page_id: str | None = None,
    end_page_id: str | None = None,
    limit_pages: int | None = None
) -> list[dict]:
    """Select successful captured pages for metadata extraction."""
```


### HTML parsing

```python
def parse_html_file(html_path: Path) -> BeautifulSoup:
    """Read and parse a saved AO3 list-page HTML file."""
```


### Page extraction

```python
def extract_page_works(
    page_record: dict,
    extraction_run_id: str
) -> tuple[list[dict], dict]:
    """Extract all work metadata records from one AO3 list-page HTML file."""
```


### Work extraction

```python
def extract_work_metadata(
    work_item: Tag,
    page_record: dict,
    extraction_run_id: str
) -> dict:
    """Extract a single AO3 work metadata record from one list-page work blurb."""
```


### URL normalisation

```python
def absolute_ao3_url(href: str | None) -> str | None:
    """Convert an AO3 relative URL to an absolute URL."""
```


### Full-work URL construction

```python
def build_full_work_url(work_url: str | None) -> str | None:
    """Build a full-work AO3 URL with adult acknowledgement and full-work view."""
```


### Date parsing

```python
def parse_ao3_display_date(date_raw: str | None) -> str | None:
    """Parse an AO3 display date into ISO YYYY-MM-DD format."""
```


### Numeric parsing

```python
def parse_int(text: str | None) -> int | None:
    """Parse an integer from AO3 text containing commas or whitespace."""
```


### Chapter parsing

```python
def parse_chapters(chapters_text: str | None) -> tuple[int | None, int | None]:
    """Parse AO3 chapter text such as '3/?' or '1/1'."""
```


### Output writing

```python
def write_ndjson(records: list[dict], output_path: Path) -> None:
    """Write metadata records as newline-delimited JSON."""
```


```python
def write_tsv(records: list[dict], output_path: Path, fieldnames: list[str]) -> None:
    """Write metadata records as TSV, serialising list/object fields as JSON strings."""
```


```python
def write_xlsx(records: list[dict], output_path: Path, fieldnames: list[str]) -> None:
    """Write metadata records as XLSX, serialising list/object fields as JSON strings."""
```


### Manifest writing

```python
def write_extraction_manifests(
    manifest: dict,
    manifest_file: Path,
    run_id: str
) -> tuple[Path, Path]:
    """Write latest and timestamped extraction manifest files."""
```


### Main orchestration

```python
def main() -> int:
    """Run AO3 work metadata extraction and return an exit code."""
```


---

## 9. HTML Parsing Requirements

## 9.1 Work item selection

Each AO3 list-page work item should be selected using:

```css
li.work
```


or more specifically:

```css
ol.work.index.group li.work
```


The extractor should preserve the order returned by the document.

---

## 9.2 Work ID extraction

Preferred source:

```html
<li id="work_76796521" ...>
```


Extract:

```plain text
76796521
```


Fallback source:

```html
<a href="/works/76796521">Title</a>
```


---

## 9.3 Title and work URL

The title link is normally inside the work heading.

Extract:

- title text;
- `href`;
- absolute `work_url`;
- generated `full_work_url`.

Example:

```json
{
  "title": "Gym Teacher",
  "work_url": "https://archiveofourown.org/works/76796521",
  "full_work_url": "https://archiveofourown.org/works/76796521?view_adult=true&view_full_work=true"
}
```


---

## 9.4 Author extraction

The extractor must handle both linked and anonymous/plain-text authors.

Linked author example:

```html
<a rel="author" href="/users/example/pseuds/example">example</a>
```


Extract:

```json
{
  "author_name": "example",
  "author_url": "https://archiveofourown.org/users/example/pseuds/example",
  "is_anonymous": false
}
```


Anonymous example:

```plain text
by Anonymous
```


Extract:

```json
{
  "author_name": "Anonymous",
  "author_url": null,
  "is_anonymous": true
}
```


The extractor should also use work blurb classes, where available, as supporting evidence for anonymity.

---

## 9.5 Gift recipient extraction

Some blurbs contain gift recipient information such as:

```plain text
for recipient
```


If present, extract:

```json
{
  "gift_recipient": "recipient",
  "gift_recipient_url": "https://archiveofourown.org/gifts?recipient=recipient"
}
```


If absent:

```json
{
  "gift_recipient": null,
  "gift_recipient_url": null
}
```


---

## 9.6 Fandom extraction

Fandoms appear under the title/author line.

Extract:

```json
{
  "fandoms": ["Original Work"],
  "fandom_urls": ["https://archiveofourown.org/tags/Original%20Work/works"]
}
```


Do not assume all fandoms are exactly `Original Work`. Capture the displayed fandoms as-is for later QC.

---

## 9.7 Required tags

The AO3 required-tags block provides:

- rating;
- archive warnings;
- categories;
- completion status.

Values should be taken from `title` attributes or visible text.

The extractor must handle multiple values in a single required tag, for example:

```plain text
Graphic Depictions Of Violence, Rape/Non-Con
```


as:

```json
["Graphic Depictions Of Violence", "Rape/Non-Con"]
```


Categories must also support multiple values:

```json
["F/F", "F/M", "Multi"]
```


`No category` should be captured as a real value:

```json
["No category"]
```


---

## 9.8 Updated date

The displayed date appears in the blurb as text such as:

```plain text
13 Oct 2026
```


Extract:

```json
{
  "date_updated": "2026-10-13",
  "date_updated_raw": "13 Oct 2026",
  "collection_year": 2026
}
```


If parsing fails:

```json
{
  "date_updated": null,
  "date_updated_raw": "unparsed value",
  "collection_year": 2026
}
```


and log a warning.

---

## 9.9 Main tag lists

The extractor should capture tag groups from the main tags list:

| HTML class      | Output field        |
|-----------------|---------------------|
| `warnings`      | `warning_tags`      |
| `relationships` | `relationship_tags` |
| `characters`    | `character_tags`    |
| `freeforms`     | `freeform_tags`     |

Each tag should be captured as text, and tag URLs should be captured in `tag_urls`.

---

## 9.10 Summary extraction

If a summary is present:

- `summary_text` should contain normalised plain text;
- `summary_html` should preserve the inner HTML of the summary block where possible.

If summary is absent:

```json
{
  "summary_text": null,
  "summary_html": null
}
```


The extractor must handle summaries with:

- paragraphs;
- line breaks;
- emphasis;
- strong text;
- block-level elements;
- embedded HTML;
- missing summary blocks.

---

## 9.11 Series extraction

Series information may appear after the summary.

The extractor must support:

- no series;
- one series;
- multiple series.

Example output:

```json
[
  {
    "part": 13,
    "title": "Kinktober '26",
    "url": "https://archiveofourown.org/series/6664996"
  },
  {
    "part": 9,
    "title": "The Boss' Toybox",
    "url": "https://archiveofourown.org/series/6694736"
  }
]
```


If no series is present:

```json
[]
```


---

## 9.12 Stats extraction

Stats appear in a definition list.

The extractor should parse:

- language;
- words;
- chapters;
- collections;
- comments;
- kudos;
- bookmarks;
- hits.

Example:

```json
{
  "language": "English",
  "language_code": "en",
  "words": 14690,
  "chapters_current": 3,
  "chapters_total": 3,
  "collections": 1,
  "comments": 5,
  "kudos": 37,
  "bookmarks": 18,
  "hits": 5194
}
```


### Omitted stats

AO3 often omits zero-value stats.

Use the following defaults when fields are absent:

```json
{
  "collections": 0,
  "comments": 0,
  "kudos": 0,
  "bookmarks": 0
}
```


`hits` is usually present, including zero. If hits cannot be found or parsed, use:

```json
"hits": null
```


---

## 9.13 Chapter URL extraction

If the current chapter number is linked, capture the link as:

```plain text
latest_chapter_url
```


Example:

```json
{
  "chapters_current": 3,
  "chapters_total": null,
  "latest_chapter_url": "https://archiveofourown.org/works/85198816/chapters/252475531"
}
```


If no chapter link is present:

```json
"latest_chapter_url": null
```


---

## 10. Output Format Specifications

## 10.1 NDJSON

The NDJSON output is canonical.

Each line must be a complete JSON object representing one extracted work occurrence.

Example:

```json
{"work_id":76796521,"title":"Gym Teacher","work_url":"https://archiveofourown.org/works/76796521","full_work_url":"https://archiveofourown.org/works/76796521?view_adult=true&view_full_work=true","author_name":"WoodyTales6366","author_url":"https://archiveofourown.org/users/WoodyTales6366/pseuds/WoodyTales6366","is_anonymous":false,"date_updated":"2025-12-31","date_updated_raw":"31 Dec 2025","collection_year":2025,"source_page_id":"2025_0005","source_list_page":5,"extraction_run_id":"20261013T101530Z"}
```


Use UTF-8 encoding.

Use `ensure_ascii=False` when writing JSON.

---

## 10.2 TSV

The TSV output must:

- use tab as delimiter;
- use UTF-8 encoding;
- include a header row;
- follow the exact field order;
- serialise list/object fields as compact JSON strings;
- represent `null` values as empty cells.

Example list field cell:

```json
["Original Work"]
```


---

## 10.3 XLSX

The XLSX output must:

- include one worksheet, preferably named `ao3_works_metadata`;
- include a header row;
- follow the exact field order;
- serialise list/object fields as compact JSON strings;
- represent `null` values as empty cells;
- freeze the header row if convenient;
- optionally enable filters if supported by the chosen library.

---

## 11. Extraction Manifest Design

The extraction manifest must use this general structure:

```json
{
  "run_metadata": {
    "run_id": "20261013T101530Z",
    "tool_name": "extract_ao3_works_metadata.py",
    "tool_version": "v1",
    "start_time": "2026-10-13T10:15:30Z",
    "end_time": "2026-10-13T10:18:42Z",
    "input_manifest": "corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json",
    "capture_run_id": "20261013T075915Z",
    "output_dir": "corpus/00_sources/ao3_works_metadata",
    "outputs": {
      "ndjson": "corpus/00_sources/ao3_works_metadata/ao3_works_metadata.ndjson",
      "tsv": "corpus/00_sources/ao3_works_metadata/ao3_works_metadata.tsv",
      "xlsx": "corpus/00_sources/ao3_works_metadata/ao3_works_metadata.xlsx"
    },
    "log_file": "corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata.log",
    "manifest_file": "corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata_manifest.json",
    "config": {
      "formats": ["ndjson", "tsv", "xlsx"],
      "overwrite": true,
      "strict": false,
      "start_page_id": null,
      "end_page_id": null,
      "limit_pages": null
    },
    "summary": {
      "pages_in_input_manifest": 1845,
      "successful_pages_in_input_manifest": 1845,
      "pages_selected_for_extraction": 1845,
      "pages_parsed": 1845,
      "pages_failed": 0,
      "works_extracted": 36900,
      "unique_work_ids": 36895,
      "duplicate_work_ids": 5,
      "work_parse_warnings": 0
    }
  },
  "pages": [
    {
      "page_id": "2026_0001",
      "source_html_path": "corpus/01_ao3_list_pages/2026/2026_0001.html",
      "status": "success",
      "works_extracted": 20,
      "error": null,
      "warnings": []
    }
  ],
  "duplicates": [
    {
      "work_id": 76796521,
      "occurrences": 2,
      "source_page_ids": ["2025_0005", "2025_0006"]
    }
  ]
}
```


---

## 12. Logging Specification

The programme must write an append-only log.

Default path:

```plain text
corpus/00_sources/ao3_works_metadata/extract_ao3_works_metadata.log
```


### Log format

```plain text
[YYYY-MM-DD HH:MM:SS] LEVEL  message
```


Example:

```plain text
[2026-10-13 10:15:30] INFO  Starting extract_ao3_works_metadata.py run_id=20261013T101530Z
```


### Required log events

The programme must log:

- startup;
- run ID;
- input manifest path;
- capture run ID if available;
- output directory;
- requested output formats;
- overwrite setting;
- strict mode setting;
- number of pages in manifest;
- number of successful pages selected;
- start/end page filters if used;
- page limit if used;
- each page parse start;
- each page parse success;
- each page parse failure;
- malformed work warnings;
- unparseable dates;
- missing HTML files;
- duplicate work summary;
- output file paths;
- extraction manifest paths;
- final summary;
- configuration errors;
- keyboard interruptions.

---

## 13. Error Handling and Resiliency

## 13.1 Configuration errors

Configuration errors should stop the programme before extraction begins.

Examples:

- missing input manifest;
- invalid manifest JSON;
- no successful pages;
- invalid output format;
- output file exists without `--overwrite`;
- missing XLSX dependency when XLSX output is requested.

Exit code:

```plain text
2
```


---

## 13.2 Page-level errors

Page-level errors should be recoverable unless `--strict` is enabled.

Examples:

- source HTML file missing;
- source HTML file unreadable;
- page contains no `li.work` items;
- Beautiful Soup parsing error.

Non-strict behaviour:

- mark page as failed;
- log error;
- continue to next page;
- exit `1` at end if any page failed.

Strict behaviour:

- stop extraction;
- write partial manifest if possible;
- exit `1`.

---

## 13.3 Work-level errors

If an individual work blurb is malformed:

- extract partial metadata if `work_id` or title can be recovered;
- set unparseable fields to `null` or empty defaults;
- log a warning;
- increment `work_parse_warnings`;
- continue processing.

If no meaningful work identifier or title can be recovered:

- skip that work blurb;
- log a warning;
- include the warning in page-level manifest details.

---

## 13.4 Keyboard interruption

If interrupted with `Ctrl+C`, the programme should:

- stop processing;
- write outputs collected so far if safe and useful;
- write a partial extraction manifest;
- mark the run as interrupted;
- log the interruption;
- exit with code `130`.

---

## 13.5 Exit codes

| Exit code | Meaning                                                                     |
|----------:|-----------------------------------------------------------------------------|
|       `0` | Completed successfully with no page-level failures                          |
|       `1` | Completed with one or more extraction failures or strict-mode parse failure |
|       `2` | Configuration or validation error                                           |
|     `130` | Interrupted by user                                                         |

---

## 14. Suggested Constants

The implementation should define constants near the top of the file:

```python
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

EXIT_SUCCESS = 0
EXIT_EXTRACTION_FAILURE = 1
EXIT_CONFIGURATION_ERROR = 2
EXIT_INTERRUPTED = 130
```


---

## 15. Docstrings and In-code Documentation

The implementation must include clear docstrings.

### Module-level docstring

Suggested module docstring:

```python
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
```


### Required function docstrings

At minimum, docstrings are required for:

- `parse_args`
- `setup_logging`
- `load_capture_manifest`
- `select_successful_pages`
- `parse_html_file`
- `extract_page_works`
- `extract_work_metadata`
- `absolute_ao3_url`
- `build_full_work_url`
- `parse_ao3_display_date`
- `parse_int`
- `parse_chapters`
- `write_ndjson`
- `write_tsv`
- `write_xlsx`
- `write_extraction_manifests`
- `main`

---

## 16. Development Notes

## 16.1 Initial implementation scope

The first implementation should prioritise:

- accurate offline parsing;
- robust handling of AO3 list-page edge cases;
- correct output schema;
- clean NDJSON export;
- TSV/XLSX exports with JSON-serialised list fields;
- clear provenance fields;
- extraction manifest;
- append-only logging;
- no network access.

---

## 16.2 Out of scope for v1

The following are out of scope:

- capturing AO3 pages;
- opening full work pages;
- extracting full work text;
- updating AO3 metadata from live pages;
- deduplicating exported works;
- content filtering or corpus sampling;
- removing fandom misclassified works;
- statistical analysis;
- language verification beyond capturing AO3’s displayed language;
- AI-authorship detection.

---

## 16.3 Recommended implementation approach

Recommended parser:

```plain text
Beautiful Soup
```


Recommended canonical output:

```plain text
NDJSON
```


Recommended tabular output:

```plain text
TSV
XLSX
```


Recommended XLSX writer:

```plain text
openpyxl
```


The programme should avoid using Selenium, because all input data are local saved HTML files.

---

## 17. Acceptance Criteria

The programme is considered complete when the following conditions are met:

1. Running:

```shell script
python extract_ao3_works_metadata.py
```


   reads:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


2. The programme selects only manifest pages with:

```plain text
status == "success"
```


3. The programme reads each selected page’s local HTML file from `output_path`.

4. The programme does not make network requests.

5. The programme extracts one metadata record per AO3 work blurb.

6. Work records preserve manifest page order and work order within pages.

7. The programme exports:

```plain text
ao3_works_metadata.ndjson
   ao3_works_metadata.tsv
   ao3_works_metadata.xlsx
```


8. The output directory is:

```plain text
corpus/00_sources/ao3_works_metadata/
```


9. The NDJSON output stores list/object fields as real JSON arrays/objects.

10. The TSV output serialises list/object fields as compact JSON strings.

11. The XLSX output serialises list/object fields as compact JSON strings.

12. The output schema follows the specified field order.

13. `date_updated` is machine-readable ISO format where parsing succeeds.

14. `date_updated_raw` preserves the original AO3 date string.

15. `collection_year` is populated from the manifest page record.

16. `full_work_url` is generated from `work_url`.

17. Anonymous works are handled correctly.

18. Missing summaries are handled correctly.

19. Multiple archive warnings are handled correctly.

20. Multiple categories are handled correctly.

21. Multiple fandoms are handled correctly.

22. Multiple series memberships are handled correctly.

23. Omitted collections/comments/kudos/bookmarks are normalised to `0`.

24. `chapters_total` is `null` when AO3 shows `?`.

25. Tag URLs are preserved in `tag_urls`.

26. Page provenance fields are populated:

```plain text
source_page_id
   source_list_page
   source_list_url
   source_html_path
```


27. `extraction_run_id` is included in every record.

28. Duplicate `work_id` values are not removed.

29. Duplicate `work_id` counts are reported in the extraction manifest.

30. Missing or unreadable HTML files are logged and reported in the manifest.

31. The programme writes an append-only log file.

32. The programme writes a latest extraction manifest.

33. The programme writes a timestamped extraction manifest.

34. The programme exits with:
   - `0` if extraction succeeds without page-level failures;
   - `1` if extraction completes with page-level failures;
   - `2` for configuration errors;
   - `130` for keyboard interruption.

---

## 18. Short Pipeline Documentation Section

The following section can be added to the project pipeline documentation.

### 1.2. Works Metadata Extraction from AO3 List Pages

After list pages have been captured, extract work-level metadata from the saved AO3 list-page HTML files.

Default extraction:

```shell script
python extract_ao3_works_metadata.py
```


The programme reads:

```plain text
corpus/01_ao3_list_pages/capture_ao3_lists_manifest.json
```


It processes only successfully captured pages and writes metadata outputs to:

```plain text
corpus/00_sources/ao3_works_metadata/
```


Generated files:

```plain text
ao3_works_metadata.ndjson
ao3_works_metadata.tsv
ao3_works_metadata.xlsx
extract_ao3_works_metadata_manifest.json
extract_ao3_works_metadata.log
```


To extract from a specific timestamped capture manifest:

```shell script
python extract_ao3_works_metadata.py \
  --input-manifest corpus/01_ao3_list_pages/capture_ao3_lists_manifest_20261013T075915Z.json
```


For a small test extraction:

```shell script
python extract_ao3_works_metadata.py \
  --limit-pages 10 \
  --overwrite
```


The extractor is offline and does not contact AO3. It parses the saved HTML files, extracts work-level metadata, and records source-page provenance for reproducibility.