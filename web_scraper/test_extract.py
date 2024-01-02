"""Unit tests for the extract.py file."""
import os
from unittest.mock import MagicMock, patch

import pytest

from extract import load_all_data, convert_to_set


@patch.dict(os.environ, {"SCRAPE_TABLE_NAME": "x", "URL_TABLE_NAME": "y"})
def test_load_url_data_raise_error_when_empty():
    """Tests that execute is called once when loading the data."""

    mock_connection = MagicMock()
    with pytest.raises(ValueError):
        load_all_data(mock_connection)

def test_convert_to_set_removes_duplicates():
    """Tests that when converted to a set, all duplicate values in list ae removed."""

    urls = ['https://www.google.co.uk','https://www.youtube.co.uk', 'https://www.youtube.co.uk']
    assert convert_to_set(urls) == {
        'https://www.google.co.uk', 'https://www.youtube.co.uk'}

