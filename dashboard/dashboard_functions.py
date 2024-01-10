"""Script containing functions to make the graphs on the dashboard."""
import os

import pandas as pd
import altair as alt
import streamlit as st
from PIL import Image


from download_screenshot import download_data_file, get_s3_client

BUCKET = 'c9-internet-archiver-bucket'

# TODO Add proper sorting to grouped bar charts


def make_metrics(scrape_data: pd.DataFrame, interaction_data: pd.DataFrame) -> None:
    """Creates metrics for number of archives, visits and saves."""
    archives = scrape_data[scrape_data["is_human"] == True]['url'].count()
    visits = interaction_data[interaction_data["type"]
                              == 'visit']['url'].count()
    saves = interaction_data[interaction_data["type"]
                             == 'save']['url'].count()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Archives", archives)

    with col2:
        st.metric("Visits", visits)

    with col3:
        st.metric("Saves", saves)


def make_date_radio() -> str:
    """Makes a date radio."""
    radio = st.sidebar.radio(label='Date Filter', options=[
        'None', 'Date Range', "Singular Date"])

    st.sidebar.write(
        """<style>div.row-widget.stRadio > div{flex-direction:row;}</style>""",
        unsafe_allow_html=True)

    return radio


def make_date_filter(scrape_df: pd.DataFrame, interaction_df: pd.DataFrame, radio: str) -> pd.DataFrame:
    """Makes a date filter"""
    min_date = min([min(scrape_df['scrape_at'].dt.date),
                   min(interaction_df['interact_at'].dt.date)])
    max_date = max([max(scrape_df['scrape_at'].dt.date),
                   max(interaction_df['interact_at'].dt.date)])

    st.markdown(
        """
    <style>
        div[role="presentation"] div{
            color: white;
        }
    </style>
    """,
        unsafe_allow_html=True)

    if radio == "Singular Date":
        # Defaults to most recent data
        selected_date = st.sidebar.date_input(
            "Select a date", max_date, key='date_selector', min_value=min_date, max_value=max_date)
        return scrape_df[scrape_df['scrape_at'].dt.date == selected_date], interaction_df[
            interaction_df['interact_at'].dt.date == selected_date]

    if radio == "Date Range":
        selected_date = st.sidebar.date_input(
            "Select a date", (min_date, max_date), key='date_selector',
            min_value=min_date, max_value=max_date)

        if len(selected_date) == 2:
            return scrape_df[(scrape_df['scrape_at'].dt.date >= selected_date[0]) & (
                scrape_df['scrape_at'].dt.date <= selected_date[1])], interaction_df[(
                    interaction_df['interact_at'].dt.date >= selected_date[0]) & (
                    interaction_df['interact_at'].dt.date <= selected_date[1])]

        return scrape_df[(scrape_df['scrape_at'].dt.date == selected_date[0])], interaction_df[
            (interaction_df['interact_at'].dt.date == selected_date[0])]

    return scrape_df, interaction_df


def make_archive_searchbar(scrape_df: pd.DataFrame, interaction_df: pd.DataFrame) -> None:
    """Makes a searchbar that returns the number of archives of a website and the archive times."""
    url_search = st.sidebar.text_input(
        "URL Search", placeholder="Search here...")

    if url_search:
        # Gets dataframe of specified url
        scrape_df_result_search = scrape_df[scrape_df['url'].str.contains(
            url_search.lower(), case=False, na=False)]

        interaction_df_result_search = interaction_df[interaction_df['url'].str.contains(
            url_search.lower(), case=False, na=False)]

        st.sidebar.write(
            "This URL has been:")

        # Grammar on singular/plural
        archive_pluralise = ''
        archive_count = scrape_df_result_search[scrape_df_result_search["is_human"]
                                                == True].shape[0]
        if archive_count != 1:
            archive_pluralise = 's'

        visit_pluralise = ''
        visit_count = interaction_df_result_search[interaction_df_result_search["type"]
                                                   == 'visit'].shape[0]
        if visit_count != 1:
            visit_pluralise = 's'

        save_pluralise = ''
        save_count = interaction_df_result_search[interaction_df_result_search["type"]
                                                  == 'save'].shape[0]
        if save_count != 1:
            save_pluralise = 's'

        st.sidebar.markdown(
            f"- Archived {archive_count} time{archive_pluralise}")
        st.sidebar.markdown(
            f"- Visited {visit_count} time{visit_pluralise}")
        st.sidebar.markdown(
            f"- Saved {save_count} time{save_pluralise}")

        st.sidebar.markdown('''
        <style>
        [data-testid="stMarkdownContainer"] ul{
            padding-left:40px;
        }
        </style>
        ''', unsafe_allow_html=True)

        return scrape_df_result_search, interaction_df_result_search
    return scrape_df, interaction_df


