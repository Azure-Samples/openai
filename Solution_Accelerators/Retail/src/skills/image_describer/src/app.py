import os
import base64
import asyncio

from common.contracts.data.prompt import Prompt
from common.telemetry.log_classes import LogProperties
from common.utilities.http_response_utils import HTTPStatusCode, create_error_response
from quart import Quart, jsonify, request
from azure.core.exceptions import ClientAuthenticationError

from config import DefaultConfig
from common.exceptions import ContentFilterException, RateLimitException
from common.contracts.skills.image_describer.api_models import AnalysisRequest, AnalysisResponse, Analysis
from describers.openai_describer import OpenAiImageDescriber
from common.clients.openai.openai_client import AzureOpenAIClient
from common.telemetry.app_logger import AppLogger, LogEvent
from common.utilities.blob_store import BlobStoreHelper
from common.utilities.files import load_file
from mimetypes import guess_type

app = Quart(__name__)

prompts = load_file(os.path.join(os.path.dirname(__file__), 'static', 'prompts_config.yaml'), "yaml")

# get the logger that is already initialized
DefaultConfig.initialize()
custom_logger = DefaultConfig.custom_logger

IMAGE_ANALYZER_COGNITIVE_SERVICES_KEY = "cognitiveservices"
IMAGE_ANALYZER_OPENAI_KEY = "openai"

logger = AppLogger(custom_logger)
openai_image_analyzer = OpenAiImageDescriber(
    openai_client=AzureOpenAIClient(logger=logger, endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT, retry=True),
    logger=logger,
)

@app.route("/analyze", methods=["POST"])
async def analyze_images():
    logger = AppLogger(custom_logger)
    conversation_id = request.headers.get('conversation_id', "")
    dialog_id = request.headers.get('dialog_id', "")
    user_id = request.headers.get('user_id', "")
    log_properties = LogProperties(
        conversation_id=conversation_id, dialog_id=dialog_id, user_id=user_id, application_name="IMAGE_DESCRIBER_SKILL"
    )
    logger.set_base_properties(log_properties.model_dump())
    logger.log_request_received("Image Describer: Request Received.")
    
    if not request.is_json:
        return create_error_response(HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE, "Request must be json.", log_properties, logger=logger)
    
    request_json = await request.get_json()
    analysis_request = AnalysisRequest(**request_json)
    log_properties.request = request_json

    # Read default analyzer from the environment variables.
    analyzer = DefaultConfig.IMAGE_ANALYSIS_DEFAULT_ANALYZER_SERVICE
    blob_store_helper = BlobStoreHelper(logger=logger, storage_account_name = DefaultConfig.AZURE_STORAGE_ACCOUNT_NAME, container_name=DefaultConfig.AZURE_STORAGE_IMAGE_CONTAINER)

    logger.info(f"Total images in request payload: {len(analysis_request.images)}")

    image_analysis_results = list()
    image_data = []
    image_analysis_tasks = []

    try:
        for image_url in analysis_request.images:
            img_name, img_data = await blob_store_helper.download_image_data(sasUrl=image_url)
            mime_type = guess_type(image_url)
            image_data.append((img_name, img_data, mime_type[0] if mime_type else None))

        # analyze images
        for img_name, img_data, mime_type in image_data:
            if analyzer == IMAGE_ANALYZER_OPENAI_KEY:
                imgAsBase64EncodedBytes = base64.b64encode(img_data).decode('utf-8')
                image_analysis_task = asyncio.create_task(openai_image_analyzer.analyze_async(
                    analyze_image_prompt=Prompt(**prompts["image_describer"]), base64_encoded_img=imgAsBase64EncodedBytes, user_query=analysis_request.user_query, mime_type=mime_type))
                image_analysis_tasks.append(image_analysis_task)

        # gather all image analysis results
        if analyzer == IMAGE_ANALYZER_OPENAI_KEY:
            image_analysis_task_results = await asyncio.gather(*image_analysis_tasks)
            i = 0
            while i < len(image_analysis_task_results):
                if image_analysis_task_results[i] is None:
                    return create_error_response(HTTPStatusCode.INTERNAL_SERVER_ERROR, "Image analysis failed. Request should be retried.", log_properties, logger)
                else:
                    image_analysis_results.append(
                        Analysis(image=image_data[i][0], analysis=image_analysis_task_results[i]))
                i += 1

        logger.log_request_success("Image Describer: Request Completed.", properties=log_properties)
        return AnalysisResponse(results=image_analysis_results).model_dump_json(), 200

    except (ClientAuthenticationError) as ex:
        err_msg = "Image analysis failed either due to inability to download image from the blob store."
        return create_error_response(500, f"{err_msg} {ex}", log_properties)
    
    except RateLimitException as ex:
        return create_error_response(HTTPStatusCode.TOO_MANY_REQUESTS, f"Image analysis failed due to rate limits. {ex}", log_properties, logger)

    except ContentFilterException as ex:
        return create_error_response(HTTPStatusCode.FORBIDDEN, f"Image analysis failed due to content filter exception. {ex}", log_properties, logger)
    
    except Exception as ex:
        return create_error_response(HTTPStatusCode.INTERNAL_SERVER_ERROR, f"Image analysis failed. {ex}", logger=logger)


if __name__ == "__main__":
    host = DefaultConfig.SERVICE_HOST
    port = int(DefaultConfig.SERVICE_PORT)
    app.run(host, port)