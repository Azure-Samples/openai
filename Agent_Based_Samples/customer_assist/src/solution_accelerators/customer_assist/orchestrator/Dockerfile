FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# # Copy the customer_assist/orchestrator directory.
COPY solution_accelerators/customer_assist/orchestrator /src/customer_assist/orchestrator

# This script is responsible for starting the Customer Assist Orchetrator service with az login.
COPY solution_accelerators/customer_assist/orchestrator/entrypoint.sh /src/customer_assist/orchestrator/entrypoint.sh
RUN chmod +x /src/customer_assist/orchestrator/entrypoint.sh

# Copy the common module directory.
COPY common /src/customer_assist/orchestrator/common

# # Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/customer_assist/orchestrator/requirements.txt

EXPOSE 5102

CMD ["/src/customer_assist/orchestrator/entrypoint.sh"]