"""Functions to download HTML and CSS files from S3 bucket."""

from datetime import datetime, timedelta
from os import environ, path, makedirs

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
        o['Key'] for o in sorted_contents[:num_files]
    ]

    return recent_keys


def download_data_files(s3_client: client, bucket: str, keys: list[str]) -> None:
    """Downloads the most recent files from S3."""

    for k in keys:
        new_filename = k.replace('/', '-')

        print(f"\nDownloading: {k}")
        s3_client.download_file(bucket, k, new_filename)


if __name__ == "__main__":

    s3_client = get_s3_client()

    keys = get_object_keys(s3_client, BUCKET)

    html_files = filter_keys_by_type(keys, '.html')
    css_files = filter_keys_by_type(keys, '.css')

    ikea_html = filter_keys_by_website(keys, 'ikea')
    guardian_html = filter_keys_by_website(keys, 'guardian')

    most_recent_files = get_recent_object_keys(s3_client, BUCKET, num_files=10)

    download_data_files(s3_client, BUCKET, most_recent_files)