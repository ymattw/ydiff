FROM python:3-alpine3.19

COPY requirements-dev.txt /tmp/

RUN apk add --no-cache bash git less make && \
    python3 -m pip install -r /tmp/requirements-dev.txt