def make_hourly_tracker_line(data: pd.DataFrame) -> None:
    """Makes an hourly visit tracker."""
    st.subheader("Hourly Website Activity")

    saved = alt.Chart(data).mark_line().encode(
        x=alt.X("hours(interact_at):O").title("Time"),

        y=alt.Y("count(url):Q").title("Archives"),
        color=alt.Color("type", scale=alt.Scale(range=['#5A5A5A', '#d15353'])).title(
            "Type"))

    st.altair_chart(saved, use_container_width=True)


def make_daily_tracker_line(data: pd.DataFrame) -> None:
    """Makes an daily archive tracker."""
    st.subheader("Daily Website Activity")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("monthdate(interact_at):O").title("Time"),

        y=alt.Y("count(url):Q").title("Archives"),
        color=alt.Color("type", scale=alt.Scale(range=['#5A5A5A', '#d15353'])).title(
            "Type"))

    st.altair_chart(archived, use_container_width=True)


def make_popular_visit_bar(data: pd.DataFrame) -> None:
    """Makes a bar chart for the most popular sites to archive."""

    st.subheader("Popular Archives")
    # Gets the 5 most popular websites
    data = data.groupby(['url_short', 'type'])['url_short'].count().reset_index(
        name='Count').sort_values(['Count'], ascending=False)

    visit_data = data[data["type"] == 'visit'].head(5)["url_short"].tolist()

    data = data[data["url_short"].isin(visit_data)]

    archives = alt.Chart(data).mark_bar().encode(
        x=alt.X("Count").title(
            "Count"),
        y=alt.Y("type", axis=None).title(
            "Type").sort("-x"),

        color=alt.Color("type", scale=alt.Scale(range=['#5A5A5A', '#d15353'])).title(
            "Type"),

        row=alt.Row('url_short').sort("descending").title("URL")).properties(height=70, width=800)

    st.altair_chart(archives)


def make_popular_genre_visit_bar(data: pd.DataFrame) -> None:
    """Makes a bar chart for the most popular genres to visit and save."""

    st.subheader("Popular Genres")
    # Gets the 5 most popular genres
    data = data.groupby(['genre', 'type'])['url_alias'].count().reset_index(
        name='Count').sort_values(['Count'], ascending=False).head(5)

    genre = alt.Chart(data).mark_bar().encode(
        x=alt.X("Count").title(
            "Count"),
        y=alt.Y("type", axis=None).title(
            "Type").sort("-x"),

        color=alt.Color("type", scale=alt.Scale(range=['#5A5A5A', '#d15353'])).title(
            "Type"),

        row=alt.Row('genre').sort("descending").title("Genre")).properties(height=70, width=800)

    st.altair_chart(genre)


def make_recent_archive_database(data: pd.DataFrame) -> None:
    """Makes database of human input archives."""
    st.subheader("Archives")
    # Filter out auto-scraping
    data = data[data["is_human"] == True][["url_alias", "scrape_at"]]

    st.dataframe(data)


def get_popular_screenshot(scrape_data: pd.DataFrame, interaction_data: pd.DataFrame):
    """Gets and displays the most popular sites screenshot."""
    s3_client = get_s3_client()

    if not os.path.exists("./screenshots"):
        os.makedirs("./screenshots")

    popular_website = interaction_data.groupby(['url_alias', "url"])['url_alias'].count(
    ).reset_index(name='Count').sort_values(['Count'], ascending=False).head(1).iloc[0]

    s3_ref = scrape_data[scrape_data["url"] == popular_website["url"]].tail(
        1).iloc[0]['screenshot_s3_ref']

    download_data_file(
        s3_client, BUCKET, s3_ref, "screenshots")

    screenshot = Image.open(f"./screenshots/{s3_ref.replace('/', '-')}")

    st.subheader("Most Popular Site")
    st.text(
        f"{popular_website['url_alias']} with {popular_website['Count']} visits.")
    st.image(screenshot)

    os.remove(f"./screenshots/{s3_ref.replace('/', '-')}")
