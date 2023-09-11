import datetime
import json
import mimetypes

import yaml
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from backend.approaches.approach import Approach
from backend.approaches.approach_classifier import ApproachClassifier
from backend.approaches.chatstructured import ChatStructuredApproach
from backend.approaches.chatunstructured import ChatUnstructuredApproach
from backend.cognition.openai_client import OpenAIClient
from backend.config import DefaultConfig
from backend.contracts.chat_response import Answer, ApproachType, ChatResponse
from backend.contracts.error import (
    ContentFilterException,
    OutOfScopeException,
    UnauthorizedDBAccessException,
)
from backend.contracts.search_settings import SearchSettings
from backend.data_client.data_client import DataClient
from backend.utilities.access_management import AccessManager
from common.contracts.chat_session import (
    ChatSession,
    DialogClassification,
    ParticipantType,
)
from flask import Flask, jsonify, request

# Use the current user identity to authenticate with Azure OpenAI, Cognitive Search and Blob Storage (no secrets needed,
# just use 'az login' locally, and managed identity when deployed on Azure). If you need to use keys, use separate AzureKeyCredential instances with the
# keys for each service
# If you encounter a blocking error during a DefaultAzureCredntial resolution, you can exclude the problematic credential by using a parameter (ex. exclude_shared_token_cache_credential=True)
DefaultConfig.initialize()
azure_credential = DefaultAzureCredential()
search_credential = AzureKeyCredential(DefaultConfig.AZURE_SEARCH_KEY)

openai_client = OpenAIClient()

# Set up clients for Cognitive Search and Storage
search_client = SearchClient(
    endpoint=f"https://{DefaultConfig.AZURE_SEARCH_SERVICE}.search.windows.net",
    index_name=DefaultConfig.AZURE_SEARCH_INDEX,
    credential=search_credential,
)

blob_client = BlobServiceClient.from_connection_string(
    DefaultConfig.AZURE_BLOB_CONNECTION_STRING
)
blob_container = blob_client.get_container_client(DefaultConfig.AZURE_STORAGE_CONTAINER)

# get the logger that is already initialized
logger = DefaultConfig.logger

chat_approaches = {
    ApproachType.unstructured.name: ChatUnstructuredApproach(
        search_client,
        DefaultConfig.KB_FIELDS_SOURCEPAGE,
        DefaultConfig.KB_FIELDS_CONTENT,
        logger,
        search_threshold_percentage=DefaultConfig.SEARCH_THRESHOLD_PERCENTAGE,
    ),
    ApproachType.structured.name: ChatStructuredApproach(
        DefaultConfig.SQL_CONNECTION_STRING, logger
    ),
}

# initialize data client
base_uri = DefaultConfig.DATA_SERVICE_URI
data_client = DataClient(base_uri, logger)
approach_classifier = ApproachClassifier(logger)
access_manager = AccessManager()

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path):
    return app.send_static_file("index.html")


@app.route("/assets/<path:rest_of_path>")
def assets(rest_of_path):
    return app.send_static_file(f"assets/{rest_of_path}")


# Serve content files from blob storage from within the app to keep the example self-contained.
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.
@app.route("/content/<path>")
def content_file(path):
    blob = blob_container.get_blob_client(path).download_blob()
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return (
        blob.readall(),
        200,
        {"Content-Type": mime_type, "Content-Disposition": f"inline; filename={path}"},
    )


