"""API script for Internet Archiver."""

import base64
from datetime import datetime, timedelta
import os
from os import environ
import requests
from connect import get_connection

from boto3 import client
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_from_directory
)
from html2image import Html2Image

from upload_to_s3 import (
    extract_title,
    extract_domain,
    get_s3_client
)

from upload_to_database import (
    add_url,
    add_website,
    add_interaction
)

from extract_from_database import (
    get_connection,
    get_url,
    get_most_popular_urls,
    get_summary_from_db,
    get_genre_from_db,
    get_first_submission_time,
    get_number_of_views,
    get_number_of_saves,
    get_recent_png_key_s3,
    get_png_keys_s3
)

from download_from_s3 import (
    get_object_keys,
    filter_keys_by_type,
    filter_keys_by_website,
    get_recent_png_s3_keys,
    get_recent_html_s3_keys,
    format_object_key_titles,
    get_object_from_s3,
    download_data_file,
    get_all_pages_ordered,
    get_all_screenshots,
    get_scrape_times,
    format_timestamps,
    get_most_recent_png_key,
    get_most_recently_saved_web_pages,
    retrieve_searched_for_pages
)

from chat_gpt_utils import (
    generate_summary,
    get_genre
)

DISPLAY_SIZE = (800, 600)
IMAGE_FILE_FORMAT = '.png'
HTML_FILE_FORMAT = '.html'
NUM_OF_SITES_HOMEPAGE = 12
IMG_FOLDER = os.path.join(os.getcwd(), 'static', 'img')
STATIC_FOLDER = os.path.join(os.getcwd(), 'static')
USER_FRIENDLY_FORMAT = "%d %B %Y - %I:%M %p"


load_dotenv()

hti = Html2Image()

app = Flask(__name__)


def get_soup(url: str) -> BeautifulSoup:
    """Gets Soup object from url."""

    response = requests.get(url)
    response.raise_for_status()

    return BeautifulSoup(response.content, 'html.parser')


def process_html_content(soup: BeautifulSoup,
                         domain: str,
                         title: str,
                         timestamp: str,
                         s3_client: client) -> str:
    """Uploads the html content as a file to the S3 bucket, given a specific url soup."""

    filename_string = f"{domain}/{title}/{timestamp}"
    html_object_key = f"{filename_string}{HTML_FILE_FORMAT}"

    html_content = soup.prettify()

    s3_client.put_object(
        Body=html_content, Bucket=environ['S3_BUCKET'], Key=html_object_key)

    return html_object_key


def process_screenshot(url: str,
                       domain: str,
                       title: str,
                       timestamp: str,
                       s3_client: client) -> None:
    """Takes screenshot of webpage and uploads to S3."""

    img_filename_string = f"{domain}_{title}_{timestamp}"
    img_object_key = f"{img_filename_string}{IMAGE_FILE_FORMAT}"

    filename_string = f"{domain}/{title}/{timestamp}"
    img_object_key_s3 = f"{filename_string}{IMAGE_FILE_FORMAT}"

    hti.screenshot(url=url,
                   size=DISPLAY_SIZE,
                   save_as=img_object_key)

    s3_client.upload_file(
        img_object_key, environ['S3_BUCKET'], img_object_key_s3)

    os.remove(img_object_key)

    return img_object_key_s3


def upload_scrape_to_database(response_data: dict) -> None:
    """Uploads website information to the database."""
    connection = get_connection(environ)
    add_url(connection, response_data)
    add_website(connection, response_data)


def upload_interaction_to_database(interaction_data: dict):
    connection = get_connection(environ)
    add_url(connection, interaction_data)
    add_interaction(connection, interaction_data)


def convert_iso_to_datetime(dt_str: str) -> datetime:
    """Converts ISO string to datetime."""
    dt, _, us = dt_str.partition(".")
    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    us = int(us.rstrip("Z"), 10)

    return dt + timedelta(microseconds=us)


