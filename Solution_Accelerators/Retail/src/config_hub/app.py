import asyncio
import os
import json
import time
from azure.identity import DefaultAzureCredential
from common.clients.cosmosdb.container import CosmosConflictError
from common.telemetry.app_logger import AppLogger, LogEvent
from common.telemetry.log_classes import CreateConfigurationLog, LogProperties
from common.utilities.http_response_utils import HTTPStatusCode
from config import DefaultConfig
from quart import Quart, Response, request, jsonify
from quart_cors import cors
from common.contracts.config_hub.create_config import CreateConfigRequest, CreateConfigResponse
from common.utilities.files import load_file_from_sas_url
from common.exceptions import FileDownloadError, FileProcessingError
from core.mapper import ConfigType
from core.manager import ConfigurationManager
from pydantic import ValidationError
from datetime import datetime


# initialize service environment
DefaultConfig.initialize()
custom_logger = DefaultConfig.custom_logger

app = Quart(__name__)
app = cors(app, allow_origin="*")

cosmos_db_credential = DefaultConfig.COSMOS_DB_KEY if (os.getenv("ENVIRONMENT") is not None and os.getenv("ENVIRONMENT").upper() != "PROD") else DefaultAzureCredential()

config_manager = None

async def initialize_db_manager():
    global config_manager
    config_manager = await ConfigurationManager.create(DefaultConfig.COSMOS_DB_ENDPOINT,
                                      cosmos_db_credential,
                                      DefaultConfig.COSMOS_DB_NAME,
                                      DefaultConfig.COSMOS_DB_CONFIGURATION_CONTAINER_NAME,
                                      AppLogger(custom_logger))

@app.before_serving
async def before_serving():
    await initialize_db_manager()
    
@app.route("/configuration-service", methods=["GET"])
async def health_check():
    return jsonify({"message": "Configuration service is running. Please refer to the API documentation for usage."}), 200

@app.route("/configuration-service/configs/<config_id>/<config_version>", methods=["GET"])
async def get_config(config_id, config_version):
    config = await config_manager.get_config_version(config_version, config_id)
    if config is None:
        return jsonify({"error": f"Configuration version {config_version} not found for {config_id}"}), 404
    return jsonify(config.model_dump()), 200

@app.route("/configuration-service/configs/<config_id>", methods=["GET"])
async def list_config_versions(config_id):
    config_versions = await config_manager.list_configs_by_id(config_id)
    if config_versions is None:
        return jsonify({"error": f"Error occured while retrieving configuration versions for {config_id}"}), 404
    return jsonify({"available_configuration_versions" : config_versions}), 200

@app.route("/configuration-service/configs/<config_id>", methods=["POST"])
async def create_config(config_id):
    logger = AppLogger(custom_logger)
    log_properties = LogProperties(application_name="CONFIGURATION_SERVICE", config_id=config_id)
    logger.set_base_properties(log_properties)

    if not request.is_json:
        logger.log_request_failed("Request body must be JSON")
        return Response(
            response=json.dumps({"error": "Request body must be JSON"}),
            status=HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE.value)

    logger.log_request_received("Create configuration request received.")
    try:
        request_data = await request.get_json()
        config_request = CreateConfigRequest(**request_data)
        config_request.config_body = get_config_body(config_request)
        config_request.config_id = config_id
        log_properties.request = request_data
        logger.info(f"request: {request_data}", properties=log_properties.model_dump())

        # validate configuration schema by creating an instance of the specified config type
        config_type = ConfigType.get_model(config_id)
        config_type(**config_request.model_dump())

         # add config version if not provided
        if not config_request.config_version:
            config_request.config_version = generate_unique_version(config_request.config_id)

        created_config = await config_manager.create_config(configuration_data=config_request)
        response = CreateConfigResponse(config_id=created_config["config_id"],
                                        config_version=created_config["id"])

        log_properties.response = response.model_dump_json()
        logger.log_request_success("Configuration created successfully", properties=log_properties)
        return jsonify(response.to_dict()), HTTPStatusCode.OK.value

    except ValidationError as ve:
        logger.log_request_failed(f"Invalid configuration schema. Exception: {str(ve)}")
        return jsonify({
            "config_id": config_id,
            "error": f"Invalid configuration schema for {config_id}. Error: {str(ve)}"}), HTTPStatusCode.BAD_REQUEST.value

    except (FileDownloadError, FileProcessingError) as fe:
        logger.log_request_failed(f"File handling error. Exception: {str(fe)}")
        return jsonify({
            "config_id": config_id,
            "error": f"Invalid request payload to create config: {str(fe)}"}), HTTPStatusCode.BAD_REQUEST.value

    except CosmosConflictError as ce:
        logger.log_request_failed(f"Conflict error. Exception: {str(ce)}")
        return jsonify({
            "config_id": config_id,
            "config_version": config_request.config_version,
            "error": f"Configuration version already exists for config_id '{config_id}' and config_version '{config_request.config_version}'. Try with another config_version."}), 409

    except Exception as e:
        logger.log_request_failed(f"Failed to create configuration. Exception: {str(e)}")
        return jsonify({"error": f"An internal error occurred. Failed to create configuration version for {config_id}, please try again later."}), HTTPStatusCode.INTERNAL_SERVER_ERROR.value

def get_config_body(request: CreateConfigRequest):
    if request.config_body:
        return request.config_body
    else:
        return load_file_from_sas_url(request.config_file_url)

def generate_unique_version(config_id: str) -> str:
    return f"{config_id}_{datetime.now().strftime('%Y%m%d_%f')}"

async def main():
    await initialize_db_manager()
    runner = app.run_task(host=DefaultConfig.SERVICE_HOST, port=DefaultConfig.SERVICE_PORT)
    try:
        await runner
    except (KeyboardInterrupt, SystemExit):
        print('Shutting down server...')
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())