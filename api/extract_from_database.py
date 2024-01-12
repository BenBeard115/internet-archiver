"""Contains functions to extract data from the database."""
from time import perf_counter
from os import environ
import logging

from dotenv import load_dotenv
from psycopg2 import sql, extensions

from connect import get_connection


def extract_data(conn: extensions.connection, url: str) -> list[tuple]:
    """Extracts data from the database relating to a specified url."""
    extract_time = perf_counter()
    logging.info("Extracting data...")
    query = sql.SQL("""
                    SELECT {fields}
                    FROM {table_1}
                    JOIN {table_2} ON {table_1}.url_id = {table_2}.url_id
                    WHERE url = {url}
                    ;
                    """).format(
        table_1=sql.Identifier('page_scrape'),
        table_2=sql.Identifier('url'),
        fields=sql.SQL(',').join([
            sql.Identifier('url'),
            sql.Identifier('scrape_at'),
            sql.Identifier('html_s3_ref'),
            sql.Identifier('css_s3_ref')
        ]),
        url=sql.Literal(url)
    )

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    logging.info("Data Extracted --- %ss.",
                 round(perf_counter() - extract_time, 3))

    return rows


def get_url(s3_ref: str, conn: extensions.connection) -> str:
    """Gets the url from the database, given an s3_ref."""

    query = f"""SELECT url FROM url
                 JOIN page_scrape ON url.url_id = page_scrape.url_id
                 WHERE html_s3_ref LIKE '%{s3_ref}%'"""

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        try:
            if len(rows):
                url_extract = rows[0][0]
                return url_extract

        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return "Empty Database!"


def get_recent_png_key_s3(conn: extensions.connection, url: str) -> str:
    """Retrieves the key for png most recently uploaded to the S3 for
    a given URL."""

    query = f"""SELECT screenshot_s3_ref 
                    FROM page_scrape 
                    JOIN url ON page_scrape.url_id = url.url_id 
                    WHERE url LIKE '{url}' 
                    ORDER BY scrape_at 
                    DESC LIMIT 1;"""
    with conn.cursor() as cur:
        try:
            cur.execute(query)
            result = cur.fetchone()[0]
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

        return result


def get_png_keys_s3(conn: extensions.connection, url: str) -> str:
    """Retrieves the key for png most recently uploaded to the S3 for
    a given URL."""

    query = f"""SELECT screenshot_s3_ref 
                    FROM page_scrape 
                    JOIN url ON page_scrape.url_id = url.url_id 
                    WHERE url LIKE '{url}';"""
    with conn.cursor() as cur:
        try:
            cur.execute(query)
            rows = cur.fetchall()
            if len(rows):
                keys = [row[0] for row in rows]
            
            result = keys
    
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

        return result

def get_most_popular_urls(conn: extensions.connection) -> list[str]:
    """Gets the url from the database, given an s3_ref."""

    urls = []
    query = """SELECT COUNT(*), url FROM url
                JOIN user_interaction ON url.url_id = user_interaction.url_id 
                JOIN page_scrape ON url.url_id = page_scrape.url_id
                WHERE is_human is True
                GROUP BY url ORDER BY COUNT(*) 
                DESC LIMIT 10;"""

    with conn.cursor() as cur:
        cur.execute(query)
        try:
            url_tuples = cur.fetchall()
            for url in url_tuples:
                urls.append(url[1])
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return urls


def get_summary_from_db(s3_ref: str, conn: extensions.connection) -> str:
    """Gets the AI summary from the database, given an s3_ref."""

    query = f"""SELECT summary FROM url
                 JOIN page_scrape ON url.url_id = page_scrape.url_id
                 WHERE html_s3_ref LIKE '%{s3_ref}%'"""

    with conn.cursor() as cur:
        cur.execute(query)
        try:
            url_extract = cur.fetchall()[0][0]
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return url_extract


def get_genre_from_db(url: str, conn: extensions.connection) -> str:
    """Gets the AI-generated genre from the database, given an url."""

    query = f"""SELECT genre FROM url
                 JOIN page_scrape ON url.url_id = page_scrape.url_id
                 WHERE url LIKE '%{url}%'"""

    with conn.cursor() as cur:
        cur.execute(query)
        try:
            url_extract = cur.fetchall()[0][0]
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return url_extract


def get_first_submission_time(url: str, conn: extensions.connection) -> str:
    """Gets the timestamp of the first submission to the database, given a url."""

    query = f"""SELECT scrape_at FROM page_scrape
                 JOIN url ON url.url_id = page_scrape.url_id
                 WHERE url LIKE '%{url}%'
                 ORDER BY scrape_at ASC
                 LIMIT 1;"""

    with conn.cursor() as cur:
        cur.execute(query)
        try:
            url_extract = cur.fetchall()[0][0]
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return url_extract


def get_number_of_views(url: str, conn: extensions.connection) -> int:
    """Get number of views for a given url."""

    query = f"""SELECT COUNT(type_id) FROM user_interaction
                JOIN url ON url.url_id = user_interaction.url_id
                WHERE url LIKE '%{url}%' and type_id = 1;"""

    with conn.cursor() as cur:
        cur.execute(query)
        try:
            url_extract = cur.fetchall()[0][0]
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return url_extract


def get_number_of_saves(url: str, conn: extensions.connection) -> int:
    """Get number of saves for a given url."""

    query = f"""SELECT COUNT(type_id) FROM user_interaction
                JOIN url ON url.url_id = user_interaction.url_id
                WHERE url LIKE '%{url}%' and type_id = 2;"""

    with conn.cursor() as cur:
        cur.execute(query)
        try:
            url_extract = cur.fetchall()[0][0]
        except KeyError as exc:
            raise KeyError(
                "There were no values with that reference!") from exc

    return url_extract


if __name__ == "__main__":
    load_dotenv()
    logging.getLogger().setLevel(logging.INFO)

    connection = get_connection(environ)
    # print(extract_data(connection, "https://www.telegraph.co.uk/"))
    print(get_png_keys_s3(connection, 'www.rocketleague.com/'))
    print(get_url(
        'www.bbc.co.uk/BBC - Home', connection))
