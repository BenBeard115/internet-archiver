"""Contains functions to upload scraped website data to a postgres database."""
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


def add_url(conn: extensions.connection, response_data: dict) -> None:
    """Adds a website's url to the database and extracts the url_id."""
    # query to search for the corresponding url_id
    search_query = sql.SQL("SELECT {field} FROM {table} WHERE {pkey} = %s").format(
        field=sql.Identifier('url_id'),
        table=sql.Identifier('url'),
        pkey=sql.Identifier('url'))

    with conn.cursor() as cur:
        cur.execute(search_query, (response_data["url"],))
        url_id = cur.fetchone()
        # checking if site has been archived before
        if not url_id:
            # inserting url to url table
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

        # adding the url_id to the response dictionary
        response_data["url_id"] = url_id[0]
        conn.commit()


def add_website(conn: extensions.connection, response_data: dict) -> None:
    """Adds a website's data to the database."""
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


if __name__ == "__main__":
    load_dotenv()
    connection = get_connection()

    example_response_data = {
        'url': "https://www.example.co.uk",
        'html_filename': 'FAKER_HTML',
        'css_filename': 'FAKER_CSS',
        'timestamp': datetime(2020, 6, 22, 19, 10, 20)
    }

    print(add_url(connection, example_response_data))
    add_website(connection, example_response_data)
