"""Functions for accessing HTML and CSS files for the most recently saved webpages."""

from os import environ, path, mkdir

from boto3 import client
from dotenv import load_dotenv


def get_object_keys(s3_client: client, bucket: str) -> list[str]:
    """Returns a list of object keys from a bucket."""

    objects = s3_client.list_objects(Bucket=bucket)["Contents"]
    sorted_objects = sorted(
        objects, key=lambda obj: obj['LastModified'], reverse=True)
    return [object["Key"] for object in sorted_objects][:16]


def format_object_key_titles(keys: list[str]) -> list[str]:
    """Formats the keys as standardised titles to be listed on the website."""
    pass


def download_files_from_bucket(s3_client: client, bucket: str, keys: list[str], folder_name: str) -> None:
    """Downloads the files with relevant keys to a folder name of choice."""
    if not path.exists(folder_name):
        mkdir(folder_name)

    for key in keys:
        if not path.exists(f"{folder_name}/{key.split('/')[1]}.{key.split('.')[-1]}"):
            s3_client.download_file(
                bucket, key, f"{folder_name}/{key.split('/')[1]}.{key.split('.')[-1]}")


if __name__ == "__main__":

    load_dotenv()

    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])
    
    keys = get_object_keys(s3_client, environ['S3_BUCKET'])
    print(keys)
    download_files_from_bucket(s3_client, environ['S3_BUCKET'], keys, 'data')

