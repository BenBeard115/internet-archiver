"""Script used to insert the re-scraped HTML and CSS files into the S3 bucket."""

from datetime import datetime
from os import environ, path, getcwd, mkdir
from time import perf_counter
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import re
import shutil

from boto3 import client
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2 import extensions

import requests


def sanitise_filename(filename: str) -> str:
    """Remove special characters from filename."""

    try:
        filename = str(filename)
    except TypeError:
        raise TypeError("This input cannot be sanitised!")

    return re.sub(r'[^\w\s.-]', ' ', filename)


def extract_title(current_url: str) -> str:
    """Extracts title used for s3_filename from given url."""

    try:
        req = Request(current_url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        soup = BeautifulSoup(page, 'html.parser')
        title = soup.title.text.strip()
    except (URLError, HTTPError):
        return None

    return sanitise_filename(title)


def extract_domain(current_url: str) -> str:
    """Extracts domain name used for s3_filename from given url."""

    regex_pattern = r'(http[s]?:\/\/)?[^\s(["<,>]*\.[\w]+[^\s.[",><]*'

    match = re.match(regex_pattern, current_url)
    if not match:
        return None

    domain = match.group(0).replace("https://", "").replace("http://", "")

    while "/" in domain:
        domain = domain.replace("/", " ")

    return domain


def upload_file_to_s3(s3_client: client, filename: str, bucket: str, key: str) -> None:
    """Uploads a file to the specified S3 bucket."""

    try:
        s3_client.upload_file(filename, bucket, key)

    except ClientError:
        print("Unable to upload file. Please check details of client!")
    except TypeError:
        print("Unable to upload file. Missing parameters required for upload!")


def upload_to_rds(conn: extensions.connection, current_url: str) -> None:
    """Uploads HTML and CSS to the RDS."""

    title = extract_title(current_url)

    if title:
        url_domain = extract_domain(current_url)
        timestamp = datetime.utcnow().isoformat()

        s3_object_key_matcher = f"{url_domain}/{title}"

        s3_object_key_html = f"{url_domain}/{title}/{timestamp}.html"
        s3_object_key_css = f"{url_domain}/{title}/{timestamp}.css"

        with conn.cursor() as cur:
            cur.execute(f"""
                        SELECT url_id FROM {environ["SCRAPE_TABLE_NAME"]}
                        WHERE html LIKE '%{s3_object_key_matcher}%' AND css LIKE '%{s3_object_key_matcher}%'
                        """)
            
            try:
                url_id = cur.fetchall()[0][0]
            except IndexError:
                return

            cur.execute(f"""
                        INSERT INTO {environ["SCRAPE_TABLE_NAME"]}
                        (url_id, at, html, css) VALUES
                        ('{url_id}', '{timestamp}', '{s3_object_key_html}', '{s3_object_key_css}')
                        """)
            conn.commit()


def upload_to_s3(s3_client: client, current_url: str, html_filename_temp: str,
                css_filename_temp: str) -> None:
    """Uploads HTML and CSS to S3 bucket."""

    title = extract_title(current_url)
    url_domain = extract_domain(current_url)

    if title and url_domain:
        timestamp = datetime.utcnow().isoformat()

        html_file_to_upload = f"static/{html_filename_temp}"
        css_file_to_upload = f"static/{css_filename_temp}"

        s3_object_key_html = f"{url_domain}/{title}/{timestamp}.html"
        s3_object_key_css = f"{url_domain}/{title}/{timestamp}.css"

        upload_file_to_s3(s3_client, html_file_to_upload,
                        environ["S3_BUCKET"], s3_object_key_html)
        upload_file_to_s3(s3_client, css_file_to_upload,
                        environ["S3_BUCKET"], s3_object_key_css)


def save_html_css(current_url: str) -> str:
    """Scrape HTML and CSS from a given URL and save them."""

    if not path.exists('static'):
        mkdir('static')

    headers = requests.utils.default_headers()
    headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",})
    response = requests.get(current_url, headers=headers, timeout=30)

    soup = BeautifulSoup(response.content, "html.parser")
    title = sanitise_filename(soup.title.text.strip())
    html_content = str(soup)
    css_content = "\n".join([style.text for style in soup.find_all("style")])
    html_filename_temp = f"{title}_html.html"
    css_filename_temp = f"{title}_css.css"

    static_folder = path.join(getcwd(), "static")

    with open(path.join(static_folder, html_filename_temp), "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    with open(path.join(static_folder, css_filename_temp), "w", encoding="utf-8") as css_file:
        css_file.write(css_content)

    return html_filename_temp, css_filename_temp


if __name__ == "__main__":

    load_dotenv()

    startup = perf_counter()
    print("Connecting to S3...")
    client = client('s3',
                       aws_access_key_id=environ["AWS_ACCESS_KEY_ID"],
                       aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY"])
    print(f"Connected to S3 --- {startup - perf_counter()}s.")

    list_of_urls = ["https://www.youtube.co.uk", "https://www.google.co.uk"]

    download = perf_counter()
    print("Uploading HTML and CSS data to S3...")
    for url in list_of_urls:

        html_file_name, css_file_name = save_html_css(url)
        upload_to_s3(client, url,
                     html_file_name, css_file_name)

    shutil.rmtree("static/")

    print(f"Data uploaded --- {download - perf_counter()}s.")
