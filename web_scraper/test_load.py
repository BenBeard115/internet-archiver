"""Unit tests for the load.py file."""
from unittest.mock import MagicMock

from pytest import raises
from botocore.exceptions import ClientError

from load import sanitise_filename, extract_title, extract_domain, upload_file_to_s3

def test_sanitise_filename_works():
    """Tests that sanitise_filename successfully removes the correct characters."""

    test_input = "H@l!@£$%£$^$oojns"

    assert sanitise_filename(test_input) == "H l         oojns"


def test_sanitise_filename_empty():
    """Tests that sanitise_filename doesn't change anything in an empty string."""

    test_input = ""

    assert sanitise_filename(test_input) == ""


def test_sanitise_filename_number():
    """Tests that sanitise_filename doesn't throw an error when given an number input."""

    test_input = 123

    assert sanitise_filename(test_input) == "123"


def test_sanitise_filename_list_and_hard():
    """Tests that sanitise_filename doesn't throw an error when given a fully invalid input."""

    test_input = ["hi", "this", "should", "work", "still"]

    assert sanitise_filename(test_input) == "  hi    this    should    work    still  "


def test_extract_title_valid():
    """Tests that extract_title successfully extracts the title."""

    test_input = "https://www.youtube.co.uk"

    assert extract_title(test_input) == "YouTube"


def test_extract_title_invalid():
    """Tests that extract_title successfully throws an error when an invalid link is given."""

    test_input = "invalid"

    with raises(ValueError):
        extract_title(test_input)


def test_extract_title_invalid_link():
    """Tests that extract_title successfully returns None when an
    invalid link is given in the correct format."""

    test_input = "https:///www.invalid.com"

    assert extract_title(test_input) is None


def test_extract_domain_valid_easy():
    """Tests that extract_domain successfully grabs the domain when a valid link is given."""

    test_input = "https://www.youtube.co.uk"

    assert extract_domain(test_input) == "www.youtube.co.uk"


def test_extract_domain_valid_hard():
    """Tests that extract_domain successfully grabs the domain
    when a valid but weird link is given."""

    test_input = "cargo.go"

    assert extract_domain(test_input) == "cargo.go"


def test_upload_to_s3_successful():
    """Tests that upload_to_s3 successfully uploads."""

    s3_client_mock = MagicMock()

    filename = "test.html"
    bucket = "test_bucket"
    key = "test_key"

    upload_file_to_s3(s3_client_mock, filename, bucket, key)

    s3_client_mock.upload_file.assert_called_once()


def test_upload_to_s3_client_error(capsys):
    """Tests that upload_to_s3 produces a print statement when a ClientError occurs."""

    s3_client_mock = MagicMock()
    s3_client_mock.upload_file.side_effect = ClientError({}, "")

    filename = "test.html"
    bucket = "test_bucket"
    key = "test_key"

    upload_file_to_s3(s3_client_mock, filename, bucket, key)

    s3_client_mock.upload_file.assert_called_once()
    assert "Unable to upload file. Please check details of client!" in capsys.readouterr().out


def test_upload_to_s3_type_error(capsys):
    """Tests that upload_to_s3 produces a print statement when a TypeError occurs."""

    s3_client_mock = MagicMock()
    s3_client_mock.upload_file.side_effect = TypeError()

    filename = "test.html"
    bucket = "test_bucket"
    key = "test_key"

    upload_file_to_s3(s3_client_mock, filename, bucket, key)

    s3_client_mock.upload_file.assert_called_once()
    assert ("Unable to upload file. Missing parameters required for upload!\n"
            in capsys.readouterr().out)
