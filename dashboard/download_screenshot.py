
from os import environ, remove
from html2image import Html2Image
from dotenv import load_dotenv
from boto3 import client


IMAGE_FILE_FORMAT = '.png'
BUCKET = 'c9-internet-archiver-bucket'


hti = Html2Image()
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

    sorted_contents = sorted(
        contents, key=lambda x: x['LastModified'], reverse=True)

    recent_keys = [
        o['Key'] for o in sorted_contents if '.png' in o["Key"]
    ][:num_files]

    return recent_keys


def format_object_key_titles(keys: list[str]) -> list[str]:
    """Formats the keys as standardised titles to be listed on the website."""

    formatted_keys = [
        key.split('-')[0].replace("  ", " ").replace('/', ' - ') for key in keys]
    return set(formatted_keys)


def download_data_file(s3_client: client, bucket: str, key: str, folder_name: str) -> str:
    """Downloads the files with relevant keys to a folder name of choice."""

    new_filename = key.replace('/', '-')

    print(f"\nDownloading: {key}")
    s3_client.download_file(bucket, key, f"{folder_name}/{new_filename}")
    return new_filename


def get_object_from_s3(s3_client: client, bucket: str, filename: str) -> str:
    """Accesses the html content directly from the s3 bucket and return it as a string."""
    response = s3_client.get_object(Bucket=bucket, Key=filename)
    html = response['Body'].read().decode('utf-8')
    return html


def download_screenshot():
    pass


if __name__ == "__main__":

    s3_client = get_s3_client()

    keys = get_object_keys(s3_client, BUCKET)
    print(keys)

    png_files = filter_keys_by_type(keys, '.png')
    print(png_files)

    # ikea_html = filter_keys_by_website(html_files, 'bbc')
    # print(ikea_html)
