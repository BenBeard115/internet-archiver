FROM python:latest

RUN apt-get update -y && apt-get install -y chromium dbus

RUN mkdir -p /run/dbus
RUN dbus-daemon --system

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY extract.py .
COPY load.py .
COPY pipeline.py .

CMD python3 pipeline.py