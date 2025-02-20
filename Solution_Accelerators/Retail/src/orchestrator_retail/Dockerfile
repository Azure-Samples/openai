FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim
WORKDIR /src

# Copy the orchestrator_retail directory.
COPY orchestrator_retail /src/orchestrator_retail

# Copy the common module directory.
COPY common /src/orchestrator_retail/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/orchestrator_retail/requirements.txt

# Set the working directory and command to run the app.
WORKDIR /src/orchestrator_retail
CMD ["hypercorn", "--bind", "0.0.0.0:5102", "run:app"]