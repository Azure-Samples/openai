import asyncio
import os
import uuid

import aiohttp_cors
from aiohttp import web
from clients.azure_index_client import AzureIndexClient
from clients.azure_storage_client import AzureStorageClient
from config import DefaultConfig
from models.api_models import CatalogPayload, DocumentPayload, IngestionRequest
from models.models import CatalogIndexerRequestPayload, DocumentIndexerRequestPayload
from processors.catalog_processor import CatalogProcessor
from processors.document_processor import DocumentProcessor

from common.contracts.data.prompt import Prompt
from common.telemetry.app_logger import AppLogger, LogEvent
from common.utilities.files import load_file
from common.utilities.task_manager import TaskManager
from managers.task_status_manager import TaskStatusManager, TaskStatus

routes = web.RouteTableDef()

ALLOWED_FILE_EXTENSIONS = [".pdf", ".csv"]
UPLOAD_DIRECTORY = "data"
MAX_CONTENT_LENGTH = 50 * 1024 * 1024 # 50MB
TASK_STATUS_MAP_NAME = "task_status_map"

# get the logger that is already initialized
DefaultConfig.initialize()
custom_logger = DefaultConfig.custom_logger
logger = AppLogger(custom_logger)

document_loader = None
document_splitter = None

storage_client = AzureStorageClient(storage_account_name=DefaultConfig.AZURE_STORAGE_ACCOUNT_NAME,
                                    logger=logger)

index_client = AzureIndexClient(search_endpoint=DefaultConfig.AZURE_SEARCH_ENDPOINT,
                                logger=logger)

document_processing_task_manager = TaskManager(AppLogger(custom_logger),
                                               queue_name=DefaultConfig.DOCUMENT_PROCESSING_TASK_QUEUE_CHANNEL,
                                               redis_host=DefaultConfig.REDIS_HOST,
                                               redis_port=DefaultConfig.REDIS_PORT,
                                               redis_password=DefaultConfig.REDIS_PASSWORD,
                                               redis_ssl=False,
                                               max_worker_threads=DefaultConfig.DOCUMENT_PROCESSING_MAX_WORKER_THREADS)

catalog_processing_task_manager = TaskManager(AppLogger(custom_logger),
                                               queue_name=DefaultConfig.CATALOG_PROCESSING_TASK_QUEUE_CHANNEL,
                                               redis_host=DefaultConfig.REDIS_HOST,
                                               redis_port=DefaultConfig.REDIS_PORT,
                                               redis_password=DefaultConfig.REDIS_PASSWORD,
                                               redis_ssl=False,
                                               max_worker_threads=DefaultConfig.CATALOG_PROCESSING_MAX_WORKER_THREADS)

task_status_manager = TaskStatusManager(logger=AppLogger(custom_logger),
                                        task_status_map_name=TASK_STATUS_MAP_NAME,
                                        redis_host=DefaultConfig.REDIS_HOST,
                                        redis_port=DefaultConfig.REDIS_PORT,
                                        redis_password=DefaultConfig.REDIS_PASSWORD,
                                        redis_ssl=False)

prompt_config = load_file(os.path.join(os.path.dirname(__file__), 'static', 'prompt.yaml'), "yaml")
catalog_indexer_detailed_description_prompt = Prompt(**prompt_config["catalog_indexer_detailed_description_prompt"])
catalog_indexer_summarized_description_prompt = Prompt(**prompt_config["catalog_indexer_summarized_description_prompt"])

@routes.get("/indexer")
async def health_check(request: web.Request):
    return web.Response(text="Document Indexer is running!", status=200)

@routes.post("/indexer/index")
async def index_document_async(request: web.Request):
    conversation_id = request.headers.get('conversation_id', "")
    dialog_id = request.headers.get('dialog_id', "")
    user_id = request.headers.get('user_id', "")

    logger = AppLogger(custom_logger)
    logger.set_base_properties({
        "ApplicationName": "DOCUMENT_INDEXER",
        "user_id": user_id,
        "conversation_id": conversation_id,
        "dialog_id": dialog_id
    })

    try:
        logger.log_request_received("Document Indexer: Request Received.")
        request_payload = await request.json()
        ingestion_request = IngestionRequest(**request_payload)

        # Validate storage before creating downstream requests.
        if not await storage_client.validate_container_async(ingestion_request.storage_container_name):
            return web.json_response({"error": "Storage container is invalid."}, status=400)

        # Validate index name before creating downstream requests.
        if not await index_client.validate_index_name(ingestion_request.index_name):
            return web.json_response({"error": "Index name is invalid."}, status=400)

        # Check request payload type.
        if isinstance(ingestion_request.payload, DocumentPayload):
            logger.info(f"Document payload received in ingestion request for document {ingestion_request.payload.filename}.")

            document_name = generate_document_name(ingestion_request.payload)
            document_path = os.path.join(UPLOAD_DIRECTORY, document_name)
            document_bytes, _ = await storage_client.download_file_async(
                ingestion_request.storage_container_name,
                ingestion_request.payload.filename
            )

            # Save file locally.
            # Ideally, the bytes can be used directly against Azure Document Intelligence.
            # However, since document processing has been decoupled from payload submission,
            # storing the file locally helps avoid heavy payload submission to Redis task queues.
            with safe_open(document_path) as target:
                target.write(document_bytes)

            task_id = str(uuid.uuid4())
            request_payload = DocumentIndexerRequestPayload(
                task_id=task_id,
                storage_container_name=ingestion_request.storage_container_name,
                index_name=ingestion_request.index_name,
                document_path=document_path,
                document_name=document_name,
                reported_year=ingestion_request.payload.reported_year,
                subsidiary=ingestion_request.payload.subsidiary
            )
            await task_status_manager.set_task_status(task_id, "Document processing task enqueued in task queue.", TaskStatus.ENQUEUED)
            await document_processing_task_manager.submit_task(request_payload.model_dump_json())
        elif isinstance(ingestion_request.payload, CatalogPayload):
            logger.info(f"Catalog payload received in ingestion request.")

            task_id = str(uuid.uuid4())
            request_payload = CatalogIndexerRequestPayload(
                task_id=task_id,
                index_name=ingestion_request.index_name,
                images_storage_container=ingestion_request.storage_container_name,
                items=ingestion_request.payload.items,
                enrichment=ingestion_request.enrichment is not None
            )
            await task_status_manager.set_task_status(task_id, "Catalog processing task enqueued in task queue.", TaskStatus.ENQUEUED)
            await catalog_processing_task_manager.submit_task(request_payload.model_dump_json())

        logger.log_request_success("Document Indexer: Request Processed.")
        return web.json_response(
            {
                "status": f"Payload submitted for indexing successfully.",
                "task_id": task_id
            },
            status=201
        )
    except Exception as ex:
        logger.error(f"Invalid payload received. {ex}", event=LogEvent.REQUEST_FAILED)
        return web.json_response({"error": "Invalid payload"}, status=400)

