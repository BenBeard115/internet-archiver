"""API script for Internet Archiver."""

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
    jsonify)

from upload_to_s3 import (
    sanitise_filename,
    extract_title,
    extract_domain,
    upload_file_to_s3
)

load_dotenv()

app = Flask(__name__)


def save_html_css(url: str) -> str:
    """Scrape HTML and CSS from a given URL and save them."""

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    title = sanitise_filename(soup.title.text.strip())

    html_content = str(soup)
    css_content = '\n'.join([style.text for style in soup.find_all('style')])

    html_filename_temp = f"{title}_html.html"
    css_filename_temp = f"{title}_css.css"

    static_folder = os.path.join(os.getcwd(), 'static')

    with open(os.path.join(static_folder, html_filename_temp), 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

    with open(os.path.join(static_folder, css_filename_temp), 'w', encoding='utf-8') as css_file:
        css_file.write(css_content)

    return html_filename_temp, css_filename_temp


def upload_to_s3(url: str, html_filename_temp: str, css_filename_temp: str):
    """Uploads HTML and CSS to S3 bucket."""

    s3_client = client('s3',
                       aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])

    title = extract_title(url)
    url_domain = extract_domain(url)
    timestamp = datetime.utcnow().isoformat()

    html_file_to_upload = f'static/{html_filename_temp}'
    css_file_to_upload = f'static/{css_filename_temp}'

    s3_object_key_html = f'{url_domain}/{title}/{timestamp}.html'
    s3_object_key_css = f'{url_domain}/{title}/{timestamp}.css'

    upload_file_to_s3(s3_client, html_file_to_upload,
                      environ['S3_BUCKET'], s3_object_key_html)
    upload_file_to_s3(s3_client, css_file_to_upload,
                      environ['S3_BUCKET'], s3_object_key_css)

    os.remove(html_file_to_upload)
    os.remove(css_file_to_upload)

    return s3_object_key_html, s3_object_key_css


@app.route('/')
def index():
    """Main page of website."""

    url_links = [
        {"display": "Passive Loathing",
         "url": "http://www.lel.ed.ac.uk/~gpullum/passive_loathing.html"},
        {"display": "Don't make fun of renowned author Dan Brown",
         "url": "https://www.telegraph.co.uk/books/authors/dont-make-fun-of-renowned-dan-brown/"},
        {"display": "The Meteor Generation",
         "url": "https://eveninguniverse.com/fiction/the-meteor-generation.html",
         "author": "Heather Flowers"},
    ]  # What if these were loaded from a database of some kind? What then?

    # All variables passed in can be used in the template
    return render_template("index.html", heading="Home", links=url_links)



@app.route('/save/input')
def save_index():
    """Saving new website URL page."""

    return render_template('save/index.html')


@app.route('/save', methods=['POST'])
def save():
    """Allows user to input URL and save HTML and CSS."""

    url = request.form['url']

    timestamp = datetime.utcnow().isoformat()

    try:
        html_file_temp, css_data_temp = save_html_css(url)
        html_filename, css_filename = upload_to_s3(url,
                                                   html_file_temp, css_data_temp)

        response_data = {
            'url': url,
            'html_filename': html_filename,
            'css_filename': css_filename,
            'timestamp': timestamp
        }

        return jsonify(response_data)

    except Exception as e:
        error_response = {'error': str(e)}
        return jsonify(error_response), 500


# uploads RDS


if __name__ == '__main__':
    app.run(debug=True)
