"""Unit tests for the load.py file."""

from pytest import raises

from load import sanitise_filename, extract_title, extract_domain

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
    """Tests that extract_title successfully returns None when an invalid link is given in the correct format."""

    test_input = "https:///www.invalid.com"

    assert extract_title(test_input) == None


def test_extract_domain_valid_easy():
    """Tests that extract_domain successfully grabs the domain when a valid link is given."""

    test_input = "https://www.youtube.co.uk"

    assert extract_domain(test_input) == "www.youtube.co.uk"


def test_extract_domain_valid_hard():
    """Tests that extract_domain successfully grabs the domain when a valid but weird link is given."""

    test_input = "cargo.go"

    assert extract_domain(test_input) == "cargo.go"


def test_extract_domain_invalid():
    """Tests that extract_domain doesn't grab anything when an invalid url is given."""

    test_input = "hello this shouldn't work.no"

    assert extract_domain(test_input) == None