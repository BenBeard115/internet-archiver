"""Functions to upload HTML and CSS files to S3 bucket."""

from datetime import datetime
from os import environ
import re

from boto3 import client
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.request import urlopen, Request


def sanitise_filename(filename: str) -> str:
    """Remove special characters from filename."""

    return re.sub(r'[^\w\s.-]', ' ', filename)


def extract_title(url: str) -> str:
    """Extracts title used for s3_filename from given url."""

    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.title.text.strip()

    return sanitise_filename(title)


def extract_domain(url: str) -> str:
    """Extracts domain name used for s3_filename from given url."""

    regex_pattern = r'^(https?:\/\/)?((?:www\.)?)([^\/]+)'

    match = re.search(regex_pattern, url)

    return match.group(2) + match.group(3)


def upload_file_to_s3(s3_client: client, filename: str, bucket: str, key: str) -> None:
    """Uploads a file to the specified S3 bucket."""

    try:
        s3_client.upload_file(filename, bucket, key)
        print('Upload successful!')

    except Exception as e:
        print('Unable to upload file. Please check details!')


if __name__ == "__main__":

    load_dotenv()

    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])

    url = 'https://www.theguardian.com/world/2024/jan/02/japan-earthquakes-tsunami-alert-dropped-but-residents-told-not-to-return-to-homes'

    title = extract_title(url)
    url_domain = extract_domain(url)
    timestamp = datetime.utcnow().isoformat()

    file_to_upload = 'static/Japan earthquakes: ‘battle against time’ to find those trapped under rubble as death toll rises | Japan | The Guardian_html.html'
    s3_object_key = f'{url_domain}/{title}/{timestamp}.html'

    upload_file_to_s3(s3_client, file_to_upload,
                      environ['S3_BUCKET'], s3_object_key)
