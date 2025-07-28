# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from contextlib import contextmanager
from typing import Optional, Union

import mysql.connector
import pandas as pd
from models.devops_settings import DevOpsSettings
from mysql.connector import Error as MySQLError
from semantic_kernel.functions import kernel_function
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.telemetry.app_logger import AppLogger


class DevOpsPlugin:
    """
    A DevOps client for connecting to MySQL database,
    executing queries, and formatting results for LLM consumption.
    """

    def __init__(
        self,
        logger: AppLogger,
        devops_settings: DevOpsSettings,
        column_metadata_str: str,
        memory: Optional[SemanticTextMemory] = None,
        memory_store_collection_name: Optional[str] = None,
    ):
        """
        Initialize the database client (MySQL) with connection parameters.

        Args:
            devops_settings: DevOpsSettings instance containing connection parameters
            column_metadata_str: JSON string containing column metadata for the database table
            logger: Optional AppLogger instance for logging (defaults to a new instance)
        """
        self.logger = logger

        self.host = devops_settings.server_url
        self.username = devops_settings.username
        self.password = devops_settings.password
        self.database = devops_settings.database_name
        self.database_table_name = devops_settings.database_table_name
        self.port = devops_settings.port
        self.connection_timeout = devops_settings.connection_timeout
        self.max_retries = devops_settings.max_retries
        self.retry_delay = devops_settings.retry_delay
        self.column_metadata = json.loads(column_metadata_str)

        self.memory = memory
        self.memory_store_collection_name = memory_store_collection_name

        # Maintain single connection to reduce overhead
        # and improve performance for multiple queries
        self.connection = None

    async def initialize(self):
        self.logger.info("Initializing DevOps plugin..")

        if not self.memory or not self.memory_store_collection_name:
            self.logger.warning("Memory store/name is not provided. Skipping memory hydration.")
            return

        self.logger.info("Hydrating memory with DevOps table schema information.")
        query = f"DESCRIBE `{self.database_table_name}`;"

        try:
            results = self.__execute_query(query)

            # Add Description column by mapping from JSON lookup
            # Create a dictionary mapping column names to descriptions from the column_metadata list
            column_desc_map = {item['name']: item['description'] for item in self.column_metadata}

            # Add Description column by mapping from the dictionary lookup
            results['Description'] = results['Field'].map(lambda col: column_desc_map.get(col, 'No description available.'))

            formatted_result = self.format_for_llm(results, max_rows=50)
            await self.memory.save_information(
                id="devops_table_schema",
                collection=self.memory_store_collection_name,
                text=formatted_result,
                description="DevOps table schema information",
                additional_metadata=f"database: {self.database}, table: {self.database_table_name}"
            )

            self.logger.info("DevOps plugin initialized and schema information saved to memory store.")
        except Exception as e:
            error_msg = f"Error retrieving schema for table {self.database_table_name}: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {str(e)}"

    @contextmanager
    def get_connection(self):
        """
        Context manager for handling database connections with retry logic.

        Yields:
            mysql.connector.MySQLConnection: Active database connection

        Raises:
            ConnectionError: If connection cannot be established after max retries
        """
        connection = None
        attempts = 0

        while attempts < self.max_retries:
            try:
                if self.connection is None or not self.connection.is_connected():
                    self.logger.info(f"Establishing connection to MySQL server for database {self.database} on {self.host}:{self.port} (attempt {attempts+1}/{self.max_retries})")

                    connection = mysql.connector.connect(
                        host=self.host,
                        user=self.username,
                        password=self.password,
                        database=self.database,
                        port=self.port,
                        connection_timeout=self.connection_timeout
                    )
                    self.connection = connection
                else:
                    self.logger.info(f"Using existing MySQL connection for database {self.database}")
                    connection = self.connection

                # Return and exit the loop if connection is successful
                yield connection
                break
            except MySQLError as sql_error:
                attempts += 1
                self.logger.error(f"Failed to connect to MySQL: {str(sql_error)}")

                if attempts < self.max_retries:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    import time
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error("Max connection attempts reached")
                    raise ConnectionError(f"Failed to connect to MySQL after {self.max_retries} attempts: {str(sql_error)}")
            finally:
                # Don't close the connection here in favor of a persistent connection
                pass

    def close(self) -> None:
        """Close the database connection if open."""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.logger.info("MySQL connection closed")
        except MySQLError as sql_error:
            self.logger.error(f"Error closing MySQL connection: {str(sql_error)}")

    def __execute_query(
        self,
        query: str,
        fetch: bool = True
    ) -> Union[pd.DataFrame, int]:
        with self.get_connection() as connection:
            try:
                cursor = connection.cursor(dictionary=True)
                try:
                    self.logger.debug(f"Executing query: {query}")
                    cursor.execute(query)

                    if fetch:
                        results = cursor.fetchall()
                        df = pd.DataFrame(results)
                        self.logger.info(f"Query executed successfully on database {self.database}, retrieved {len(df)} rows")
                        return df
                    else:
                        connection.commit()
                        rows_affected = cursor.rowcount
                        self.logger.info(f"Query executed successfully on database {self.database}, {rows_affected} rows affected")
                        return rows_affected
                except MySQLError as sql_error:
                    connection.rollback()
                    error_msg = f"Error executing query: {str(sql_error)}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
                finally:
                    cursor.close()
            except ConnectionError as conn_error:
                self.logger.error(f"Connection error during query execution: {str(conn_error)}")
                raise

    def format_for_llm(self, df: pd.DataFrame, max_rows: int = 50) -> str:
        """
        Format a DataFrame for LLM consumption.

        Args:
            df: DataFrame to format
            max_rows: Maximum number of rows to include

        Returns:
            str: Formatted string representation
        """
        if df.empty:
            return "No data returned."

        # Limit rows for LLM context
        if len(df) > max_rows:
            truncated_df = df.head(max_rows)
            truncated_msg = f"\n[Note: Showing {max_rows} of {len(df)} total rows]"
        else:
            truncated_df = df
            truncated_msg = ""

        try:
            # Convert to JSON string for structured representation
            result = truncated_df.to_json(orient="records", date_format="iso")
            formatted_result = json.dumps(json.loads(result), indent=2)

            result = formatted_result + truncated_msg

            self.logger.info(f"Formatted results LLM: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error formatting results for LLM: {str(e)}")
            # Fall back to string representation
            return str(truncated_df) + truncated_msg

    @kernel_function
    def execute_query(
        self,
        query: str,
        max_rows: int = 50
    ) -> str:
        """
        Execute a query and format the results specifically for LLM consumption.

        Args:
            query: SQL query to execute
            max_rows: Maximum number of rows to include in the result

        Returns:
            str: Formatted query results ready for LLM processing

        Raises:
            Exception: If query execution fails
        """
        try:
            results = self.__execute_query(query)
            return self.format_for_llm(results, max_rows)
        except Exception as e:
            error_msg = f"Error in query execution for LLM: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {str(e)}"

    @kernel_function
    async def get_table_schema(self) -> str:
        """
        Get the schema of a specified table in the database including column names, types, and descriptions.

        Returns:
            str: Formatted JSON string representation of the table schema with additional metadata
        """
        if not self.memory:
            return self.column_metadata

        result = await self.memory.search(
            collection=self.memory_store_collection_name,
            query="DevOps table schema information",
            limit=1
        )

        return {
            "schema": result[0].text,
            "metadata": result[0].additional_metadata if result and result[0].additional_metadata else None
        } if result else "No table schema information found."

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context."""
        self.close()
