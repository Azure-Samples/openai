FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# # Copy the sales_analyst/orchestrator directory.
COPY solution_accelerators/sales_analyst/orchestrator /src/sales_analyst/orchestrator

# This script is responsible for starting the Sales Analyst service with az login.
COPY solution_accelerators/sales_analyst/orchestrator/entrypoint.sh /src/sales_analyst/orchestrator/entrypoint.sh
RUN chmod +x /src/sales_analyst/orchestrator/entrypoint.sh

# Copy the common module directory.
COPY common /src/sales_analyst/orchestrator/common

# # Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/sales_analyst/orchestrator/requirements.txt

EXPOSE 5102

CMD ["/src/sales_analyst/orchestrator/entrypoint.sh"]