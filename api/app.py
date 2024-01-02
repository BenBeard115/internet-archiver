"""API script for Internet Archiver."""

import os
import requests
from datetime import datetime

from bs4 import BeautifulSoup
from flask import (
    Flask,
    render_template,
    request,
    jsonify)


app = Flask(__name__)


def save_html_css(url):
    """Scrape HTML and CSS from a given URL and save them."""

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.title.text.strip()

    html_content = str(soup)
    css_content = '\n'.join([style.text for style in soup.find_all('style')])

    html_filename = f"{title}_html.html"
    css_filename = f"{title}_css.css"

    static_folder = os.path.join(os.getcwd(), 'static')

    with open(os.path.join(static_folder, html_filename), 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

    with open(os.path.join(static_folder, css_filename), 'w', encoding='utf-8') as css_file:
        css_file.write(css_content)

    return html_filename, css_filename


@app.route('/')
def index():
    """Main page of website."""

    return render_template('index.html')


@app.route('/save/index.html')
def save_index():
    """Saving new website URL page."""

    return render_template('save/index.html')


@app.route('/save', methods=['POST'])
def save():
    """Allows user to input URL and save HTML and CSS."""

    # Gets input URL from user form
    url = request.form['url']

    timestamp = datetime.utcnow().isoformat()

    try:
        html_filename, css_filename = save_html_css(url)

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
