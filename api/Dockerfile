FROM python:latest

RUN apt-get update -y && apt-get install -y chromium dbus

WORKDIR /api

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY download_from_s3.py .
COPY extract_from_database.py .
COPY upload_to_database.py .
COPY upload_to_s3.py .
COPY connect.py .
COPY chat_gpt_utils.py .

COPY templates/ /api/templates/
COPY static /api/static

COPY app.py .

CMD python app.py