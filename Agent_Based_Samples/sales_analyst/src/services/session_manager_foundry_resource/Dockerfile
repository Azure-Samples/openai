FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# Copy the session_manager_foundry_resource directory.
COPY services/session_manager_foundry_resource /src/session_manager_foundry_resource

# Copy the session_manager_foundry_resource entrypoint script.
# This script is responsible for starting the session manager service with az login.
COPY services/session_manager_foundry_resource/entrypoint.sh /src/session_manager_foundry_resource/entrypoint.sh
# Fix line endings and ensure script is executable
RUN sed -i 's/\r$//' /src/session_manager_foundry_resource/entrypoint.sh && \
    chmod +x /src/session_manager_foundry_resource/entrypoint.sh

# Copy the common module directory.
COPY common /src/session_manager_foundry_resource/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/session_manager_foundry_resource/requirements.txt

EXPOSE 5000

CMD ["/src/session_manager_foundry_resource/entrypoint.sh"]