@app.route("/chat", methods=["POST"])
def chat():
    # try get conversation_id and dialog_id needed for logging
    conversation_id = request.json.get(
        "conversation_id", "no conversation_id found in request"
    )
    dialog_id = request.json.get("dialog_id", "no dialog_id found in request")
    user_id = request.json.get("user_id", "no user_id found in request")

    classification_override = None
    overrides = request.json.get("overrides", None)
    if overrides:
        classification_override = overrides.get("classification_override", None)

    # fetch user profile
    user_profile = data_client.get_user_profile(user_id)

    # check user access rules
    allowed_resources = data_client.get_user_resources(user_id)
    allowed_approaches = access_manager.get_allowed_approaches(allowed_resources)

    logger.set_conversation_and_dialog_ids(conversation_id, dialog_id)
    properties = logger.get_updated_properties(
        {"conversation_id": conversation_id, "dialog_id": dialog_id, "user_id": user_id}
    )

    logger.info(f"request: {json.dumps(request.json)}", extra=properties)

    user_message = request.json.get("dialog")

    chat_session: ChatSession
    chat_session_exists = data_client.check_chat_session(user_id, conversation_id)
    if not chat_session_exists:
        chat_session = data_client.create_chat_session(user_id, conversation_id)
        logger.info(
            f"created new chat session for user {user_id} and session {conversation_id}",
            extra=properties,
        )
    else:
        chat_session = data_client.get_chat_session(user_id, conversation_id)
        logger.info(
            f"chat session for user {user_id} and session {conversation_id} already exists",
            extra=properties,
        )

    history = [
        {
            "participant_type": dialog.participant_type.value,
            "utterance": dialog.utterance,
            "question_type": dialog.classification.value,
        }
        for dialog in chat_session.conversation
    ]
    history.append(
        {"participant_type": ParticipantType.user.value, "utterance": user_message}
    )

    bot_config = yaml.safe_load(open("backend/bot_config.yaml", "r"))
    question_classification = None

    try:

        if classification_override:
            approach_type = ApproachType(classification_override)
        else:
            approach_type = approach_classifier.run(history, bot_config, openai_client)

        logger.info(f"question_type: {approach_type.name}", extra=properties)

        if approach_type == ApproachType.chit_chat:
            chit_chat_canned_response = "I'm sorry, but the question you've asked is outside my area of expertise. I'd be happy to help with any questions related to Microsoft Surface PCs and Laptops. Please feel free to ask about those, and I'll do my best to assist you!"
            data_client.add_dialog_to_chat_session(
                user_id,
                conversation_id,
                ParticipantType.user,
                datetime.datetime.now(),
                user_message,
                DialogClassification.chit_chat,
            )
            logger.info(
                f"added dialog to chat session for user {user_id} and session {conversation_id}",
                extra=properties,
            )

            answer = Answer(formatted_answer=chit_chat_canned_response)
            response = ChatResponse(answer=answer, classification=approach_type)

            data_client.add_dialog_to_chat_session(
                user_id,
                conversation_id,
                ParticipantType.assistant,
                datetime.datetime.now(),
                json.dumps(response.answer.to_item()),
                DialogClassification.chit_chat,
            )
            logger.info(
                f"added response {chit_chat_canned_response} to chat session for user {user_id} and session {conversation_id}",
                extra=properties,
            )

            return jsonify(response.to_item())

        elif approach_type == ApproachType.inappropriate:

            inappropiate_canned_response = "I'm sorry, but the question you've asked goes against our content safety policy due to harmful, offensive, or illegal content. I'd be happy to help with any questions related to Microsoft Surface PCs and Laptops. Please feel free to ask about those, and I'll do my best to assist you!"
            # TODO: Use DialogClassification.inappropiate once data service has been updated.
            data_client.add_dialog_to_chat_session(
                user_id,
                conversation_id,
                ParticipantType.user,
                datetime.datetime.now(),
                user_message,
                DialogClassification.chit_chat,
            )
            logger.info(
                f"added dialog to chat session for user {user_id} and session {conversation_id}",
                extra=properties,
            )

            answer = Answer(formatted_answer=inappropiate_canned_response)
            response = ChatResponse(answer=answer, classification=approach_type)
            # TODO: Use DialogClassification.inappropiate once data service has been updated.
            data_client.add_dialog_to_chat_session(
                user_id,
                conversation_id,
                ParticipantType.assistant,
                datetime.datetime.now(),
                json.dumps(response.answer.to_item()),
                DialogClassification.chit_chat,
            )
            logger.info(
                f"added response {inappropiate_canned_response} to chat session for user {user_id} and session {conversation_id}",
                extra=properties,
            )

            return jsonify(response.to_item())

        # check if user is allowed to use the approach
        user_allowed = access_manager.is_user_allowed(allowed_approaches, approach_type)

        if not user_allowed:
            prohibited_resource = access_manager.map_approach_to_resource(approach_type)
            raise Exception(
                f"This query requires access to {prohibited_resource}\nUser: {user_profile.user_name} is not allowed to use this resource, please try another query or contact your administrator."
            )

        question_classification = (
            DialogClassification.unstructured_query
            if approach_type == ApproachType.unstructured
            else DialogClassification.structured_query
        )

        # filtered_chat_session = data_client.filter_chat_session(chat_session, filter=question_classification)
        filtered_chat_session = chat_session
        simplified_history = [
            {
                "participant_type": dialog.participant_type.value,
                "utterance": dialog.utterance,
            }
            for dialog in filtered_chat_session.conversation
        ]
        simplified_history.append(
            {"participant_type": ParticipantType.user.value, "utterance": user_message}
        )

        impl = chat_approaches.get(approach_type.name)

        if not impl:
            return jsonify({"error": "unknown approach"}), 400

        response = impl.run(
            simplified_history,
            bot_config,
            openai_client,
            request.json.get("overrides") or None,
        )

        # state store update
        if not response.error:
            data_client.add_dialog_to_chat_session(
                user_id,
                conversation_id,
                ParticipantType.user,
                datetime.datetime.now(),
                user_message,
                question_classification,
            )
            logger.info(
                f"added dialog to chat session for user {user_id} and session {conversation_id}",
                extra=properties,
            )
            data_client.add_dialog_to_chat_session(
                user_id,
                conversation_id,
                ParticipantType.assistant,
                datetime.datetime.now(),
                json.dumps(response.answer.to_item()),
                question_classification,
            )
            logger.info(
                f"added response {response.answer.formatted_answer} to chat session for user {user_id} and session {conversation_id}",
                extra=properties,
            )

        return jsonify(response.to_item())
    except OutOfScopeException as e:
        logger.exception(f"Exception in /chat: {str(e)}", extra=properties)
        if access_manager.is_user_allowed(
            allowed_approaches, e.suggested_classification
        ):
            response = ChatResponse(
                answer=Answer(
                    f"Error when querying knowledge-base: '{str(e.message)}'."
                ),
                show_retry=True,
                suggested_classification=e.suggested_classification,
                classification=question_classification,
            )
            return jsonify(response.to_item())
        else:
            response = ChatResponse(
                answer=Answer(str(e.message)), classification=question_classification
            )
            return jsonify(response.to_item())
    except UnauthorizedDBAccessException as e:
        logger.exception(
            f"UnauthorizedDBAccessExceptionException in /chat: {str(e)}",
            extra=properties,
        )
        response = ChatResponse(answer=Answer(), error=str(e.message))
        return jsonify(response.to_item()), 403
    except ContentFilterException as e:
        logger.exception(f"ContentFilterException in /chat: {str(e)}", extra=properties)
        response = ChatResponse(answer=Answer(), error=str(e.message))
        return jsonify(response.to_item()), 400
    except Exception as e:
        logger.exception(f"Exception in /chat: {e}", extra=properties)
        response = ChatResponse(answer=Answer(), error=str(e), show_retry=True)
        return jsonify(response.to_item()), 500


