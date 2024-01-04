"""Script that creates the dashboard for the archiver data"""
from os import environ

from dotenv import load_dotenv

from extract import get_connection, get_all_data

if __name__ == "__main__":
    load_dotenv()
    print(environ["DB_USERNAME"])
    connection = get_connection(environ)
    print(get_all_data(connection))
