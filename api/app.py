"""API script for Internet Archiver."""

import base64
from datetime import datetime
import os
from os import environ
import requests

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
    add_website
)

from connect import get_connection

from download_from_s3 import (
    get_object_keys,
    filter_keys_by_type,
    filter_keys_by_website,
    get_recent_object_keys,
    format_object_key_titles,
    get_object_from_s3
)

from chat_gpt_utils import (
    generate_summary
)

DISPLAY_SIZE = (800, 600)
IMAGE_FILE_FORMAT = '.png'
HTML_FILE_FORMAT = '.html'


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
    keys = get_recent_object_keys(s3_client, environ['S3_BUCKET'])
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
    html_keys = filter_keys_by_type(keys, '.html')
    relevant_keys = filter_keys_by_website(html_keys, input)

    for key in relevant_keys:
        pages.append({'display': key, 'filename': key})
    return pages


def upload_to_database(response_data: dict) -> None:
    """Uploads website information to the database."""
    connection = get_connection(environ)
    add_url(connection, response_data)
    add_website(connection, response_data)


@app.route('/')
def index():
    """Main page of website."""

    status = request.args.get('status')
    gpt_summary = request.args.get('summary')

    if status == 'success':
        print(gpt_summary)
        return render_template('index.html',
                               result='Save successful!',
                               gpt_summary=gpt_summary,
                               )
    elif status == 'failure':
        return render_template('index.html', result='Sorry, that webpage is not currently supported.')
    else:
        return render_template('index.html')


# Redirect to saved template page... with details
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
            'is_human': True
        }

        upload_to_database(response_data)

        return redirect(f'/?status=success&summary={gpt_summary}')

    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect('/?status=failure')


@app.route('/saved-pages', methods=['GET', 'POST'])
def view_saved_pages():
    """Allows the user to view a list of currently saved webpages."""

    if request.method == "POST":
        input = request.form.get("input")
        return redirect(f"/result/{input}")

    url_links = get_most_recently_saved_web_pages()
    return render_template("saved_pages.html", links=url_links)


@app.get("/result/<input>")
def dynamic_page(input):
    """Navigates to a page specific to what the user searched for."""

    url_links = retrieve_searched_for_pages(input)
    if len(url_links) == 0:
        return render_template("search_error.html", input=input)
    return render_template("result.html", input=input, links=url_links)


@app.get("/display-page")
def display_page():
    """Navigates to page of specific url with html embedded and download link."""

    url = request.args['display']
    html_filename = request.args['filename']
    s3_client = get_s3_client(environ)

    html_object = get_object_from_s3(
        s3_client, environ['S3_BUCKET'], html_filename)
    html_content_base64 = base64.b64encode(html_object.encode()).decode()

    return render_template('display.html', url=url, html_content=html_content_base64)


@app.route('/download/<filename>')
def download_file(filename):
    """Allows user to download archived webpage."""

    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
