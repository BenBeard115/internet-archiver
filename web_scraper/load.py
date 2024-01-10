"""Script used to insert the re-scraped HTML and CSS files into the S3 bucket."""

from datetime import datetime
from os import environ, getcwd, remove
from time import perf_counter
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import re

from boto3 import client
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2 import extensions, sql
from html2image import Html2Image
import requests

from extract import get_database_connection

DISPLAY_SIZE = (800, 600)
IMAGE_FILE_FORMAT = ".png"
HTML_FILE_FORMAT = ".html"
CSS_FILE_FORMAT = ".css"
IS_HUMAN = False


def get_soup(current_url: str) -> BeautifulSoup:
    """Gets Soup object from url."""

    response = requests.get(current_url, timeout=30)
    response.raise_for_status()

    return BeautifulSoup(response.content, 'html.parser')


def sanitise_filename(filename: str) -> str:
    """Remove special characters from filename."""

    try:
        filename = str(filename)
    except TypeError as exc:
        raise TypeError("This input cannot be sanitised!") from exc

    return re.sub(r'[^\w\s.-]', ' ', filename)


def extract_title(current_url: str) -> str:
    """Extracts title used for s3_filename from given url."""

    try:
        req = Request(current_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as page:
            current_soup = BeautifulSoup(page, 'html.parser')
            current_title = current_soup.title.text.strip()
    except (URLError, HTTPError):
        return None

    return sanitise_filename(current_title)


def extract_domain(current_url: str) -> str:
    """Extracts domain name used for s3_filename from given url."""

    regex_pattern = r'^(https?:\/\/)?((?:www\.)?)([^\/]+)'

    match = re.search(regex_pattern, current_url)
    if not match:
        return None

    return match.group(2) + match.group(3)


def process_html_content(current_soup: BeautifulSoup,
                        current_domain: str,
                        current_title: str,
                        current_timestamp: str,
                        s3_client: client) -> str:
    """Uploads the html content as a file to the S3 bucket, given a specific url soup."""

    filename_string = f"{current_domain}/{current_title}/{current_timestamp}"
    html_object_key = f"{filename_string}{HTML_FILE_FORMAT}"

    html_content = current_soup.prettify()

    s3_client.put_object(
        Body=html_content, Bucket=environ["S3_BUCKET"], Key=html_object_key)

    return html_object_key


def process_css_content(current_soup: BeautifulSoup,
                        current_domain: str,
                        current_title: str,
                        current_timestamp: str,
                        s3_client: client) -> str:
    """Uploads the css content as a file to the S3 bucket, given a specific url soup."""

    filename_string = f"{current_domain}/{current_title}/{current_timestamp}"
    css_object_key = f"{filename_string}{CSS_FILE_FORMAT}"

    css_content = current_soup.prettify()

    s3_client.put_object(
        Body=css_content, Bucket=environ["S3_BUCKET"], Key=css_object_key)

    return css_object_key


def process_screenshot(current_url: str,
                       current_domain: str,
                       current_title: str,
                       current_timestamp: str,
                       s3_client: client,
                       hti: Html2Image) -> str:
    """Takes screenshot of webpage and uploads to S3."""

    img_filename_string = f"{current_domain}_{current_title}_{current_timestamp}"
    img_object_key = f"{img_filename_string}{IMAGE_FILE_FORMAT}"

    filename_string = f"{current_domain}/{current_title}/{current_timestamp}"
    img_object_key_s3 = f"{filename_string}{IMAGE_FILE_FORMAT}"

    hti.screenshot(url=current_url,
                   size=DISPLAY_SIZE,
                   save_as=img_object_key)

    upload_file_to_s3(s3_client, img_object_key, environ["S3_BUCKET"], img_object_key_s3)

    remove(img_object_key)

    return img_object_key_s3


def upload_file_to_s3(s3_client: client, filename: str, bucket: str, key: str) -> None:
    """Uploads a file to the specified S3 bucket."""

    try:
        s3_client.upload_file(filename, bucket, key)

    except ClientError:
        print("Unable to upload file. Please check details of client!")
    except TypeError:
        print("Unable to upload file. Missing parameters required for upload!")


def add_website(conn: extensions.connection, current_response_data: dict, current_url: str) -> None:
    """Adds a website's data to the database."""

    with conn.cursor() as cur:
        cur.execute(f"""
                    SELECT {environ["SCRAPE_TABLE_NAME"]}.url_id FROM {environ["SCRAPE_TABLE_NAME"]}
                    JOIN url ON {environ["URL_TABLE_NAME"]}.url_id = {environ["SCRAPE_TABLE_NAME"]}.url_id
                    WHERE url LIKE '%{current_url}%'
                    """)

        try:
            current_response_data["url_id"] = cur.fetchall()[0][0]
        except IndexError:
            return

    query = sql.SQL("""
                    INSERT INTO {table} 
                        ({fields})
                    VALUES
                        ({values});""").format(
        table=sql.Identifier('page_scrape'),
        fields=sql.SQL(',').join([
            sql.Identifier('url_id'),
            sql.Identifier('scrape_at'),
            sql.Identifier('html_s3_ref'),
            sql.Identifier('css_s3_ref'),
            sql.Identifier('screenshot_s3_ref'),
            sql.Identifier('is_human')
        ]),
        values=sql.SQL(',').join([
            sql.Literal(current_response_data["url_id"]),
            sql.Literal(current_response_data["scrape_at"]),
            sql.Literal(current_response_data["html_s3_ref"]),
            sql.Literal(current_response_data["css_s3_ref"]),
            sql.Literal(current_response_data["screenshot_s3_ref"]),
            sql.Literal(current_response_data["is_human"])
        ])
    )

    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()


if __name__ == "__main__":

    load_dotenv()
    connection = get_database_connection()

    hti = Html2Image(custom_flags=["--no-sandbox",
                               "--no-first-run", "--disable-gpu", "--use-fake-ui-for-media-stream",
                               "--use-fake-device-for-media-stream", "--disable-sync"])

    startup = perf_counter()
    print("Connecting to S3...")
    client = client('s3',
                       aws_access_key_id=environ["AWS_ACCESS_KEY_ID"],
                       aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY"])
    print(f"Connected to S3 --- {perf_counter() - startup}s.")

    list_of_urls = ["https://eveninguniverse.com/fiction/the-meteor-generation.html",
                    "https://www.youtube.co.uk", "https://www.youtube.co.uk/"]

    download = perf_counter()
    print("Uploading HTML and image data to S3...")
    for url in list_of_urls:

        soup = get_soup(url)
        title = extract_title(url)
        domain = extract_domain(url)
        timestamp = datetime.utcnow().isoformat()
        html_file_name = process_html_content(soup, domain, title, timestamp, client)
        img_file_name = process_screenshot(url, domain, title, timestamp, client, hti)
        css_file_name = process_css_content(soup, domain, title, timestamp, client)

        response_data = {"scrape_at": timestamp, "html_s3_ref": html_file_name,
                        "css_s3_ref": css_file_name, "screenshot_s3_ref": img_file_name,
                        "is_human": IS_HUMAN}

        if html_file_name and img_file_name and css_file_name:
            add_website(connection, response_data, url)

    print(f"Data uploaded --- {perf_counter() - download}s.")