@app.route("/user-profiles", methods=["GET"])
def get_all_user_profiles():
    try:
        user_profiles = data_client.get_all_user_profiles()
        user_profiles_dict = [user_profile.to_item() for user_profile in user_profiles]
        return jsonify(user_profiles_dict)
    except Exception as e:
        logger.exception(f"Exception in /user-profiles: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/chat-sessions/<user_id>/<conversation_id>", methods=["DELETE"])
def clear_chat_session(user_id: str, conversation_id: str):
    properties = logger.get_updated_properties(
        {"user_id": user_id, "conversation_id": conversation_id}
    )

    try:
        data_client.clear_chat_session(user_id, conversation_id)
        logger.info(f"cleared chat session.", extra=properties)
        return jsonify({"message": "cleared chat session"})
    except Exception as e:
        logger.exception(
            f"Exception in /chat-sessions/<user_id>/<conversation_id>: {e}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/search-settings", methods=["GET"])
def get_search_settings():
    try:
        skip_vectorization_str = DefaultConfig.SEARCH_SKIP_VECTORIZATION
        vectorization_enabled = (
            True
            if skip_vectorization_str.lower() == "false"
            else False
            if skip_vectorization_str.lower() == "true"
            else None
        )
        if vectorization_enabled is None:
            raise Exception(
                f"Invalid value for SEARCH_SKIP_VECTORIZATION: {skip_vectorization_str}. Must be either 'true' or 'false'"
            )
        search_settings = SearchSettings(vectorization_enabled)
        return jsonify(search_settings.to_item())
    except Exception as e:
        logger.exception(f"Exception in /search-settings: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run()
