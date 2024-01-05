"""Script containing functions to make the graphs on the dashboard."""
import pandas as pd
import altair as alt
import streamlit as st


def make_hourly_archive_tracker_line(data: pd.DataFrame):
    """Makes an hourly archive tracker."""
    st.subheader("Websites Archived")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("hours(at):O").title("Time"),
        y=alt.Y("count(url):Q").title("Archives"))

    st.altair_chart(archived, use_container_width=True)


def make_daily_archive_tracker_line(data: pd.DataFrame):
    """Makes an daily archive tracker."""
    st.subheader("Websites Archived")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("monthdate(at):O").title("Time"),
        y=alt.Y("count(url):Q").title("Archives"))

    st.altair_chart(archived, use_container_width=True)


def make_archive_searchbar(df: pd.DataFrame):
    """Makes a searchbar that returns the number of archives of a website and the archive times."""
    url_search = st.text_input("URL Search", placeholder="Search here...")

    if url_search:
        df_result_search = df[df['url'].str.contains(
            url_search, case=False, na=False)]

        st.write("Found {} Archived Records".format(
            str(df_result_search.shape[0])))

        st.dataframe(
            df_result_search[["url", "at"]], use_container_width=True)


def make_popular_archives_bar(df):
    """Makes a bar chart for the most popular sites to archive."""
    st.subheader("Popular Archives")
    archives = alt.Chart(df).mark_bar().encode(y=alt.Y("count(url)").title("Archive Count"),
                                               x=alt.X("url_alias").title("Website").sort("-y"))
    st.altair_chart(archives, use_container_width=True)
