"""Script that web scrapes the non-duplicate URLs contained in the S3 bucket."""

from time import perf_counter
from os import environ
from datetime import datetime

from dotenv import load_dotenv
from boto3 import client
from html2image import Html2Image

from extract import get_database_connection, load_all_data
from load import (add_website, get_soup, extract_title,
                  extract_domain, process_html_content,
                  process_screenshot, process_css_content)

IS_HUMAN = False


if __name__ == "__main__":
    hti = Html2Image(custom_flags=["--no-sandbox",
                                "--no-first-run", "--disable-gpu", "--use-fake-ui-for-media-stream",
                                "--use-fake-device-for-media-stream", "--disable-sync"])
    load_dotenv()

    startup = perf_counter()
    print("Loading data...")
    connection = get_database_connection()
    list_of_urls = load_all_data(connection)
    print(f"Data loaded --- {perf_counter() - startup}s.")


    connecting_time = perf_counter()
    print("Connecting to S3...")
    client = client('s3',
                       aws_access_key_id=environ["AWS_ACCESS_KEY_ID"],
                       aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY"])
    print(f"Connected to S3 --- {perf_counter() - connecting_time}s.")

    download = perf_counter()
    print("Uploading HTML and image data to S3...")
    for url in list_of_urls:

        soup = get_soup(url)
        title = extract_title(url)
        domain = extract_domain(url)
        timestamp = datetime.utcnow().isoformat()
        print(title)

        html_file_name = process_html_content(soup, domain, title, timestamp, client)
        img_file_name = process_screenshot(url, domain, title, timestamp, client, hti)
        css_file_name = process_css_content(soup, domain, title, timestamp, client)

        response_data = {"scrape_at": timestamp, "html_s3_ref": html_file_name,
                        "css_s3_ref": css_file_name, "screenshot_s3_ref": img_file_name,
                        "is_human": IS_HUMAN}

        if html_file_name and img_file_name and css_file_name:
            add_website(connection, response_data, url)

    connection.close()

    print(f"Data uploaded --- {perf_counter() - download}s.")
    print(f"Pipeline complete --- {perf_counter() - startup}s.")
