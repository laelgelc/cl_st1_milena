# Corpus Linguistics - Study 1 - Milena

## Phase 0 - Data Collection Testing
This project involves ethically collecting data from [Archive of Our Own](https://archiveofourown.org/) (AO3). In this preliminary phase, the goals are:

1. Check the best method to scrape AO3's web pages
2. Define the process for scraping the works in English tagged as `Original Work`

### Method to scrape AO3's web pages
AO3 is primarily a static-rendered site, but it behaves like a dynamic one for bots:

```
(my_env) eyamrog@eyamrog-iMac:~/PycharmProjects/cl_st1_milena/cl_st1_ph0_milena$ python getwebpage.py archiveofourown https://archiveofourown.org/tags/Original%20Work/works?page=1
Failed to fetch the URL: 525 Server Error: <none> for url: https://archiveofourown.org/tags/Original%20Work/works?page=1
(my_env) eyamrog@eyamrog-iMac:~/PycharmProjects/cl_st1_milena/cl_st1_ph0_milena$ 
```

Therefore, the recommended method is to use Selenium because it emulates a human-controlled browser.

### Scraping the works in English tagged as `Original Work`

The list of works in English tagged as `Original Work` is:

- https://archiveofourown.org/tags/Original%20Work/works

Applying the filter `Language:English` yields the following list:

- https://archiveofourown.org/works?work_search%5Bsort_column%5D=revised_at&work_search%5Bother_tag_names%5D=&work_search%5Bexcluded_tag_names%5D=&work_search%5Bcrossover%5D=&work_search%5Bcomplete%5D=&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=&work_search%5Bdate_to%5D=&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Original+Work

This list's maximum length is 5,000 pages long, and each page contains 20 works. Therefore, the list contains 100,000 works. This is a portion of the total number of works, which was 335,768 works in 15/01/2026, at the time of writing this document.

- From: https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=&work_search[date_to]=&work_search[query]=&work_search[language_id]=en&commit=Sort+and+Filter&tag_id=Original+Work&page=1
- To: https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=&work_search[date_to]=&work_search[query]=&work_search[language_id]=en&commit=Sort+and+Filter&tag_id=Original+Work&page=5000

Each of the list pages can be captured using Selenium. For instance, the first page can be captured as follows:

```
(my_env) eyamrog@eyamrog-iMac:~/PycharmProjects/cl_st1_milena/cl_st1_ph0_milena$ python getwebpageselenium.py ao3_index_1 "https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=&work_search[date_to]=&work_search[query]=&work_search[language_id]=en&commit=Sort+and+Filter&tag_id=Original+Work&page=1"
Successfully saved HTML to ao3_index_1.html
Successfully saved extracted text to ao3_index_1.txt
(my_env) eyamrog@eyamrog-iMac:~/PycharmProjects/cl_st1_milena/cl_st1_ph0_milena$ 
```

Click [captured first list page](cl_st1_ph0_milena/ao3_index_1.html) to see it. 

Each work's URL can be captured from the corresponding page's HTML code. For instance, for the work [Pan's Shenaniganery](https://archiveofourown.org/works/76671106?view_full_work=true), the full URL can be composed as follows:

- From the title's `href` attribute: /works/76671106
- The full URL: https://archiveofourown.org/works/76671106
- The full URL to the entire work's page: https://archiveofourown.org/works/76671106?view_full_work=true

Using the full URL, the entire work's page can be captured using Selenium:

```
(my_env) eyamrog@eyamrog-iMac:~/PycharmProjects/cl_st1_milena/cl_st1_ph0_milena$ python getwebpageselenium.py ao3_work_1 "https://archiveofourown.org/works/76671106?view_full_work=true"
Successfully saved HTML to ao3_work_1.html
Successfully saved extracted text to ao3_work_1.txt
(my_env) eyamrog@eyamrog-iMac:~/PycharmProjects/cl_st1_milena/cl_st1_ph0_milena$ 
```

Finally, the full text of the work can be scraped from the HTML code using Beautiful Soup:

Click [raw text](cl_st1_ph0_milena/ao3_work_1.txt) to see it.

Notes:

- Each web page capture takes about 3 seconds
- Capturing the 5,000 list pages will take about 4.17 hours
- Capturing the 100,000 works will take about 3.47 days.

#### "Adult Content" warning page

[The Therapist](https://archiveofourown.org/works/73631631)

This work could have adult content. If you continue, you have agreed that you are willing to see such content.
- Yes, Continue
- No, Go Back

## Phase 1 - Data Collection

AO3's website encodes the entire filter as `URL Query Parameters` which makes the list pages reproducible. It means that parameters can be set directly in the URL to change the filtering.

For instance, the following URL:

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2024-01-01&work_search[date_to]=2024-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1
```

has the following parameters:

- work_search[date_from]=2024-01-01: start date (`Date Updated`)
- work_search[date_to]=2024-12-31: end date (`Date Updated`)
- work_search[language_id]=en: English language filter
- include_work_search[fandom_ids][]=2692: Internal ID (2692) for `Original Work` fandom category.
- page=1: Pagination handle, used to loop through results programmatically.

This study focuses on Original Works in English. The data collection strategy is as follows:

1. Capture the list of works in English tagged as `Original Work` corresponding to years from 2020 to 2025 (`Date Updated`) as HTML files. E.g. `2024_0001.html` with the content of the first page of the 2024 list.
2. Extract the works' URLs from the HTML files.
3. Randomly select 1,000 works from each year.
4. Capture the full text of the selected works as HTML files.

If the study is extended to consider AI, works dated (`Date Updated`) before the advent of ChatGPT on 30th November 2022 can be considered as human-authored works.

### List URL ranges

Year: 2025

90,476 Works in Original Work

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2025-01-01&work_search[date_to]=2025-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1

https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2025-01-01&work_search[date_to]=2025-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=4524
```

Year: 2024

60,360 Works in Original Work

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2024-01-01&work_search[date_to]=2024-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1

https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2024-01-01&work_search[date_to]=2024-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=3018
```

Year: 2023

47,949 Works in Original Work

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2023-01-01&work_search[date_to]=2023-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1

https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2023-01-01&work_search[date_to]=2023-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=2398
```

Year: 2022

36,182 Works in Original Work

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2022-01-01&work_search[date_to]=2022-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1

https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2022-01-01&work_search[date_to]=2022-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1810
```

Year: 2021

27,972 Works in Original Work

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2021-01-01&work_search[date_to]=2021-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1

https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2021-01-01&work_search[date_to]=2021-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1399
```

Year: 2020

20,178 Works in Original Work

```
https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2020-01-01&work_search[date_to]=2020-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1

https://archiveofourown.org/works?work_search[sort_column]=revised_at&work_search[other_tag_names]=&work_search[excluded_tag_names]=&work_search[crossover]=&work_search[complete]=&work_search[words_from]=&work_search[words_to]=&work_search[date_from]=2020-01-01&work_search[date_to]=2020-12-31&work_search[query]=&work_search[language_id]=en&include_work_search[fandom_ids][]=2692&commit=Sort+and+Filter&tag_id=Original+Work&page=1009
```
