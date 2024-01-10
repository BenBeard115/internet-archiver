FROM python:latest

WORKDIR dashboard

COPY archive_image.png .
COPY requirements.txt .

RUN mkdir ./screenshots
RUN pip3 install -r requirements.txt

EXPOSE 8501

COPY extract.py .
COPY donwload_screenshot.py .
COPY dashboard_functions.py .
COPY dashboard.py .

COPY .streamlit/ ./.streamlit/

CMD streamlit run dashboard.py --server.port 8501