FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim as base

WORKDIR /src

COPY skills/search/src/ /src/search
COPY common /src/search/common

RUN pip3 install --no-cache-dir --upgrade -r /src/search/requirements.txt

WORKDIR /src/search/
CMD ["hypercorn", "--bind", "0.0.0.0:6002", "app:app"]