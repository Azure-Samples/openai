FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim
WORKDIR /src

# Copy the source code.
COPY tests/e2e_test_agent /src/e2e_test_agent

# Copy the common module directory.
COPY common /src/e2e_test_agent/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/e2e_test_agent/requirements.txt

# Expose the port.
EXPOSE 5051

# Set the working directory and command to run the app.
WORKDIR /src/e2e_test_agent
CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:5051"]