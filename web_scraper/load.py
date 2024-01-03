"""Script used to insert the re-scraped HTML and CSS files into the S3 bucket."""

from datetime import datetime
from os import environ, path, getcwd
from time import perf_counter
import re
import shutil

from boto3 import client
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.request import urlopen
import requests


def sanitise_filename(filename: str) -> str:
    """Remove special characters from filename."""

    return re.sub(r'[^\w\s.-]', ' ', filename)


def extract_title(url: str) -> str:
    """Extracts title used for s3_filename from given url."""
    
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.title.text.strip()

    return sanitise_filename(title)


def extract_domain(url: str) -> str:
    """Extracts domain name used for s3_filename from given url."""

    regex_pattern = r'(www.[a-z.]*)'

    return re.search(regex_pattern, url).group(1)


def upload_file_to_s3(s3_client: client, filename: str, bucket: str, key: str) -> None:
    """Uploads a file to the specified S3 bucket."""

    try:
        s3_client.upload_file(filename, bucket, key)

    except Exception as e:
        print('Unable to upload file. Please check details!')


def upload_to_s3(s3_client: client, url: str, html_filename_temp: str, css_filename_temp: str):
    """Uploads HTML and CSS to S3 bucket."""

    title = extract_title(url)
    url_domain = extract_domain(url)
    timestamp = datetime.utcnow().isoformat()

    html_file_to_upload = f'static/{html_filename_temp}'
    css_file_to_upload = f'static/{css_filename_temp}'

    s3_object_key_html = f'{url_domain}/{title}/{timestamp}.html'
    s3_object_key_css = f'{url_domain}/{title}/{timestamp}.css'

    upload_file_to_s3(s3_client, html_file_to_upload,
                      environ['S3_BUCKET'], s3_object_key_html)
    upload_file_to_s3(s3_client, css_file_to_upload,
                      environ['S3_BUCKET'], s3_object_key_css)

    return s3_object_key_html, s3_object_key_css


def save_html_css(url: str) -> str:
    """Scrape HTML and CSS from a given URL and save them."""

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    title = sanitise_filename(soup.title.text.strip())
    html_content = str(soup)
    css_content = '\n'.join([style.text for style in soup.find_all('style')])
    html_filename_temp = f"{title}_html.html"
    css_filename_temp = f"{title}_css.css"

    static_folder = path.join(getcwd(), 'static')

    with open(path.join(static_folder, html_filename_temp), 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

    with open(path.join(static_folder, css_filename_temp), 'w', encoding='utf-8') as css_file:
        css_file.write(css_content)

    return html_filename_temp, css_filename_temp


if __name__ == "__main__":

    load_dotenv()

    startup = perf_counter()
    print("Connecting to S3...")
    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])
    print(f"Connected to S3 --- {startup - perf_counter()}s.")

    list_of_urls = ["https://www.youtube.co.uk", "https://www.google.co.uk"]

    download = perf_counter()
    print("Uploading HTML and CSS data to S3...")
    for url in list_of_urls:

        html_file_name, css_file_name = save_html_css(url)
        upload_to_s3(s3_client, url,
                     html_file_name, css_file_name)

    shutil.rmtree("static/")

    print(f"Data uploaded --- {download - perf_counter()}s.")
