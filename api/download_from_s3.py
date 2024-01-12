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

    contents = s3_client.list_objects(Bucket=bucket).get('Contents', None)

    if contents is None:
        return None

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

    contents = s3_client.list_objects(Bucket=bucket).get('Contents', None)

    if contents is None:
        return "Empty Database!"

    sorted_contents = sorted(
        contents, key=lambda x: x['LastModified'], reverse=True)

    recent_keys = [
        o['Key'] for o in sorted_contents if '.png' in o["Key"]
    ][:num_files]

    return recent_keys


def get_most_recent_png_key(s3_client: client, bucket: str, url: str) -> str:
    """Returns a list of the most recent .png keys uploaded to S3."""
    
    contents = s3_client.list_objects(Bucket=bucket).get('Contents', None)

    if contents is None:
        return "Empty Database!"

    sorted_contents = sorted(contents, key=lambda x: x['LastModified'], reverse=True)
    
    keys = [o['Key'] for o in sorted_contents if url in o['Key']
            and IMAGE_FILE_FORMAT in o['Key']]

    if len(keys) == 0:
        return 'No Relevant Keys'

    most_recent_key = keys[0]

    return most_recent_key



def format_object_key_titles(keys: list[str]) -> list[str]:
    """Formats the keys as standardised titles to be listed on the website."""

    formatted_keys = []

    for key in keys:
        formatted_key = key.split(
            '/')[0] + '/' + key.split('/')[1]
        formatted_keys.append(formatted_key)
    return set(formatted_keys)


def download_data_file(s3_client: client, bucket: str, key: str, folder_name: str) -> str:
    """Downloads the files with relevant keys to a folder name of choice."""

    new_filename = key.replace('/', '_')

    print(f"\nDownloading: {key}")
    try:
        s3_client.download_file(bucket, key, f"{folder_name}/{new_filename}")
    except:
        return None

    return new_filename


def get_object_from_s3(s3_client: client, bucket: str, filename: str) -> str:
    """Accesses the html content directly from the s3 bucket and return it as a string."""
    response = s3_client.get_object(Bucket=bucket, Key=filename)
    html = response['Body'].read().decode('utf-8')
    return html


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


def get_relevant_html_keys_for_url(s3_client: client, bucket: str, url: str) -> list[str]:
    """Returns a list of html keys from a given bucket, given a constraint."""
    url_without_https = url[8:]
    contents = s3_client.list_objects(Bucket=bucket)['Contents']

    return [o['Key'] for o in contents if o['Key'].startswith(url_without_https) and o['Key'].endswith('.html')]


def get_relevant_png_keys_for_url_from_s3(s3_client: client, bucket: str, url: str) -> list[str]:
    """Returns a list of object keys from a given bucket, given a constraint."""
    if 'https' in url:
        url_without_https = url[8:]
    else:
        url_without_https = url
    print(url)
    contents = s3_client.list_objects(Bucket=bucket)['Contents']

    return [o['Key'] for o in contents if o['Key'].startswith(url_without_https) and o['Key'].endswith('.png')]


def retrieve_searched_for_pages(s3_client: client, input: str):
    """Get the relevant pages that have been searched for."""

    keys = get_object_keys(s3_client, environ['S3_BUCKET'])
    if keys is None:
        return 'Empty Database!'

    png_keys = filter_keys_by_type(keys, '.png')
    relevant_keys = filter_keys_by_website(png_keys, input)
    
    return [relevant_key.split(
            '/')[0] + '/' + relevant_key.split('/')[1] for relevant_key in relevant_keys]


def get_most_recently_saved_web_pages() -> dict:
    """Get the most recently saved web pages to display on the website."""
    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])
    keys = get_recent_png_s3_keys(s3_client, environ['S3_BUCKET'])
    titles = format_object_key_titles(keys)
    
    return [title for title in titles]


if __name__ == "__main__":

    s3_client = get_s3_client()

    # keys = get_object_keys(s3_client, BUCKET)

    # html_files = filter_keys_by_type(keys, '.html')

    # ikea_html = filter_keys_by_website(html_files, 'bbc')

    # most_recent_files = get_recent_object_keys(s3_client, BUCKET, num_files=10)

    # download_data_files(s3_client, BUCKET, ikea_html, 'data')

    # get_object_from_s3(
    #     s3_client, BUCKET, "www.rocketleague.com/Rocket League     Rocket League  - Official Site/2024-01-05T15:53:37.392835.html")

    urls = ['www.bbc.co.uk']

    for url in urls:
        print(get_most_recent_png_key(s3_client, environ['S3_BUCKET'], url))

    print(get_most_recently_saved_web_pages())