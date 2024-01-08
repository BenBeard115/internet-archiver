"""Script that creates the dashboard for the archiver data"""
from os import environ
import logging
import re

from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import altair as alt
from PIL import Image

from extract import get_connection, get_all_scrape_data, get_all_interaction_data
from dashboard_functions import (
    make_hourly_archive_tracker_line,
    make_archive_searchbar,
    make_popular_archives_bar,
    make_daily_archive_tracker_line,
    make_date_filter,
    make_date_radio,
    make_daily_visit_tracker_line,
    make_daily_save_tracker_line)


def make_url_alias(url):
    regex_pattern = r'^(https?:\/\/)?((?:www\.)?)([^\/]+)'
    match = re.search(regex_pattern, url)
    return match.group(3)


def setup_database():
    load_dotenv()
    logging.getLogger().setLevel(logging.INFO)

    connection = get_connection(environ)
    scrape_df = get_all_scrape_data(connection)
    scrape_df["url_alias"] = scrape_df["url"].apply(make_url_alias)

    interaction_df = get_all_interaction_data(connection)
    interaction_df["url_alias"] = interaction_df["url"].apply(make_url_alias)
    return scrape_df, interaction_df


def setup_page():
    img = Image.open("archive_image.png")

    st.set_page_config(page_title="Internet Archiver Dashboard",
                       page_icon=img,
                       layout="wide")

    st.title("Internet Archiver Dashboard")


if __name__ == "__main__":
    scrape_df, interaction_df = setup_database()
    setup_page()

    radio = make_date_radio()
    selected_date_scrape_df, selected_date_interaction_df = make_date_filter(
        scrape_df, interaction_df, radio)
    selected_website_scrape_df, selected_website_interaction_df = make_archive_searchbar(
        selected_date_scrape_df, selected_date_interaction_df)

    # make_daily_archive_tracker_line(df)

    # col1, col2 = st.columns([3, 2])

    # with col1:
    #     if selected_website_df.shape[0] > 0:
    #         make_hourly_archive_tracker_line(selected_website_df)

    # with col2:
    #     if selected_date_df.shape[0] > 0:
    #         make_popular_archives_bar(selected_date_df)

    # make_daily_visit_tracker_line(df)
    # make_daily_save_tracker_line(df)
