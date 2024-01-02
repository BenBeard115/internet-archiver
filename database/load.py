"""Contains functions to upload scraped website data to a postgres database."""
from os import environ
from datetime import datetime

from dotenv import load_dotenv
from psycopg2 import connect, sql, DatabaseError, OperationalError


def get_connection():
    load_dotenv()
    try:
        conn = connect(user=environ["DB_USERNAME"],
                       dbname=environ["DB_NAME"],
                       password=environ["DB_PASSWORD"],
                       host=environ["DB_IP"])
        return conn

    except (Exception, DatabaseError, OperationalError) as error:
        print(error)
        raise error


def add_website(conn, url_id, at, html, css):
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
            sql.Literal(url_id),
            sql.Literal(at),
            sql.Literal(html),
            sql.Literal(css)
        ])
    )

    with conn.cursor() as cur:

        cur.execute(query)

        cur.execute("SELECT * FROM page_scrape;")
        print(cur.fetchall())


def print_page_scrape(conn):
    query = sql.SQL("SELECT * FROM {table};").format(
        table=sql.Identifier('page_scrape'))

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        print(rows)


if __name__ == "__main__":
    connection = get_connection()

    url_id = 2
    at = datetime(2020, 6, 22, 19, 10, 20)
    html = 'FAKER_HTML'
    css = 'FAKER_CSS'

    add_website(connection, url_id, at, html, css)

    print_page_scrape(connection)
