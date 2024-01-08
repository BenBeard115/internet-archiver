"""Script containing functions to extract all data from the database."""
from time import perf_counter
from os import environ
import logging

from psycopg2 import connect, sql, DatabaseError, OperationalError, extensions
import pandas as pd


def get_connection(environ: environ) -> extensions.connection:
    """Connects to the postgres database hosted on aws RDS."""
    connect_time = perf_counter()
    logging.info("Connecting to database...")
    try:
        conn = connect(user=environ["DB_USERNAME"],
                       dbname=environ["DB_NAME"],
                       password=environ["DB_PASSWORD"],
                       host=environ["DB_IP"])
        logging.info("Connected --- %ss.",
                     round(perf_counter() - connect_time, 3))
        return conn

    except (Exception, DatabaseError, OperationalError) as error:
        logging.warning("%s --- %ss.",
                        error, round(perf_counter() - connect_time, 3))
        raise error


def get_all_data(conn: extensions.connection):
    """Extracts all data from the database."""
    extract_time = perf_counter()
    logging.info("Extracting data...")
    query = sql.SQL("""
                    SELECT {fields}
                    FROM {url_table}
                    JOIN {page_scrape_table} ON {url_table}.url_id = {page_scrape_table}.url_id
                    ;
                    """).format(
        page_scrape_table=sql.Identifier('page_scrape'),
        url_table=sql.Identifier('url'),
        fields=sql.SQL(',').join([
            sql.Identifier('url'),
            sql.Identifier('at'),
            sql.Identifier('html'),
            sql.Identifier('css')
        ])
    )

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    logging.info("Data Extracted --- %ss.",
                 round(perf_counter() - extract_time, 3))

    return pd.DataFrame(rows, columns=["url", "at", "html", "css"])