@app.route('/')
def index():
    """First page of the website."""

    return render_template('index.html')


@app.route('/submit')
def submit():
    """End point to submit a story."""

    s3_client = get_s3_client(environ)
    connection = get_connection(environ)

    s3_refs = get_most_recently_saved_web_pages()
    pages = []
    s3_refs_set = set(s3_refs)

    for s3_ref in s3_refs_set:
        png_key = get_most_recent_png_key(s3_client, environ['S3_BUCKET'], s3_ref)
        url = get_url(s3_ref, connection)

        if png_key == 'No Relevant Keys':
            return render_template('archived_pages.html')

        image_filename = download_data_file(
            s3_client, environ['S3_BUCKET'], png_key, 'static')
        screenshot_label = png_key.split(
            '/')[0] + '/' + png_key.split('/')[1]

        pages.append({'url': url, 'image_filename': image_filename, "label": screenshot_label})

    return render_template("submit.html", pages=pages, input=input)


@app.route('/save', methods=['POST'])
def save():
    """Allows user to input URL and save HTML and CSS."""

    connection = get_connection(environ)

    url = request.form['url']
    timestamp = datetime.utcnow().isoformat()

    try:

        soup = get_soup(url)

        domain = extract_domain(url)
        title = extract_title(url)
        timestamp = datetime.utcnow().isoformat()

        s3_client = get_s3_client(environ)

        html_object_key = process_html_content(
            soup, domain, title, timestamp, s3_client)
        img_object_key_s3 = process_screenshot(
            url, domain, title, timestamp, s3_client)

        gpt_summary = generate_summary(str(soup))
        webpage_genre = get_genre(str(soup))
        print(f"WEBPAGE GENRE (AT SUBMIT): {webpage_genre}")

        response_data = {
            'url': url,
            'html_s3_ref': html_object_key,
            'css_s3_ref': 'css_data',
            'screenshot_s3_ref': img_object_key_s3,
            'scrape_at': timestamp,
            'summary': gpt_summary,
            'is_human': True,
            'genre': webpage_genre
        }

        upload_scrape_to_database(response_data)

        timestamp = convert_iso_to_datetime(timestamp).replace(microsecond=0)

        interaction_data = {
            'url': url,
            'type': 'save',
            'interact_at': timestamp
        }

        upload_interaction_to_database(interaction_data)

        print(f"Upload successful: {interaction_data}")

        first_submitted = get_first_submission_time(url, connection)
        number_of_views = get_number_of_views(url, connection)
        number_of_saves = get_number_of_saves(url, connection)

        return render_template('page_history.html',
                               img_filename=img_object_key_s3,
                               html_filename=html_object_key,
                               url=url,
                               timestamp=timestamp,
                               gpt_summary=gpt_summary,
                               genre=webpage_genre,
                               first_submitted=first_submitted,
                               number_of_views=number_of_views,
                               number_of_saves=number_of_saves
                               )

    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect('/submit?status=failure')


@app.route('/archived-pages', methods=['GET', 'POST'])
def view_archived_pages():
    """Allows the user to view a list of currently saved webpages."""

    if request.method == "POST":
        input = request.form.get("input")
        return redirect(f"/result/{input}")

    s3_client = get_s3_client(environ)
    connection = get_connection(environ)

    urls = get_most_popular_urls(connection)
    pages = []
    for url in urls:
        png_key = get_recent_png_key_s3(connection, url)
        image_filename = download_data_file(
            s3_client, environ['S3_BUCKET'], png_key, 'static')
        screenshot_label = png_key.split(
            '/')[0] + '/' + png_key.split('/')[1]

        pages.append(
            {'url': url, 'image_filename': image_filename, "label": screenshot_label})

    return render_template('archived_pages.html', pages=pages)


