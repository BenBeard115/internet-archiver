"""Contains functions to upload scraped website data to a postgres database."""
from time import perf_counter
from os import environ
from datetime import datetime
import logging

from dotenv import load_dotenv
from psycopg2 import sql, extensions

from connect import get_connection

VISIT_ID = 1
SAVE_ID = 2


def add_interaction(conn: extensions.connection, interaction_data: dict) -> None:
    """Adds interactions to the interactions database."""
    update_time = perf_counter()

    if interaction_data.get("type") == 'visit':
        type_id = VISIT_ID

    elif interaction_data.get("type_id") == 'save':
        type_id = SAVE_ID

    else:
        raise ValueError("Invalid type value")

    interaction_query = sql.SQL("""
                    INSERT INTO {table} 
                        ({fields})
                    VALUES
                        ({values});""").format(
        table=sql.Identifier('user_interaction'),
        fields=sql.SQL(',').join([
            sql.Identifier('url_id'),
            sql.Identifier('type_id'),
            sql.Identifier('interact_at')
        ]),
        values=sql.SQL(',').join([
            sql.Literal(interaction_data["url_id"]),
            sql.Literal(type_id),
            sql.Literal(interaction_data.get("interact_at"))
        ])
    )

    with conn.cursor() as cur:
        cur.execute(interaction_query)
        conn.commit()

    logging.info("Interaction Uploaded --- %ss.",
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
                    sql.Identifier('summary'),
                    sql.Identifier('genre')
                ]),
                values=sql.SQL(',').join([
                    sql.Literal(response_data["url"]),
                    sql.Literal(response_data.get("summary")),
                    sql.Literal(response_data.get("genre"))
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
            sql.Identifier('scrape_at'),
            sql.Identifier('html_s3_ref'),
            sql.Identifier('css_s3_ref'),
            sql.Identifier('screenshot_s3_ref'),
            sql.Identifier('is_human')
        ]),
        values=sql.SQL(',').join([
            sql.Literal(response_data["url_id"]),
            sql.Literal(response_data["scrape_timestamp"]),
            sql.Literal(response_data["html_filename"]),
            sql.Literal(response_data["css_filename"]),
            sql.Literal(response_data["screenshot_filename"]),
            sql.Literal(response_data["is_human"])
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
        'screenshot_filename': 'FAKE_SCREENSHOT',
        'scrape_timestamp': datetime(2023, 6, 22, 19, 10, 20),
        'is_human': True,
        'summary': 'FAKE SUMMARY',
        'genre': 'media'
    }

    add_url(connection, example_response_data)
    add_website(connection, example_response_data)

    example_interaction_data = {
        'url': "https://www.youtube.co.uk",
        'type': 'visit',
        'interact_at': datetime(2023, 9, 22, 19, 10, 20)
    }

    add_url(connection, example_interaction_data)
    add_interaction(connection, example_interaction_data)
