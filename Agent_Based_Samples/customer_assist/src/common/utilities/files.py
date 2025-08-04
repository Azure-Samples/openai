# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import json
import yaml
import requests
from urllib.parse import urlparse, unquote
from common.exceptions import FileDownloadError, FileProcessingError


def load_file(filepath: str, filetype: str) -> dict:
    try:
        with open(filepath, "r") as f:
            if filetype == "json":
                return json.load(f)
            elif filetype == "yaml" or filetype == "yml":
                return yaml.safe_load(f)
            else:
                raise FileProcessingError(f"Filetype {filetype} not supported")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise FileProcessingError(
            f"Failed to parse the local file content. Error: {str(e)}"
        )
    except Exception as e:
        raise FileProcessingError(f"Failed to load the local file. Error: {str(e)}")


def download_file_from_sas_url(sas_url: str) -> str:
    try:
        response = requests.get(sas_url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise FileDownloadError(
            f"Failed to download the file from SAS URL: {sas_url}. Error: {str(e)}"
        )


def determine_file_extension(sas_url: str) -> str:
    try:
        parsed_url = urlparse(sas_url)
        file_name = os.path.basename(parsed_url.path)
        file_name = unquote(file_name)
        return os.path.splitext(file_name)[1].lower()
    except Exception as e:
        raise FileProcessingError(f"Error processing the URL or file name: {str(e)}")


def parse_file_content(file_content: str, file_extension: str) -> dict:
    try:
        if file_extension == ".json":
            return json.loads(file_content)
        elif file_extension in (".yaml", ".yml"):
            return yaml.safe_load(file_content)
        else:
            raise FileProcessingError(f"Unsupported file extension: {file_extension}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise FileProcessingError(f"Failed to parse the file content. Error: {str(e)}")
    except Exception as e:
        raise FileProcessingError(
            f"Unexpected error during file parsing. Error: {str(e)}"
        )


def load_file_from_sas_url(sas_url: str) -> dict:
    file_content = download_file_from_sas_url(sas_url)
    file_extension = determine_file_extension(sas_url)
    return parse_file_content(file_content, file_extension)
