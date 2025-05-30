FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# # Copy the release_manager directory.
COPY solution_accelerators/release_manager /src/release_manager

# Copy the release_manager entrypoint script.
# This script is responsible for starting the release manager service with az login.
COPY solution_accelerators/release_manager/entrypoint.sh /src/release_manager/entrypoint.sh
RUN chmod +x /src/release_manager/entrypoint.sh

# Copy the common module directory.
COPY common /src/release_manager/common

# # Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/release_manager/requirements.txt

EXPOSE 6000

CMD ["/src/release_manager/entrypoint.sh"]