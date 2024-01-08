"""Script containing functions to extract all data from the database."""
from time import perf_counter
from os import environ
import logging

from psycopg2 import connect, sql, DatabaseError, OperationalError, extensions
import pandas as pd


def get_connection(config: environ) -> extensions.connection:
    """Connects to the postgres database hosted on aws RDS."""
    connect_time = perf_counter()
    logging.info("Connecting to database...")
    try:
        conn = connect(user=config["DB_USERNAME"],
                       dbname=config["DB_NAME"],
                       password=config["DB_PASSWORD"],
                       host=config["DB_IP"])
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
                    SELECT 
                        url, genre, scrape_at, is_human, type, interact_at
                    FROM 
                        url
                    JOIN 
                        page_scrape ON url.url_id = page_scrape.url_id
                    JOIN 
                        user_interaction ON url.url_id = user_interaction.url_id
                    JOIN
                        interaction_type ON interaction_type.type_id = user_interaction.type_id
                    ;
                    """)

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    logging.info("Data Extracted --- %ss.",
                 round(perf_counter() - extract_time, 3))

    return pd.DataFrame(rows, columns=["url", "genre", "scrape_at",
                                       "is_human", "type", "interact_at"])
