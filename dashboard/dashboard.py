"""Script that creates the dashboard for the archiver data"""
from os import environ
import logging

from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import altair as alt

from extract import get_connection, get_all_data
from dashboard_functions import make_hourly_archive_tracker_line


def make_clickable(link):
    return f'<a target="_blank" href="{link}">{link}</a>'


if __name__ == "__main__":
    load_dotenv()
    logging.getLogger().setLevel(logging.INFO)

    connection = get_connection(environ)
    df = get_all_data(connection)

    st.set_page_config(page_title="Internet Archiver Dashboard",
                       page_icon=":bar_char:",
                       layout="wide")

    st.title("Internet Archiver Dashboard")

    make_hourly_archive_tracker_line(df)

    col1, col2 = st.columns(2)

    with col1:
        url_search = st.text_input("URL Search", placeholder="Search here...")

        if url_search:
            df_result_search = df[df['url'].str.contains(
                url_search, case=False, na=False)]

            st.write("Found {} Archived Records".format(
                str(df_result_search.shape[0])))

            st.dataframe(
                df_result_search[["url", "at"]], use_container_width=True)
