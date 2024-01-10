"""Functions to download HTML and CSS files from S3 bucket."""

from datetime import datetime, timedelta
from os import environ, path, mkdir

from boto3 import client
from dotenv import load_dotenv

BUCKET = 'c9-internet-archiver-bucket'
USER_FRIENDLY_FORMAT = '%d %B %Y - %I:%M %p'
IMAGE_FILE_FORMAT = '.png'

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


def get_recent_png_s3_keys(s3_client: client, bucket: str, num_files: int = 10) -> list[str]:
    """Returns a list of the most recent .png keys uploaded to S3."""

    contents = s3_client.list_objects(Bucket=bucket)['Contents']

    sorted_contents = sorted(
        contents, key=lambda x: x['LastModified'], reverse=True)

    recent_keys = [
        o['Key'] for o in sorted_contents if '.png' in o["Key"]
    ][:num_files]

    return recent_keys


def get_recent_html_s3_keys(s3_client: client, bucket: str, num_files: int = 10) -> list[str]:
    """Returns a list of the most recent .html keys uploaded to S3."""

    contents = s3_client.list_objects(Bucket=bucket)['Contents']

    sorted_contents = sorted(
        contents, key=lambda x: x['LastModified'], reverse=True)

    recent_keys = [
        o['Key'] for o in sorted_contents if '.html' in o["Key"]
    ][:num_files]

    return recent_keys


def format_object_key_titles(keys: list[str]) -> list[str]:
    """Formats the keys as standardised titles to be listed on the website."""

    formatted_keys = [
        key.split('-')[0].replace("  ", " ").replace('/', ' - ') for key in keys]
    return set(formatted_keys)


def download_data_file(s3_client: client, bucket: str, key: str, folder_name: str) -> str:
    """Downloads the files with relevant keys to a folder name of choice."""

    new_filename = key.replace('/', '_')

    print(f"\nDownloading: {key}")
    s3_client.download_file(bucket, key, f"{folder_name}/{new_filename}")
    return new_filename


def get_object_from_s3(s3_client: client, bucket: str, filename: str) -> str:
    """Accesses the html content directly from the s3 bucket and return it as a string."""
    response = s3_client.get_object(Bucket=bucket, Key=filename)
    html = response['Body'].read().decode('utf-8')
    return html


def get_all_pages_ordered(s3_client: client, html_filename: str, bucket: str) -> list[str]:
    """Gets all previous scrapes of a webpage and returns the keys in reverse chronological order."""

    startswith = f"{html_filename.split('/')[0]}/{html_filename.split('/')[1]}"

    contents = s3_client.list_objects(Bucket=bucket)['Contents']
    sorted_contents = sorted(
        contents, key=lambda x: x['LastModified'], reverse=True)

    return [object['Key'] for object in sorted_contents if object['Key'].startswith(startswith) and object['Key'].endswith('.html')]


def get_all_screenshots(html_files: list[str]) -> list[str]:
    """Gets all previous screenshots of a webpage given an html key."""

    return [filename.replace('.html', '.png').replace('/', '_') for filename in html_files]


def get_scrape_times(html_files: list[str]) -> list[str]:
    """Extract the times scraped."""

    return [filename.split('/')[-1].replace('.html', '')
            for filename in html_files]


def format_timestamps(timestamps: list[str]) -> list[str]:
    """Convert to user-friendly format."""

    return [datetime.strptime(
        ts, "%Y-%m-%dT%H:%M:%S.%f").strftime(USER_FRIENDLY_FORMAT) for ts in timestamps]

def get_relevant_html_keys_for_url(s3_client: client, bucket: str, url:str) -> list[str]:
    """Returns a list of object keys from a given bucket, given a constraint."""
    url_without_https = url[8:]
    contents = s3_client.list_objects(Bucket=bucket)['Contents']
    return [o['Key'] for o in contents if o['Key'].startswith(url_without_https) and o['Key'].endswith('.html')]

if __name__ == "__main__":

    s3_client = get_s3_client()

    # keys = get_object_keys(s3_client, BUCKET)

    # html_files = filter_keys_by_type(keys, '.html')

    # ikea_html = filter_keys_by_website(html_files, 'bbc')

    # most_recent_files = get_recent_object_keys(s3_client, BUCKET, num_files=10)

    # download_data_files(s3_client, BUCKET, ikea_html, 'data')

    # get_object_from_s3(
    #     s3_client, BUCKET, "www.rocketleague.com/Rocket League     Rocket League  - Official Site/2024-01-05T15:53:37.392835.html")

    
    urls = ['https://www.youtube.co.uk', 'https://www.bbc.co.uk/news/uk-politics-62064552', 'https://www.itv.co.uk', 'https://www.bbc.co.uk',
        'https://www.theguardian.com/film/2023/dec/31/raging-grace-review-gothic-infused-filipina-immigrant-thriller-paris-zarcilla']
    
  

    for url in urls:
        print(url[8:])
        print(get_relevant_object_keys_for_url(s3_client, environ['S3_BUCKET'], url))
    

