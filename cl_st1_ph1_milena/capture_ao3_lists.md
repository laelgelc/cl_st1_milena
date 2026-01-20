# `capture_ao3_lists.py` programme specification

The `capture_ao3_lists.py` programme performs the following tasks:

1. Captures lists of works from the Archive of Our Own (AO3) website
2. Saves the captured lists in the `corpus` directory as HTML files
3. Captures metadata for each work and save them in the `corpus` directory as a JSONL and an Excel file

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

## "Consent to AO3 Terms"

The attempt to access some works may result in a "Consent to AO3 Terms" page. Please refer to [ao3_work_3_consent.html](cl_st1_ph0_milena/ao3_work_3_consent.html) for an example.

On the Archive of Our Own (AO3), users can create works, bookmarks, comments, tags, and other Content. Any information you publish on AO3 may be accessible by the public, AO3 users, and/or AO3 personnel. Be mindful when sharing personal information, including but not limited to your name, email, age, location, personal relationships, gender or sexual identity, racial or ethnic background, religious or political views, and/or account usernames for other sites.

To learn more, check out our Terms of Service, including the Content Policy and Privacy Policy.

 I have read & understood the 2024 Terms of Service, including the Content Policy and Privacy Policy.

 By checking this box, you consent to the processing of your personal data in the United States and other jurisdictions in connection with our provision of AO3 and its related services to you. You acknowledge that the data privacy laws of such jurisdictions may differ from those provided in your jurisdiction. For more information about how your personal data will be processed, please refer to our Privacy Policy.

I agree/consent to these Terms

The two checkboxes must be checked and the `I agree/consent to these Terms` button must be clicked.

## Processing steps

1. Use Selenium to download each list page and save the page as, for instance, `2025_0001.html` in the corresponding output directory. The last four digits of the filename mean the page represented with four digits. Please consider ["Consent to AO3 Terms"](#"consent-to-ao3-terms")

2. Keep the WebDriver session open for a batch of pages with a cool-down period. Implement polite throttling to avoid overloading the AO3 server and run into penalties, and error handling. Consider Firefox headless and the following location for the geckodriver: `/home/ubuntu/geckodriver/geckodriver`. Keep in mind that the programme will run on an EC2 instance running Ubuntu 24.04.3 LTS and Python 3.12.3

3. Before moving on to the next page, use Beautiful Soup with `lxml` parser to scrape the page. Please refer to [capture_ao3_lists_list_example_1.html](capture_ao3_lists_list_example_1.html) and:

- Find `<ol class="work index group">`
- Find all `<li>` tags inside the `<ol>` tag
- For each `<li>` tag, extract the following elements (please refer to `<li id="work_76796521" class="work blurb group work-76796521 user-29195771" role="article">` in the example) and keep in mind that not all elements may be present in each `<li>` tag
  - Year (predefined as the year of the `Date_Updated` element)
  - Title: From `<a href="/works/76796521">Gym Teacher</a`
  - Author: From `<a rel="author" href="/users/WoodyTales6366/pseuds/WoodyTales6366">WoodyTales6366</a>`
  - Fandom: From `<a class="tag" href="/tags/Original%20Work/works">Original Work</a>`
  - Date_Updated: From `<p class="datetime">31 Dec 2025</p>`
  - Language: From `<dd class="language" lang="en">English</dd>`
  - Words: From `<dd class="words">14,690</dd>`
  - Chapters: From `<dd class="chapters"><a href="/works/76796521/chapters/201015281">3</a>/3</dd>`
  - Collections: From `<dd class="collections"><a href="/works/76796521/collections">1</a></dd>`
  - Comments: From `<dd class="comments"><a href="/works/76796521?show_comments=true&amp;view_full_work=true#comments">5</a></dd>`
  - Kudos: From `<dd class="kudos"><a href="/works/76796521?view_full_work=true#kudos">37</a></dd>`
  - Bookmarks: From `<dd class="bookmarks"><a href="/works/76796521/bookmarks">18</a></dd>`
  - Hits: From `<dd class="hits">5,194</dd>`
  - URL: From `<a href="/works/76796521">Gym Teacher</a`. Prepend `https://archiveofourown.org` to the URL. Append `?view_adult=true&view_full_work=true` to the URL.
- Save the scraped data as a JSONL file as `corpus/00_sources/lists.jsonl` and as an Excel file as `corpus/00_sources/lists.xlsx`

