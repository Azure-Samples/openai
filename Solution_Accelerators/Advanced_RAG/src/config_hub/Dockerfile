FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim
WORKDIR /src

# Copy the config_hub directory.
COPY config_hub /src/config_hub

# Copy the common module directory.
COPY common /src/config_hub/common

# install dependencies
RUN pip install --no-cache-dir --upgrade -r /src/config_hub/requirements.txt

EXPOSE 5003

# Set the working directory and command to run the app.
WORKDIR /src/config_hub
CMD ["hypercorn", "--bind", "0.0.0.0:5003", "app:app"]