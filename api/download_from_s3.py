"""Functions to download HTML and CSS files from S3 bucket."""

from datetime import datetime, timedelta
from os import environ, path, mkdir

from boto3 import client
from dotenv import load_dotenv

BUCKET = 'c9-internet-archiver-bucket'

load_dotenv()


def get_s3_client() -> client:
    """Gets S3 client."""

    return client('s3',
                  aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                  aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])


def get_object_keys(s3_client: client, bucket: str) -> list[str]:
    """Returns a list of object keys from a given bucket."""

    contents = s3_client.list_objects(Bucket=bucket)['Contents']
    
    return [o['Key'] for o in contents]


def filter_keys_by_type(keys: list[str], ends_with: str = None) -> list[str]:
    """Returns a list of relevant object keys of certain type."""

    filtered_keys = [key for key in keys if key.endswith(ends_with)]

    return filtered_keys


def filter_keys_by_website(keys: list[str], domain: str = None) -> list[str]:
    """Returns a list of relevant object keys for a given website."""

    filtered_keys = [key for key in keys if domain in key]

    return filtered_keys


def get_recent_object_keys(s3_client: client, bucket: str, num_files: int = 10) -> list[str]:
    """Returns a list of the 'num_files' most recent object keys uploaded to S3."""


    contents = s3_client.list_objects(Bucket=bucket)['Contents']

    sorted_contents = sorted(contents, key=lambda x: x['LastModified'], reverse=True)

    recent_keys = [
        o['Key'] for o in sorted_contents[:num_files] if '.html' in o["Key"]
    ]

    return recent_keys


def format_object_key_titles(keys: list[str]) -> list[str]:
    """Formats the keys as standardised titles to be listed on the website."""

    formatted_keys = [key.split('-')[0].replace("  ", " ").replace('/',' - ') for key in keys]
    return set(formatted_keys)


def download_data_files(s3_client: client, bucket: str, keys: list[str], folder_name: str) -> None:
    """Downloads the files with relevant keys to a folder name of choice."""

    if not path.exists(folder_name):
        mkdir(folder_name)

    for k in keys:
        new_filename = k.replace('/', '-')

        print(f"\nDownloading: {k}")
        s3_client.download_file(bucket, k, f"{folder_name}/{new_filename}")

def get_object_from_s3(s3_client: client, bucket: str, filename: str) -> dict:
    """"""
    response = s3_client.get_object(Bucket=bucket, Key=filename)
    html_data = response['Body'].read().decode('utf-8')
    return html_data




if __name__ == "__main__":

    s3_client = get_s3_client()

    # keys = get_object_keys(s3_client, BUCKET)

    # html_files = filter_keys_by_type(keys, '.html')

    # ikea_html = filter_keys_by_website(html_files, 'bbc')

    # most_recent_files = get_recent_object_keys(s3_client, BUCKET, num_files=10)

    # download_data_files(s3_client, BUCKET, ikea_html, 'data')

    get_object_from_s3(s3_client, BUCKET, "www.rocketleague.com/Rocket League     Rocket League  - Official Site/2024-01-05T15:53:37.392835.html")
