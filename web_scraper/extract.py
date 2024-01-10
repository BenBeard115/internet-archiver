"""Script used to extract from the RDS to get the required URLs."""
from os import environ
from time import perf_counter

from dotenv import load_dotenv
from psycopg2 import connect, extensions, OperationalError


def get_database_connection() -> extensions.connection:
    """Connects you to the database, and returns an error if unable to connect."""

    try:
        return connect(host=environ["DB_IP"],
                       port=environ["DB_PORT"],
                       database=environ["DB_NAME"],
                       user=environ["DB_USERNAME"],
                       password=environ["DB_PASSWORD"])

    except OperationalError as exc:
        raise OperationalError("Error connecting to database.") from exc


def load_all_data(conn: extensions.connection) -> set:
    """Returns all of the url data from the database."""

    with conn.cursor() as cur:
        cur.execute(f"""
                    SELECT url FROM {environ["URL_TABLE_NAME"]}
                    JOIN {environ["SCRAPE_TABLE_NAME"]} ON
                    {environ["URL_TABLE_NAME"]}.url_id = {environ["SCRAPE_TABLE_NAME"]}.url_id
                    """)
        urls = cur.fetchall()
        conn.close()

        if len(urls) == 0:
            raise ValueError("No urls were found!")
        url_list = [url[0] for url in urls]
        return convert_to_set(url_list)


def convert_to_set(urls: list[str]) -> set:
    """Turns the list into a set to remove duplicate entries."""

    return set(urls)


if __name__ == "__main__":

    load_dotenv()

    startup = perf_counter()
    print("Loading data...")
    connection = get_database_connection()
    list_of_urls = load_all_data(connection)
    print(f"Data loaded --- {perf_counter() - startup}s.")

    print(f"Extract phase complete --- {perf_counter() - startup}s.")
