"""Functions for accessing HTML and CSS files for the most recently saved webpages."""

from os import environ, path, mkdir

from boto3 import client
from dotenv import load_dotenv
from psycopg2 import connect, sql, DatabaseError, OperationalError, extensions

DISPLAY_LIMIT = 8

def get_object_keys(s3_client: client, bucket: str) -> list[str]:
    """Returns a list of object keys from a bucket."""

    objects = s3_client.list_objects(Bucket=bucket)["Contents"]
    sorted_objects = sorted(
        objects, key=lambda obj: obj['LastModified'], reverse=True)
    return [object["Key"] for object in sorted_objects if '.html' in object["Key"]][:DISPLAY_LIMIT]


def format_object_key_titles(keys: list[str]) -> list[str]:
    """Formats the keys as standardised titles to be listed on the website."""
    formatted_keys = [key.split('-')[0].replace("  ", " ").replace('/',' - ') for key in keys]
    return set(formatted_keys)


def get_database_connection() -> extensions.connection:
    """Connects you to the database, and returns an error if unable to connect."""

    try:
        return connect(host=environ["DB_IP"],
                       port=environ["DB_PORT"],
                       database=environ["DB_NAME"],
                       user=environ["DB_USERNAME"],
                       password=environ["DB_PASSWORD"])

    except OperationalError as exc:
        raise OperationalError("Error connecting to database.") from exc


# def get_url_from_html_file_name(conn: extensions.connection) -> dict:
#     """Uses an SQL query to get the 8 most recently saved website urls and html file names."""
#     with conn.cursor() as cur:
#         cur.execute("""
#                     SELECT url,html FROM url
#                     JOIN page_scrape ON
#                     url.url_id = page_scrape.url_id
#                     ORDER BY at DESC
#                     LIMIT 8;""")
#         data = cur.fetchall()
#         return data


if __name__ == "__main__":

    load_dotenv()

    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])

    keys = get_object_keys(s3_client, environ['S3_BUCKET'])

    connection = get_database_connection()

    # print(get_url_from_html_file_name(connection))


