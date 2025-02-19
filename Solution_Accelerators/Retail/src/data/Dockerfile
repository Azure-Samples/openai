FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim
WORKDIR /src

# Copy the data directory.
COPY data /src/data

# Copy the common module directory.
COPY common /src/data/common

# install dependencies
RUN pip install --no-cache-dir --upgrade -r /src/data/requirements.txt

EXPOSE 5001

# Set the working directory and command to run the app.
WORKDIR /src/data
CMD [ "python", "-u", "app.py" ]