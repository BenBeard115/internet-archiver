# The Internet Archiver API (working README)

This API allows you to scrape and save the HTML and CSS of a webpage from a given URL.


## 🗂️ Folder Structure
This subfolder is structured as follows:

- `app.py`: This is the main script for the API.
- `templates/`: This folder contains the HTML templates for the website.
- `static/`: This folder contains the saved HTML and CSS files, as well as the styles.css file.


## 🚀 Usage
The API uses the following routes:

- `/`: This route serves the main page of the website.
- `/save`: This route allows users to input a URL and saves the corresponding HTML and CSS. It accepts POST requests with a form data object containing a 'url' field.


