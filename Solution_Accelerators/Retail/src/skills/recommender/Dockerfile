FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim

WORKDIR /src

COPY skills/recommender/src /src/recommender
COPY common /src/recommender/common

# Install node requirements
RUN pip3 install --no-cache-dir --upgrade -r /src/recommender/requirements.txt

EXPOSE 6003

WORKDIR /src/recommender/
CMD ["hypercorn", "--bind", "0.0.0.0:6003", "app:app"]
