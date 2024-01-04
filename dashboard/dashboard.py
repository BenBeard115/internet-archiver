"""Script that creates the dashboard for the archiver data"""
from os import environ
import logging
import re

from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import altair as alt

from extract import get_connection, get_all_data
from dashboard_functions import make_hourly_archive_tracker_line


def make_clickable(link):
    return f'<a target="_blank" href="{link}">{link}</a>'


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
        url_search = st.text_input("URL Search", placeholder="Search here...")

        if url_search:
            df_result_search = df[df['url'].str.contains(
                url_search, case=False, na=False)]

            st.write("Found {} Archived Records".format(
                str(df_result_search.shape[0])))

            st.dataframe(
                df_result_search[["url", "at"]], use_container_width=True)

    with col2:
        st.subheader("Popular Archives")
        archives = alt.Chart(df).mark_bar().encode(y=alt.Y("count(url)").title("Archive Count"),
                                                   x=alt.X("url_alias").title("Website").sort("-y"))
        st.altair_chart(archives, use_container_width=True)
