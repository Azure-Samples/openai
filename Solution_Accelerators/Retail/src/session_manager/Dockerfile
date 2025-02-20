FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim
WORKDIR /src

# Copy the session_manager directory.
COPY session_manager /src/session_manager

# Copy the common module directory.
COPY common /src/session_manager/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/session_manager/requirements.txt

EXPOSE 5000

# Set the working directory and command to run the app.
WORKDIR /src/session_manager
CMD [ "python", "-u", "app.py" ]