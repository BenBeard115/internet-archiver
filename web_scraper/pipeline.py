"""Script that web scrapes the non-duplicate URLs contained in the S3 bucket."""

from time import perf_counter
from os import environ
import shutil

from dotenv import load_dotenv
from boto3 import client

from extract import get_database_connection, load_all_data, scrape_all_urls
from load import save_html_css, upload_to_s3, upload_to_rds


if __name__ == "__main__":

    load_dotenv()

    startup = perf_counter()
    print("Loading data...")
    connection = get_database_connection()
    list_of_urls = load_all_data(connection)
    print(f"Data loaded --- {perf_counter() - startup}s.")

    scraper = perf_counter()
    print("Scraping websites...")
    scrape_all_urls(list_of_urls)
    print(f"Websites scraped --- {perf_counter() - scraper}s.")

    connecting_time = perf_counter()
    print("Connecting to S3...")
    s3_client = client("s3",
                       aws_access_key_id=environ["AWS_ACCESS_KEY_ID"],
                       aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY"])
    print(f"Connected to S3 --- {perf_counter() - connecting_time}s.")

    download = perf_counter()
    print("Uploading HTML and CSS data to S3 and RDS...")
    for url in list_of_urls:

        html_file_name, css_file_name = save_html_css(url)

        # to see which files are being blocked on AWS
        print(html_file_name)
        print(css_file_name)
        upload_to_s3(s3_client, url,
                     html_file_name, css_file_name)
        upload_to_rds(connection, url)

    shutil.rmtree("static/")

    print(f"Data uploaded --- {perf_counter() - download}s.")
    print(f"Pipeline complete --- {perf_counter() - startup}s.")
