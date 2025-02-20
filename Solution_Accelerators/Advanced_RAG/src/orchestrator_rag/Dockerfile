FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim
WORKDIR /src

# Copy the orchestrator_rag directory.
COPY orchestrator_rag /src/orchestrator_rag

# Copy the common module directory.
COPY common /src/orchestrator_rag/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/orchestrator_rag/requirements.txt

# Set the working directory and command to run the app.
WORKDIR /src/orchestrator_rag
CMD ["hypercorn", "--bind", "0.0.0.0:5002", "run:app"]