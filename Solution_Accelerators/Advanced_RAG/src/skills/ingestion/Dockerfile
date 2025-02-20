FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim

WORKDIR /src

COPY skills/ingestion/ /src/ingestion
COPY common /src/ingestion/common

RUN pip3 install --no-cache-dir --upgrade -r /src/ingestion/requirements.txt

EXPOSE 6001

WORKDIR /src/ingestion/
CMD ["python", "app.py"]