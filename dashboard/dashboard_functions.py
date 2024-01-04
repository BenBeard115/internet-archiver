"""Script containing functions to make the graphs on the dashboard."""

from os import environ

from dotenv import load_dotenv
import pandas as pd
import altair as alt
import streamlit as st


def make_hourly_archive_tracker_line(data: pd.DataFrame):
    st.subheader("Websites Archived")

    archived = alt.Chart(data).mark_line().encode(
        x=alt.X("hours(at):O").title("Time"),
        y=alt.Y("count(url):Q").title("Archives"))

    st.altair_chart(archived, use_container_width=True)
