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
            sql.Identifier('at'),
            sql.Identifier('html'),
            sql.Identifier('css')
        ]),
        url=sql.Literal(url)
    )

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    logging.info("Data Extracted --- %ss.",
                 round(perf_counter() - extract_time, 3))

    return rows


if __name__ == "__main__":
    load_dotenv()
    logging.getLogger().setLevel(logging.INFO)

    connection = get_connection(environ)
    print(extract_data(connection, "https://www.telegraph.co.uk/"))