@routes.get("/indexer/index/{task_id}")
async def check_ingestion_status(request: web.Request):

    logger = AppLogger(custom_logger)
    logger.set_base_properties({
        "ApplicationName": "DOCUMENT_INDEXER",
        "path":"/indexer/index"
    })

    task_id = request.match_info.get("task_id")

    if not task_id:
        return web.json_response({"error": "Task ID is required to check on status of task."}, status=400)
    
    task_status = await task_status_manager.get_task_status(task_id)

    if task_status == TaskStatus.NOT_FOUND:
        return web.json_response(
            {
                "Task ID": task_id,
                "Task Status": "Task not found."
            },
            status=404
        )
    
    return web.json_response(
            {
                "Task ID": task_id,
                "Task Status": task_status,
            },
            status=200
        )

def generate_document_name(payload: DocumentPayload) -> str:
    filename, ext = os.path.splitext(payload.filename)
    if ext not in ALLOWED_FILE_EXTENSIONS:
        logger.error(f"Document processing failed. File extension not supported.")
        return web.json_response({"error": "File extension not supported."}, status=400)

    return f'{filename}_{payload.reported_year}{ext}'

def safe_open(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'wb')

def start_server(host: str, port: int):
    app = web.Application(client_max_size=MAX_CONTENT_LENGTH)
    app.add_routes(routes)

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
    })

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Start server
    web.run_app(app, host=host, port=port)

async def on_startup(app):
    logger = AppLogger(custom_logger)
    base_properties = {
        "ApplicationName": "DOCUMENT_INDEXER"
    }
    logger.set_base_properties(base_properties)

    document_processor = DocumentProcessor(
        logger=logger,
        storage_client=storage_client,
        search_endpoint=DefaultConfig.AZURE_SEARCH_ENDPOINT,
        document_loader=DefaultConfig.DEFAULT_DOCUMENT_LOADER,
        document_splitter=DefaultConfig.DEFAULT_DOCUMENT_SPLITTER,
        azure_openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
        azure_openai_embeddings_engine_name=DefaultConfig.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME,
        document_intelligence_endpoint=DefaultConfig.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
        document_intelligence_key=DefaultConfig.AZURE_DOCUMENT_INTELLIGENCE_KEY,
        document_intelligence_model=DefaultConfig.AZURE_DOCUMENT_INTELLIGENCE_MODEL,
        document_max_chunk_size=DefaultConfig.DOCUMENT_MAX_CHUNK_SIZE,
        markdown_content_include_image_captions=DefaultConfig.MARKDOWN_CONTENT_INCLUDE_IMAGE_CAPTIONS,
        markdown_header_split_config=DefaultConfig.MARKDOWN_HEADER_SPLIT_CONFIG,
        upload_dir=UPLOAD_DIRECTORY,
        document_indexer_status_manager=task_status_manager
    )
    asyncio.create_task(document_processing_task_manager.start_async(document_processor.process_async))

    catalog_processor = CatalogProcessor(
        logger=logger,
        detailed_description_prompt=catalog_indexer_detailed_description_prompt,
        summarized_description_prompt=catalog_indexer_summarized_description_prompt,
        storage_client=storage_client,
        search_endpoint=DefaultConfig.AZURE_SEARCH_ENDPOINT,
        azure_openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
        azure_openai_embeddings_engine_name=DefaultConfig.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME,
        catalog_indexer_status_manager=task_status_manager
    )
    asyncio.create_task(catalog_processing_task_manager.start_async(catalog_processor.process_async))

async def on_shutdown(app):
    logger = AppLogger(custom_logger)

    await task_status_manager.remove_in_progress_tasks()

    logger.info("Shutting down the server.")

if __name__ == '__main__':
    asyncio.run(start_server(
        host=DefaultConfig.SERVICE_HOST,
        port=int(DefaultConfig.SERVICE_PORT)
    ))