"""Contains functions to download a website screenshot from their s3 bucket."""
from os import environ
from html2image import Html2Image
from dotenv import load_dotenv
from boto3 import client


hti = Html2Image()
load_dotenv()


def get_s3_client() -> client:
    """Gets S3 client."""

    return client('s3',
                  aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                  aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])


def download_data_file(s3_client: client, bucket: str, key: str, folder_name: str) -> str:
    """Downloads the files with relevant keys to a folder name of choice."""

    new_filename = key.replace('/', '-')
    print(f"\nDownloading: {key}")
    s3_client.download_file(bucket, key, f"{folder_name}/{new_filename}")
    return new_filename
