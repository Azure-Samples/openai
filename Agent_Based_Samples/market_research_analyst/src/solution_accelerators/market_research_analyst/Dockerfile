FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# # Copy the market_research_analyst directory.
COPY solution_accelerators/market_research_analyst /src/market_research_analyst

# Copy the market_research_analyst entrypoint script.
# This script is responsible for starting the market research analyst service with az login.
COPY solution_accelerators/market_research_analyst/entrypoint.sh /src/market_research_analyst/entrypoint.sh
RUN chmod +x /src/market_research_analyst/entrypoint.sh

# Copy the common module directory.
COPY common /src/market_research_analyst/common

# # Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/market_research_analyst/requirements.txt

EXPOSE 6000

CMD ["/src/market_research_analyst/entrypoint.sh"]