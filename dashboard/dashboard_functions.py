"""Script containing functions to make the graphs on the dashboard."""
import os

import pandas as pd
import altair as alt
import streamlit as st
from PIL import Image


from download_screenshot import download_data_file, get_s3_client

BUCKET = 'c9-internet-archiver-bucket'


def make_searchbar_toggle_radio() -> None:
    """Makes a searchbar radio."""
    radio = st.sidebar.radio(label='Search by...', options=[
        'URL', 'Genre'])
    st.sidebar.write(
        """<style>div.row-widget.stRadio > div{flex-direction:row;}</style>""",
        unsafe_allow_html=True)

    return radio


def make_metrics(scrape_data: pd.DataFrame, interaction_data: pd.DataFrame) -> None:
    """Creates metrics for number of archives, visits and saves."""
    archives = scrape_data['url'].nunique()
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


def make_archive_searchbar(scrape_df: pd.DataFrame, interaction_df: pd.DataFrame, radio: str) -> None:
    """Makes a searchbar that returns the number of archives of a website and the archive times."""
    filter_by = None
    # Choice of what to search the database by
    if radio == "Genre":
        search = st.sidebar.text_input(
            "Genre Search", placeholder="Search here...")

        if search:
            filter_by = 'genre'
    else:
        search = st.sidebar.text_input(
            "URL Search", placeholder="Search here...")

        if search:
            filter_by = 'url'

    if filter_by:
        # Gets dataframe of specified url or genre
        scrape_df_result_search = scrape_df[scrape_df[filter_by].str.contains(
            search.lower(), case=False, na=False)]

        interaction_df_result_search = interaction_df[interaction_df[filter_by].str.contains(
            search.lower(), case=False, na=False)]

        st.sidebar.write(
            f"This {filter_by} has been:")

        # Grammar on singular/plural
        archive_pluralise = ''
        archive_count = scrape_df_result_search['url'].nunique()
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

        y=alt.Y("count(url):Q").title("Count"),
        color=alt.Color("type", scale=alt.Scale(range=['#5A5A5A', '#d15353'])).title(
            "Type"))

    st.altair_chart(saved, use_container_width=True)


def make_daily_tracker_line(data: pd.DataFrame) -> None:
    """Makes an daily archive tracker."""
    st.subheader("Daily Website Activity")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("monthdate(interact_at):O").title("Time"),

        y=alt.Y("count(url):Q").title("Count"),
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

        row=alt.Row('url_short').title("URL")).properties(height=70, width=800)

    st.altair_chart(archives)


def make_popular_genre_visit_bar(data: pd.DataFrame) -> None:
    """Makes a bar chart for the most popular genres to visit and save."""

    st.subheader("Popular Genres")
    # Gets the 5 most popular genres
    data = data.groupby(['genre', 'type'])['url_alias'].count().reset_index(
        name='Count').sort_values(['Count'], ascending=False)

    genre_data = data[data["type"] == 'visit'].head(5)["genre"].tolist()

    data = data[data["genre"].isin(genre_data)]

    genre = alt.Chart(data).mark_bar().encode(
        x=alt.X("Count").title(
            "Count"),
        y=alt.Y("type", axis=None).title(
            "Type").sort("-x"),

        color=alt.Color("type", scale=alt.Scale(range=['#5A5A5A', '#d15353'])).title(
            "Type"),

        row=alt.Row('genre').title("Genre")).properties(height=70, width=800)

    st.altair_chart(genre)


def make_recent_archive_database(data: pd.DataFrame) -> None:
    """Makes database of human input archives."""
    st.subheader("Archives")
    # Filter out auto-scraping
    data = data[data["is_human"] == True][["url_alias", "genre", "scrape_at"]]

    st.dataframe(data)


def get_popular_screenshot(scrape_data: pd.DataFrame, interaction_data: pd.DataFrame):
    """Gets and displays the most popular sites screenshot."""
    s3_client = get_s3_client()

    if not os.path.exists("./screenshots"):
        os.makedirs("./screenshots")

    popular_website = interaction_data.groupby(['url', 'url_alias'])['url_alias'].count(
    ).reset_index(name='Count').sort_values(['Count'], ascending=False).head(1).iloc[0]

    s3_ref = scrape_data[scrape_data["url_alias"] == popular_website["url_alias"]].tail(
        1).iloc[0]['screenshot_s3_ref']

    download_data_file(
        s3_client, BUCKET, s3_ref, "screenshots")

    screenshot = Image.open(f"./screenshots/{s3_ref.replace('/', '-')}")

    st.subheader("Most Popular Site")
    # Make url fit in container
    if len(popular_website["url"]) > 35:
        website = popular_website['url'][:35] + '...'
    else:
        website = popular_website['url']
    st.text(
        f"{website}")
    #  with {popular_website['Count']} visits.
    st.image(screenshot)

    os.remove(f"./screenshots/{s3_ref.replace('/', '-')}")
