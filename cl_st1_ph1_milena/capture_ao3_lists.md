# `capture_ao3_lists.py` programme specification

The `capture_ao3_lists.py`:

1. Captures lists of works from the Archive of Our Own (AO3) website
2. Saves the captured lists in the `corpus` directory as HTML files
3. Captures metadata for each work and save them in the `corpus` directory as a JSON file

## Input data

- Load the `ao3_original_work_lists.json` file as a dictionary of input data.

## Output data

Use or create the following structure of output directories under the `corpus` directory:

- `corpus/00_sources/00_lists/2025/`
- `corpus/00_sources/00_lists/2024/`
- and so on

## Logging

Set up logging to record the progress and errors of the programme. Use the `capture_ao3_lists.log` to write logs.

## Test mode

Implement a test mode that allows running the programme with a limited number of pages to test the functionality and performance. Consider 5 pages per year as the default parameter.

## Processing steps

1. Use Selenium to download each list page and save the page as, for instance, `2025_0001.html` in the corresponding output directory. The last four digits of the filename mean the page represented with four digits.

2. Keep the WebDriver session open for a batch of pages with a cool-down period. Implement polite throttling to avoid overloading the AO3 server and run into penalties, and error handling. Consider Firefox headless and the following location for the geckodriver: `/home/ubuntu/geckodriver/geckodriver`. Keep in mind that the programme will run on an EC2 instance running Ubuntu 24.04.3 LTS and Python 3.12.3

3. Before moving on to the next page, use Beautiful Soup with `lxml` parser to scrape the page. Please refer to [capture_ao3_lists_list_example_1.html](capture_ao3_lists_list_example_1.html)