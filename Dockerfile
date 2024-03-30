# https://stackoverflow.com/questions/56104183/how-do-i-get-python2-7-and-3-7-both-installed-in-an-alpine-docker-image
FROM python:3-alpine3.15

COPY requirements-dev.txt /tmp/

RUN apk add --no-cache bash git less make && \
    python3 -m pip install -r /tmp/requirements-dev.txt
