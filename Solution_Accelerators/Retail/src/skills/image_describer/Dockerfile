FROM mcr.microsoft.com/mirror/docker/library/python:3.10-slim

WORKDIR /src

COPY skills/image_describer/src /src/image_describer
COPY common /src/image_describer/common

# Install node requirements
RUN pip3 install --no-cache-dir --upgrade -r /src/image_describer/requirements.txt

EXPOSE 6004

WORKDIR /src/image_describer/
CMD ["hypercorn", "--bind", "0.0.0.0:6004", "app:app"]
