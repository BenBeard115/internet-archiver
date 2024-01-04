"""Script used to extract from the RDS to get the required URLs."""
import os
from os import environ, path, mkdir
from time import perf_counter
import requests

from dotenv import load_dotenv
from bs4 import BeautifulSoup
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
    """Returns all of the truck data from the database."""

    with conn.cursor() as cur:
        cur.execute(f"""
                    SELECT url FROM {environ["URL_TABLE_NAME"]}
                    JOIN {environ["SCRAPE_TABLE_NAME"]} ON
                    {environ["URL_TABLE_NAME"]}.url_id = {environ["SCRAPE_TABLE_NAME"]}.url_id
                    """)
        urls = cur.fetchall()

        if len(urls) == 0:
            raise ValueError("No urls were found!")
        url_list = [url[0] for url in urls]
        return convert_to_set(url_list)


def convert_to_set(urls: list[str]) -> set:
    """Turns the list into a set to remove duplicate entries."""

    return set(urls)


def save_html_css(url: str):
    """Scrape HTML and CSS from a given URL and save them."""

    if not path.exists('static'):
        mkdir('static')

    headers = requests.utils.default_headers()
    headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',})
    response = requests.get(url, headers=headers, timeout=30)

    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.title.text.strip()

    html_content = str(soup)
    css_content = '\n'.join([style.text for style in soup.find_all('style')])

    html_filename = f"{title}_html.html"
    css_filename = f"{title}_css.css"

    static_folder = os.path.join(os.getcwd(), 'static')

    with open(os.path.join(static_folder, html_filename), 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

    with open(os.path.join(static_folder, css_filename), 'w', encoding='utf-8') as css_file:
        css_file.write(css_content)

    return html_filename, css_filename


def scrape_all_urls(urls: set) -> None:
    """Scrapes the data for all the unique urls in the database."""

    for url in urls:
        save_html_css(url)


if __name__ == "__main__":

    load_dotenv()

    startup = perf_counter()
    print("Loading data...")
    connection = get_database_connection()
    list_of_urls = load_all_data(connection)
    print(f"Data loaded --- {perf_counter() - startup}s.")

    scraper = perf_counter()
    print("Scraping websites...")
    scrape_all_urls(list_of_urls)
    print(f"Websites scraped --- {perf_counter() - scraper}s.")

    print(f"Extract phase complete --- {perf_counter() - startup}s.")
