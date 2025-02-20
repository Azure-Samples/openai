#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import os

from dotenv import load_dotenv

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

# load value from .debug.env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.path.dirname(__file__)}/.debug.env")


class ConfigReader:
    def __init__(self) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Set the formatter for the console handler
        formatter = logging.Formatter("%(asctime)s: %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")
        console_handler.setFormatter(formatter)

        # Add the console handler to the logger
        logger.addHandler(console_handler)

        self.logger = logger

    def set_logger(self, logger):
        self.logger = logger

    def read_config_value(self, key_name: str) -> str:
        return self._get_config_value(key_name)

    def _get_config_value(self, key_name: str) -> str:

        value = os.getenv(key_name)

        if value is None:
            if self.logger:
                self.logger.error(f"Necessary value {value} couldn't be found in environment")
            raise Exception(f"Necessary value {value} couldn't be found in environment")
        return value


class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader()
            cls.logger = config_reader.logger

            try:
                cls.SESSION_MANAGER_URL = config_reader.read_config_value("SESSION-MANAGER-URL")
                cls.TEST_CASE_SCENARIO = config_reader.read_config_value("TEST-CASE-SCENARIO")
                cls._initialized = True

            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e
