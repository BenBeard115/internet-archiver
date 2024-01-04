"""Contains functions to extract data from the database."""
from os import environ
from datetime import datetime

from dotenv import load_dotenv
from psycopg2 import connect, sql, DatabaseError, OperationalError, extensions


def get_connection() -> extensions.connection:
    """Connects to the postgres database hosted on aws RDS."""
    try:
        conn = connect(user=environ["DB_USERNAME"],
                       dbname=environ["DB_NAME"],
                       password=environ["DB_PASSWORD"],
                       host=environ["DB_IP"])
        return conn

    except (Exception, DatabaseError, OperationalError) as error:
        print(error)
        raise error


def extract_data():
    pass


if __name__ == "__main__":
    load_dotenv()
    connection = get_connection()
