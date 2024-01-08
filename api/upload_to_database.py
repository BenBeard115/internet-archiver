"""Contains functions to upload scraped website data to a postgres database."""
from time import perf_counter
from os import environ
from datetime import datetime
import logging

from dotenv import load_dotenv
from psycopg2 import sql, extensions

from connect import get_connection


def add_visit(conn: extensions.connection, url: str) -> None:
    """Adds 1 to a url's visit_count"""
    update_time = perf_counter()

    visit_query = sql.SQL("""UPDATE {table}
                            SET {field} = {field} + 1
                            WHERE {url} = %s
                          ;
                          """).format(
        table=sql.Identifier('url'),
        field=sql.Identifier('visit_count'),
        url=sql.Identifier('url')
    )

    with conn.cursor() as cur:
        cur.execute(visit_query, (url,))
        conn.commit()

    logging.info("Visit Uploaded --- %ss.",
                 round(perf_counter() - update_time, 3))


def add_url(conn: extensions.connection, response_data: dict) -> None:
    """Adds a website's url to the database and extracts the url_id."""
    # query to search for the corresponding url_id
    upload_time = perf_counter()

    search_query = sql.SQL("""
                           SELECT {field} 
                            FROM {table} 
                            WHERE {url} = %s
                           """).format(
        field=sql.Identifier('url_id'),
        table=sql.Identifier('url'),
        url=sql.Identifier('url'))

    with conn.cursor() as cur:
        cur.execute(search_query, (response_data["url"],))
        url_id = cur.fetchone()
        # checking if site has been archived before
        if not url_id:
            # inserting url to url table
            insert_query = sql.SQL("""
                    INSERT INTO {table} 
                        ({fields})
                    VALUES
                        ({values});""").format(
                table=sql.Identifier('url'),
                fields=sql.SQL(',').join([
                    sql.Identifier('url'),
                    sql.Identifier('visit_count'),
                    sql.Identifier('summary')
                ]),
                values=sql.SQL(',').join([
                    sql.Literal(response_data["url"]),
                    sql.Literal(response_data["visit_count"]),
                    sql.Literal(response_data["summary"])
                ])
            )
            cur.execute(insert_query)
            cur.execute(search_query, (response_data["url"],))
            url_id = cur.fetchone()

        # adding the url_id to the response dictionary
        response_data["url_id"] = url_id[0]
        conn.commit()
        logging.info("URL Uploaded --- %ss.",
                     round(perf_counter() - upload_time, 3))


def add_website(conn: extensions.connection, response_data: dict) -> None:
    """Adds a website's data to the database."""
    upload_time = perf_counter()

    query = sql.SQL("""
                    INSERT INTO {table} 
                        ({fields})
                    VALUES
                        ({values});""").format(
        table=sql.Identifier('page_scrape'),
        fields=sql.SQL(',').join([
            sql.Identifier('url_id'),
            sql.Identifier('at'),
            sql.Identifier('html'),
            sql.Identifier('css')
        ]),
        values=sql.SQL(',').join([
            sql.Literal(response_data["url_id"]),
            sql.Literal(response_data["timestamp"]),
            sql.Literal(response_data["html_filename"]),
            sql.Literal(response_data["css_filename"])
        ])
    )

    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()

    logging.info("Website Uploaded --- %ss.",
                 round(perf_counter() - upload_time, 3))


if __name__ == "__main__":
    load_dotenv()
    logging.getLogger().setLevel(logging.INFO)

    connection = get_connection(environ)

    example_response_data = {
        'url': "https://www.youtube.co.uk",
        'html_filename': 'FAKE_HTML',
        'css_filename': 'FAKE_CSS',
        'timestamp': datetime(2023, 6, 22, 19, 10, 20)
    }

    add_url(connection, example_response_data)
    add_website(connection, example_response_data)
    add_visit(connection, example_response_data["url"])
