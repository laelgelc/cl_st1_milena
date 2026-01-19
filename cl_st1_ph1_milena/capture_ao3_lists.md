# `capture_ao3_lists.py` programme specification

The programme should:

1. Load the `ao3_original_work_lists.json` file as a dictionary of input data.

2. Use or create the following structure of output directories under the `corpus` directory:

- `corpus/00_sources/00_lists/2025/`
- `corpus/00_sources/00_lists/2024/`
- and so on

3. Use Selenium to download each list page and save the page as, for instance, `2025_0001.html` in the corresponding directory. The last four digits of the filename mean the page represented with four digits.
4. Start and close the WebDriver in each iteration. Consider Firefox headless and the following location for the geckodriver: `/home/ubuntu/geckodriver/geckodriver`.
5. Before moving on to the next page, use Beautiful Soup with `lxml` parser 