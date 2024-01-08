"""Script containing functions to make the graphs on the dashboard."""
from datetime import datetime
import pandas as pd
import altair as alt
import streamlit as st


def make_date_radio():
    radio = st.sidebar.radio(label='Date Filter', options=[
        'None', 'Date Range', "Singular Date"])

    st.sidebar.write(
        """<style>div.row-widget.stRadio > div{flex-direction:row;}</style>""", unsafe_allow_html=True)

    return radio


def make_date_filter(df: pd.DataFrame, radio: str):
    """Makes a date filter"""
    min_date = min([min(df['scrape_at'].dt.date),
                   min(df['interact_at'].dt.date)])
    max_date = max([max(df['scrape_at'].dt.date),
                   max(df['interact_at'].dt.date)])

    st.markdown(
        """
    <style>

        div[role="presentation"] div{
            color: white;
        }
    </style>
    """,
        unsafe_allow_html=True,)

    if radio == "Singular Date":
        # Defaults to most recent data
        selected_date = st.sidebar.date_input(
            "Select a date", max_date, key='date_selector', min_value=min_date, max_value=max_date)
        return df[(df['scrape_at'].dt.date == selected_date) & (df['interact_at'].dt.date == selected_date)]

    if radio == "Date Range":
        selected_date = st.sidebar.date_input(
            "Select a date", (min_date, max_date), key='date_selector', min_value=min_date, max_value=max_date)

        if len(selected_date) == 2:
            return df[(df['scrape_at'].dt.date >= selected_date[0]) & (df['scrape_at'].dt.date <= selected_date[1]) & (
                df['interact_at'].dt.date >= selected_date[0]) & (df['interact_at'].dt.date <= selected_date[1])]

        else:
            return df[(df['scrape_at'].dt.date == selected_date[0]) & (df['interact_at'].dt.date == selected_date[0])]

    return df


def make_hourly_archive_tracker_line(data: pd.DataFrame):
    """Makes an hourly archive tracker."""
    st.subheader("Websites Archived")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("hours(at):O").title("Time"),
        y=alt.Y("count(url):Q").title("Archives")).configure_line(color="#d15353")

    st.altair_chart(archived, use_container_width=True)


def make_daily_archive_tracker_line(data: pd.DataFrame):
    """Makes a daily archive tracker."""
    st.subheader("Total Websites Archived")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("monthdate(at):O").title("Time"),
        y=alt.Y("count(url):Q").title("Archives")).configure_line(color="#d15353")

    st.altair_chart(archived, use_container_width=True)


def make_daily_visit_tracker_line(data: pd.DataFrame):
    """Makes an daily archive tracker."""
    st.subheader("Daily Archives Visited")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("monthdate(at):O").title("Time"),
        y=alt.Y("visit_count:Q").title("Archives Visited")).configure_line(color="#d15353")

    st.altair_chart(archived, use_container_width=True)


def make_daily_save_tracker_line(data: pd.DataFrame):
    """Makes an daily archive tracker."""
    st.subheader("Daily Archives Saved")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("monthdate(at):O").title("Time"),
        y=alt.Y("save_count:Q").title("Archives Saved")).configure_line(color="#d15353")

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
    # Gets the 5 most popular websites
    data = data.groupby(['url_alias'])['url_alias'].count().reset_index(
        name='Count').sort_values(['Count'], ascending=False).head(5)

    archives = alt.Chart(data).mark_bar().encode(y=alt.Y("Count").title("Archive Count"),
                                                 x=alt.X("url_alias").title(
                                                     "Website").sort("-y")).configure_bar(color="#d15353")

    st.altair_chart(archives, use_container_width=True)
