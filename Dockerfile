FROM python:3-alpine

COPY requirements-dev.txt /tmp/

RUN pip install -r /tmp/requirements-dev.txt && \
    apk add --no-cache bash git make
