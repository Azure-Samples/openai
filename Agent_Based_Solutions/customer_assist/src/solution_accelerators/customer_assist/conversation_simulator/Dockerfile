FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# # Copy the customer_assist/conversation_simulator directory.
COPY solution_accelerators/customer_assist/conversation_simulator /src/customer_assist/conversation_simulator

# Make sure data directory exists with proper permissions
RUN mkdir -p /src/customer_assist/conversation_simulator/data/verification_documents && \
    chmod -R 755 /src/customer_assist/conversation_simulator/data

# Copy the conversation simulator entrypoint script.
# This script is responsible for starting the conversation simulator service with az login.
COPY solution_accelerators/customer_assist/conversation_simulator/entrypoint.sh /src/customer_assist/conversation_simulator/entrypoint.sh
RUN chmod +x /src/customer_assist/conversation_simulator/entrypoint.sh

# Copy the common module directory.
COPY common /src/customer_assist/conversation_simulator/common

# # Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/customer_assist/conversation_simulator/requirements.txt

# Set environment variables
ENV DOCKER_CONTAINER=true
ENV SERVICE_HOST=0.0.0.0
ENV SERVICE_PORT=6001

EXPOSE 6001

CMD ["/src/customer_assist/conversation_simulator/entrypoint.sh"]