# Usage
# python getwebpage.py ed_article https://www.theguardian.com/technology/2025/mar/31/bridget-phillipson-eyes-ais-potential-to-free-up-teachers-time

import argparse
import requests
import validators
from bs4 import BeautifulSoup

def main(file_id, url):
    """Fetch a web page, save it as an HTML file, and extract 'h' and 'p' tags' text to a separate file."""
    # Validate URL
    if not validators.url(url):
        print("Invalid URL. Please provide a valid URL.")
        return

    http = requests.Session()
    # Obtain the 'User-Agent' at 'https://httpbin.org/headers'
    # Setting up the 'User-Agent' may not prevent websites from restricting automated access and returning a 403 Forbidden error
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0'}
    try:
        # Fetch the web page with a timeout
        response = http.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Save the HTML content to a file
        html_file_path = f"{file_id}.html"
        with open(html_file_path, 'w', encoding='utf-8') as html_file:
            html_file.write(response.text)
        print(f"Successfully saved HTML to {html_file_path}")

        # Extract text from 'h' and 'p' tags
        soup = BeautifulSoup(response.text, 'lxml')
        text_content = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            text_content.append(tag.get_text(strip=True))

        # Save the extracted text to a file
        text_file_path = f"{file_id}.txt"
        with open(text_file_path, 'w', encoding='utf-8') as text_file:
            text_file.write("\n".join(text_content))
        print(f"Successfully saved extracted text to {text_file_path}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch the URL: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get a web page, save its HTML, and extract 'h' and 'p' tags' text.")
    parser.add_argument('file_id', type=str, help="Web page's filename (without extension)")
    parser.add_argument('url', type=str, help="Web page's URL")
    args = parser.parse_args()
    main(args.file_id, args.url)
