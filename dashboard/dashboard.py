"""Script that creates the dashboard for the archiver data"""
from os import environ
import logging
import re

from dotenv import load_dotenv
import streamlit as st
from PIL import Image
import pandas as pd
from psycopg2 import extensions
from streamlit_autorefresh import st_autorefresh

from extract import get_connection, get_all_scrape_data, get_all_interaction_data
from dashboard_functions import (
    make_archive_searchbar,
    make_date_filter,
    make_date_radio,
    make_daily_tracker_line,
    make_hourly_tracker_line,
    make_popular_genre_visit_bar,
    make_popular_visit_bar,
    make_recent_archive_database,
    make_metrics,
    get_popular_screenshot,
    make_searchbar_toggle_radio)


def make_url_alias(url: str) -> str:
    """Makes an alias for the url."""
    regex_pattern = r'^(https?:\/\/)?((?:www\.)?)([^\/]+)'
    match = re.search(regex_pattern, url)
    return match.group(3)


def make_shorter_alias(url_alias: str) -> str:
    """Returns a shorter url alias for graphs."""
    if len(url_alias) >= 8:
        return url_alias[:8] + '...'
    return url_alias


def setup_database(connection: extensions.connection) -> tuple[pd.DataFrame]:
    """Sets up the database."""
    logging.getLogger().setLevel(logging.INFO)

    scrape_df = get_all_scrape_data(connection)
    scrape_df = scrape_df[scrape_df["url"] != "Empty Database!"]
    scrape_df["url_alias"] = scrape_df["url"].apply(make_url_alias)
    scrape_df["url_short"] = scrape_df["url_alias"].apply(make_shorter_alias)

    interaction_df = get_all_interaction_data(connection)
    interaction_df = interaction_df[interaction_df["url"] != "Empty Database!"]
    interaction_df["url_alias"] = interaction_df["url"].apply(make_url_alias)
    interaction_df["url_short"] = interaction_df["url_alias"].apply(
        make_shorter_alias)
    return scrape_df, interaction_df


def setup_page():
    """Sets up the main page of the dashboard."""
    img = Image.open("archive_image.png")

    st.set_page_config(page_title="SnapSite Dashboard",
                       page_icon=img,
                       layout="wide")

    st.title("SnapSite Dashboard")


if __name__ == "__main__":
    load_dotenv()
    connection = get_connection(environ)
    setup_page()

    st_autorefresh(interval=20000)

    scrape_df, interaction_df = setup_database(connection)

    st.sidebar.write(
        "[SnapSite: The Website Archiver](http://13.42.9.188:5000/)")

    date_radio = make_date_radio()
    selected_date_scrape_df, selected_date_interaction_df = make_date_filter(
        scrape_df, interaction_df, date_radio)

    search_radio = make_searchbar_toggle_radio()
    selected_website_scrape_df, selected_website_interaction_df = make_archive_searchbar(
        selected_date_scrape_df, selected_date_interaction_df, search_radio)

    make_metrics(selected_website_scrape_df, selected_website_interaction_df)
    make_daily_tracker_line(interaction_df)

    if selected_website_interaction_df.shape[0] > 0:
        make_hourly_tracker_line(selected_website_interaction_df)

    if selected_date_interaction_df.shape[0] > 0:
        make_popular_visit_bar(selected_date_interaction_df)

        make_popular_genre_visit_bar(selected_date_interaction_df)

    col1, col2 = st.columns(2)
    with col1:
        if selected_date_scrape_df.shape[0] > 0:
            make_recent_archive_database(selected_date_scrape_df)
        else:
            make_recent_archive_database(scrape_df)

    with col2:
        if selected_website_interaction_df.shape[0] > 0 and selected_website_scrape_df.shape[0] > 0:
            get_popular_screenshot(
                selected_website_scrape_df, selected_website_interaction_df)

        else:
            get_popular_screenshot(scrape_df, interaction_df)

    connection.close()
