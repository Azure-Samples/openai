# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from dataclasses import dataclass
from typing import Optional


@dataclass
class DevOpsSettings:
    """
    Configuration settings for connecting to a MySQL database.

    This class holds the necessary connection parameters and retry configuration
    needed to establish and maintain a connection to a MySQL database.

    Attributes:
        server_url (str): The URL of the MySQL server.
        username (str): The username for MySQL authentication.
        password (str): The password for MySQL authentication.
        database_name (str): The name of the database to connect to.
        database_table_name (str): The name of the table within the database.
        config_file_path (str): The file path for the configuration file containing additional metadata.
        port (int, optional): The port number for the MySQL server. Default is 3306.
        connection_timeout (int, optional): Timeout for establishing a connection in seconds. Default is 10.
        max_retries (int, optional): Maximum number of retries for connection attempts. Default is 3.
    """

    server_url: str
    username: str
    password: str
    database_name: str
    database_table_name: str
    config_file_path: str
    port: Optional[int] = 3306
    connection_timeout: Optional[int] = 10
    max_retries: Optional[int] = 3
    retry_delay: Optional[int] = 2