@app.get("/result/<input>")
def dynamic_page(input):
    """Navigates to a page specific to what the user searched for."""

    s3_client = get_s3_client(environ)
    connection = get_connection(environ)
    s3_refs = retrieve_searched_for_pages(s3_client, input)

    if len(s3_refs) == 0:
        return render_template("search_error.html", input=input)

    pages = []
    s3_refs_set = set(s3_refs)

    for s3_ref in s3_refs_set:
        png_key = get_most_recent_png_key(s3_client, environ['S3_BUCKET'], s3_ref)
        url = get_url(s3_ref, connection)

        if png_key == 'No Relevant Keys':
            return render_template('archived_pages.html')
    
        image_filename = download_data_file(
            s3_client, environ['S3_BUCKET'], png_key, 'static')
        screenshot_label = png_key.split(
            '/')[0] + '/' + png_key.split('/')[1]

        pages.append({'url': url, 'image_filename': image_filename, "label": screenshot_label})
    
    return render_template("result.html", pages=pages, input=input)


@app.route('/page-history')
def display_page_history():
    """Page which displays all previous captures of a page."""

    s3_client = get_s3_client(environ)
    connection = get_connection(environ)

    url = request.args.get('url')

    png_files = get_png_keys_s3(connection, url)
    html_files = [png_file.replace(
        '.png', '.html', ) for png_file in png_files]

    local_screenshot_files = []
    screenshot_labels = []
    timestamps = []
    for scrape in png_files:
        local_filename = download_data_file(
            s3_client, environ['S3_BUCKET'], scrape, 'static')

        local_screenshot_files.append(local_filename)
        screenshot_labels.append(scrape.split(
            '/')[0] + '/' + scrape.split('/')[1])

        timestamp = scrape.split('/')[-1].replace('.png', '')
        timestamps.append(timestamp)

    html_key = html_files[0]
    screenshot_label = html_key.split(
            '/')[0] + '/' + scrape.split('/')[1]

    gpt_summary = get_summary_from_db(html_key, connection)
    webpage_genre = get_genre_from_db(url, connection)
    first_submitted = get_first_submission_time(url, connection)
    number_of_views = get_number_of_views(url, connection)
    number_of_saves = get_number_of_saves(url, connection)


    img_files = get_all_screenshots(html_files)

    scrape_times = get_scrape_times(html_files)
    formatted_ts = format_timestamps(scrape_times)

    pages = zip(html_files, img_files, formatted_ts)

    timestamp = datetime.utcnow().isoformat()
    timestamp = convert_iso_to_datetime(timestamp).replace(microsecond=0)
    print(timestamp, type(timestamp))

    interaction_data = {
        'url': url,
        'type': 'visit',
        'interact_at': timestamp
    }

    print(interaction_data)

    upload_interaction_to_database(interaction_data)

    print(f"WEBPAGE GENRE (WHEN VIEWING): {webpage_genre}")

    return render_template('page_history.html',
                           pages=pages,
                           url=url,
                           screenshot_label=screenshot_label,
                           gpt_summary=gpt_summary,
                           genre=webpage_genre,
                           first_submitted=first_submitted,
                           number_of_views=number_of_views,
                           number_of_saves=number_of_saves)


@app.get("/display-page")
def display_page_instance():
    """Navigates to page of specific url with html embedded and download link."""

    url = request.args.get('url')
    html_key = request.args.get('html_file')
    timestamp = request.args.get('timestamp')

    s3_client = get_s3_client(environ)

    html_object = get_object_from_s3(
        s3_client, environ['S3_BUCKET'], html_key)
    html_content_base64 = base64.b64encode(html_object.encode()).decode()

    return render_template('display_page_instance.html',
                           html_content=html_content_base64,
                           url=url,
                           timestamp=timestamp)


@app.route('/download/<filename>')
def download_file(filename):
    """Allows user to download archived webpage."""

    return send_from_directory('static', filename)


@app.route('/limitations')
def limitations():
    """Renders the web page that states the limitations of our application at its current stage."""

    return render_template('limitations.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
