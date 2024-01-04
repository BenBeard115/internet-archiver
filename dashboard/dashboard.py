"""Script that creates the dashboard for the archiver data"""
from os import environ
import logging
import re

from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import altair as alt

from extract import get_connection, get_all_data
from dashboard_functions import make_hourly_archive_tracker_line, make_archive_searchbar, make_popular_archives_bar


def make_url_alias(url):
    regex_pattern = r'^(https?:\/\/)?((?:www\.)?)([^\/]+)'
    match = re.search(regex_pattern, url)
    return match.group(3)


if __name__ == "__main__":
    load_dotenv()
    logging.getLogger().setLevel(logging.INFO)

    connection = get_connection(environ)
    df = get_all_data(connection)

    df["url_alias"] = df["url"].apply(make_url_alias)

    st.set_page_config(page_title="Internet Archiver Dashboard",
                       page_icon=":bar_char:",
                       layout="wide")

    st.title("Internet Archiver Dashboard")

    make_hourly_archive_tracker_line(df)

    col1, col2 = st.columns(2)

    with col1:
        # TODO Add filter to sort by timeframe
        make_archive_searchbar(df)

    with col2:
        # TODO Only display the 5 most popular websites
        make_popular_archives_bar(df)
