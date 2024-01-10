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
    get_most_popular_urls
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
    get_relevant_html_keys_for_url,
    get_relevant_png_keys_for_url
)

from chat_gpt_utils import (
    generate_summary
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


def get_most_recently_saved_web_pages() -> dict:
    """Get the most recently saved web pages to display on the website."""
    pages = []
    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])
    keys = get_recent_png_s3_keys(s3_client, environ['S3_BUCKET'])
    titles = format_object_key_titles(keys)
    for title in titles:
        pages.append({'display': title, 'url': None})
    print(pages)
    return pages


def retrieve_searched_for_pages(input: str):
    """Get the relevant pages that have been searched for."""
    pages = []
    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])
    keys = get_object_keys(s3_client, environ['S3_BUCKET'])
    if keys is None:
        return 'Empty Database!'

    html_keys = filter_keys_by_type(keys, '.html')
    relevant_keys = filter_keys_by_website(html_keys, input)

    for key in relevant_keys:
        pages.append({'display': key, 'filename': key})
    return pages


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
    """Main page of website."""

    # do we still need these?
    status = request.args.get('status')
    gpt_summary = request.args.get('summary')
    url = request.args.get('url')
    timestamp = request.args.get('timestamp')
    #

    s3_client = get_s3_client(environ)
    connection = get_connection(environ)

    recent_screenshots = get_recent_png_s3_keys(
        s3_client, environ['S3_BUCKET'], NUM_OF_SITES_HOMEPAGE)

    recent_html_files = [screenshot.replace(
        '.png', '.html') for screenshot in recent_screenshots]

    urls = [get_url(html, connection) for html in recent_html_files]
    print(urls)

    local_screenshot_files = []
    screenshot_labels = []
    timestamps = []
    for scrape in recent_screenshots:
        local_filename = download_data_file(
            s3_client, environ['S3_BUCKET'], scrape, 'static')
        if local_filename is None:
            return render_template('submit.html')

        local_screenshot_files.append(local_filename)
        screenshot_labels.append(scrape.split(
            '/')[0] + '/' + scrape.split('/')[1])

        timestamp = scrape.split('/')[-1].replace('.png', '')
        timestamps.append(timestamp)

    page_info = zip(local_screenshot_files,
                    screenshot_labels,
                    timestamps,
                    recent_html_files,
                    urls)

    return render_template('submit.html', page_info=page_info)


@app.route('/save', methods=['POST'])
def save():
    """Allows user to input URL and save HTML and CSS."""

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
        print(gpt_summary)

        response_data = {
            'url': url,
            'html_s3_ref': html_object_key,
            'css_s3_ref': 'css_data',
            'screenshot_s3_ref': img_object_key_s3,
            'scrape_at': timestamp,
            'summary': gpt_summary,
            'is_human': True,
            'genre': ''
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

        # return redirect(f'/?status=success&summary={gpt_summary}&url={url}&timestamp={timestamp}')

        return render_template('page_history.html',
                               img_filename=img_object_key_s3,
                               html_filename=html_object_key,
                               url=url,
                               timestamp=timestamp,
                               gpt_summary=gpt_summary)

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
    print(f"URLS: {urls}")
    popular_screenshots = []
    for url in urls:
        relevant_keys = get_relevant_png_keys_for_url(
            s3_client, environ['S3_BUCKET'], url)

        popular_screenshots += relevant_keys

    print(f"POPULAR SCREENSHOTS: {popular_screenshots}")

    popular_html_files = [png_file.replace(
        '.png', '.html', ) for png_file in popular_screenshots]

    local_screenshot_files = []
    screenshot_labels = []
    timestamps = []
    for scrape in popular_screenshots:
        local_filename = download_data_file(
            s3_client, environ['S3_BUCKET'], scrape, 'static')

        local_screenshot_files.append(local_filename)
        screenshot_labels.append(scrape.split(
            '/')[0] + '/' + scrape.split('/')[1])

        timestamp = scrape.split('/')[-1].replace('.png', '')
        timestamps.append(timestamp)

    page_info = zip(local_screenshot_files,
                    screenshot_labels,
                    timestamps,
                    popular_html_files,
                    urls)

    return render_template('archived_pages.html', page_info=page_info)


@app.get("/result/<input>")
def dynamic_page(input):
    """Navigates to a page specific to what the user searched for."""

    url_links = retrieve_searched_for_pages(input)
    if len(url_links) == 0:
        return render_template("search_error.html", input=input)
    return render_template("result.html", input=input, links=url_links)


@app.route('/page-history')
def display_page_history():
    """Page which displays all previous captures of a page."""

    s3_client = get_s3_client(environ)

    local_img_filename = request.args.get('local_img_filename')
    screenshot_label = request.args.get('screenshot_label')
    timestamp = request.args.get('timestamp')
    html_key = request.args.get('html_key')
    url = request.args.get('url')

    print(local_img_filename)
    print(screenshot_label)
    print(timestamp)
    print(html_key)
    print(url)

    html_files = get_all_pages_ordered(
        s3_client, html_key, environ['S3_BUCKET'])

    img_files = get_all_screenshots(html_files)

    scrape_times = get_scrape_times(html_files)
    formatted_ts = format_timestamps(scrape_times)

    pages = zip(html_files, img_files, formatted_ts)

    timestamp = convert_iso_to_datetime(timestamp).replace(microsecond=0)
    print(timestamp, type(timestamp))

    interaction_data = {
        'url': url,
        'type': 'visit',
        'interact_at': timestamp
    }

    print(interaction_data)

    upload_interaction_to_database(interaction_data)

    return render_template('page_history.html',
                           pages=pages,
                           url=url,
                           screenshot_label=screenshot_label)


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
