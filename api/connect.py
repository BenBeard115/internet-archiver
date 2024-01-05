"""Contains a function to connect to the database."""
from time import perf_counter
from os import environ
import logging

from psycopg2 import connect, DatabaseError, OperationalError, extensions


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
