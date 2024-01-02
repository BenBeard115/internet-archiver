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


def add_url(conn, response_data):
    search_query = sql.SQL("SELECT {field} FROM {table} WHERE {pkey} = %s").format(
        field=sql.Identifier('url_id'),
        table=sql.Identifier('url'),
        pkey=sql.Identifier('url'))

    with conn.cursor() as cur:
        cur.execute(search_query, (response_data["url"],))
        url_id = cur.fetchone()
        if not url_id:
            insert_query = sql.SQL("""
                    INSERT INTO {table} 
                        ({field})
                    VALUES
                        ({value});""").format(
                table=sql.Identifier('url'),
                field=sql.Identifier('url'),
                value=sql.Literal(response_data["url"])
            )
            cur.execute(insert_query)
            cur.execute(search_query, (response_data["url"],))
            url_id = cur.fetchone()

        return url_id[0]


def add_website(conn, response_data):
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

    response_data = {
        'url': "https://www.google.co.uk",
        'html_filename': 'FAKER_HTML',
        'css_filename': 'FAKER_CSS',
        'timestamp': datetime(2020, 6, 22, 19, 10, 20)
    }

    print(add_url(connection, response_data))
    # add_website(connection, response_data)

    # print_page_scrape(connection)
