FROM python:3.6-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apk update && apk add git && rm -rf /var/cache/apk/* && mkdir upload_folder

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY . .

CMD python client.py
