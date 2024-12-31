FROM python:3.12-slim

WORKDIR /app

COPY locale /app/locale
COPY source /app/source
COPY static/XHS-Downloader.tcss /app/static/XHS-Downloader.tcss
COPY LICENSE /app/LICENSE
COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

VOLUME /app

EXPOSE 8000
