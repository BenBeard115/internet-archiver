"""Script containing functions to make the graphs on the dashboard."""
from datetime import datetime
import pandas as pd
import altair as alt
import streamlit as st


def make_timeframe_filter(df: pd.DataFrame):
    today = datetime.today()
    selected_date = st.sidebar.date_input(
        "Select a date", today, key='date_selector')
    selected_df = df[df['at'].dt.date == selected_date]
    return selected_df


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


def make_archive_searchbar(data: pd.DataFrame):
    """Makes a searchbar that returns the number of archives of a website and the archive times."""
    url_search = st.sidebar.text_input(
        "URL Search", placeholder="Search here...")

    if url_search:
        # Gets dataframe of specified url
        df_result_search = data[data['url'].str.contains(
            url_search.lower(), case=False, na=False)]

        # Grammar on singular/plural
        if df_result_search.shape[0] == 1:
            st.sidebar.write("Found {} Archived Record".format(
                str(df_result_search.shape[0])))

        else:
            st.sidebar.write("Found {} Archived Records".format(
                str(df_result_search.shape[0])))

        return df_result_search
    return data


def make_popular_archives_bar(data: pd.DataFrame):
    """Makes a bar chart for the most popular sites to archive."""
    st.subheader("Popular Archives")
    # TODO Add text to each bar of the number of visits (only possible when visits added)
    data = data.groupby(['url_alias'])['url_alias'].count().reset_index(
        name='Count').sort_values(['Count'], ascending=False).head(10)

    archives = alt.Chart(data).mark_bar().encode(y=alt.Y("Count").title("Archive Count"),
                                                 x=alt.X("url_alias").title(
                                                     "Website").sort("-y"))

    st.altair_chart(archives, use_container_width=True)
