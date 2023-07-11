import json
from common.contracts.access_rule import Member, Resource
from common.contracts.chat_session import Dialog, DialogClassification, ParticipantType
from common.contracts.group import User
from common.contracts.resource import ResourceProfile, ResourceTypes
from common.utilities.property_item_reader import read_item_property_with_type, read_item_property_with_enum, NullValueError, MissingPropertyError
from data.config import DefaultConfig
from data.cosmosdb.container import CosmosConflictError
from data.managers.chat_sessions.api.manager import SessionNotFoundError, ChatSessionManager
from data.managers.permissions.manager import PermissionsManager
from data.managers.entities.api.manager import EntitiesManager
from datetime import datetime
from flask import Flask, Response, request
from typing import List, Set

# initialize config
DefaultConfig.initialize()

# get the logger that is already initialized
logger = DefaultConfig.logger

app = Flask(__name__)

cosmos_db_endpoint = DefaultConfig.COSMOS_DB_ENDPOINT
cosmos_db_key = DefaultConfig.COSMOS_DB_KEY
cosmos_db_name = DefaultConfig.COSMOS_DB_NAME
cosmos_db_chat_sessions_container_name = DefaultConfig.COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME
cosmos_db_entities_container_name = DefaultConfig.COSMOS_DB_ENTITIES_CONTAINER_NAME
cosmos_db_permissions_container_name = DefaultConfig.COSMOS_DB_PERMISSIONS_CONTAINER_NAME

chat_manager = ChatSessionManager(cosmos_db_endpoint, cosmos_db_key, cosmos_db_name, cosmos_db_chat_sessions_container_name)
entities_manager = EntitiesManager(cosmos_db_endpoint, cosmos_db_key, cosmos_db_name, cosmos_db_entities_container_name)
permissions_manager = PermissionsManager(cosmos_db_endpoint, cosmos_db_key, cosmos_db_name, cosmos_db_permissions_container_name)

@app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['POST'])
def create_chat_session(user_id: str, conversation_id: str):
    properties = get_log_properties(request, user_id)
    logger.info("create_chat_session", extra=properties)

    body = request.json

    if body is None:
        logger.error("create-chat-session: error: Missing request body.", extra=properties)
        return Response(response="Missing request body.", status=400)
    
    try:
        start = datetime.now()

        initial_conversation_dct = body.get('initial_conversation', [])
        initial_conversation: List[Dialog] = []
        for dialog_dict in initial_conversation_dct:
            initial_conversation.append(Dialog.as_item(dialog_dict))
        session = chat_manager.create_chat_session(user_id, conversation_id, initial_conversation)
        
        end = datetime.now()
        
        addl_dim = {"create-chat-sessions[MS]": (end - start).microseconds/1000}
        properties = logger.get_updated_properties(addl_dim)
        logger.info(f'chat session created for user_id {user_id} session_id {conversation_id}', extra=properties)

        return Response(response=json.dumps(session.to_item()), status=201)
    except (TypeError, NullValueError, MissingPropertyError) as e:
        logger.exception(f"create-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=400)
    except CosmosConflictError as e:
        logger.exception(f"create-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=409)
    except Exception as e:
        logger.exception(f"create-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=500)
    
@app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['GET'])
def get_chat_session(user_id: str, conversation_id: str):

    properties = get_log_properties(request, user_id)
    logger.info("get_chat_session", extra=properties)

    try:
        start = datetime.now()
        session = chat_manager.get_chat_session(user_id, conversation_id)
        end = datetime.now()
        
        addl_dim ={"get-chat-sessions[MS]": (end - start).microseconds/1000}
        properties = logger.get_updated_properties(addl_dim)

        if session is None:
            logger.info(f"get-chat-session: session with conversation_id {conversation_id} not found", extra=properties)
            return Response(response=f"Chat session with conversation_id {conversation_id} not found.", status=404)
        else:
            logger.info("get-chat-session: session found", extra=properties)
            return Response(response=json.dumps(session.to_item()), status=200)
    except Exception as e:
        logger.exception(f"get-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=500)

@app.route('/check-chat-session/<user_id>/<conversation_id>', methods=['GET'])
def check_chat_session(user_id: str, conversation_id: str):

    properties = get_log_properties(request, user_id)
    logger.info("check_chat_session", extra=properties)

    try:
        start = datetime.now()
        session = chat_manager.get_chat_session(user_id, conversation_id)
        end = datetime.now()
        addl_dim= {"get-chat-sessions[MS]":(end - start).microseconds/1000}
        properties = logger.get_updated_properties(addl_dim)
        if session is None:
            logger.info(f"check-chat-session: session not found for user_id {user_id} and conversation_id {conversation_id}", extra=properties)
            return Response(response=f"false", status=200)
        else:
            logger.info(f"check-chat-session: session found for user_id {user_id} and conversation_id {conversation_id}", extra=properties)
            return Response(response="true", status=200)
    except Exception as e:
        logger.exception(f"check-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=500)

@app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['PUT'])
def update_chat_session(user_id: str, conversation_id: str):

    properties = get_log_properties(request, user_id)
    logger.info("update_chat_session", extra=properties)

    body = request.json
    if body is None:
        logger.error("update-chat-session: Missing request body.", extra=properties)
        return Response(response="Missing request body.", status=400)
    
    try:
        start = datetime.now()

        valid_participant_types = [type.value for type in ParticipantType]
        participant_type = read_item_property_with_enum(body, 'participant_type', valid_participant_types, ParticipantType)
        utterance = read_item_property_with_type(body, 'utterance', str)
        timestamp_converter = lambda timestamp_str : datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
        timestamp = read_item_property_with_type(body, 'timestamp', datetime, converter=timestamp_converter)
        valid_dialog_classifications = [classification.value for classification in DialogClassification]
        classification = read_item_property_with_enum(body, 'classification', valid_dialog_classifications, DialogClassification)
    
        session = chat_manager.add_dialog_to_chat_session(user_id, conversation_id, participant_type, timestamp, utterance, classification)
        end = datetime.now()

        addl_dim= {"update-chat-session[MS]":(end - start).microseconds/1000}
        properties = logger.get_updated_properties(addl_dim)
        logger.info("update-chat-session: session updated", extra=properties)

        return Response(response=json.dumps(session.to_item()), status=200)
    except (TypeError, NullValueError, MissingPropertyError, ValueError) as e:
        logger.exception(f"update-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=400)
    except SessionNotFoundError as e:
        logger.exception(f"update-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=404)
    except Exception as e:
        logger.exception(f"update-chat-session: error: {e} ", extra=properties)
        return Response(response=str(e), status=500)
    
@app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['DELETE'])
def clear_chat_session(user_id: str, conversation_id: str):
    try:
        chat_manager.clear_chat_session(user_id, conversation_id)
        return Response(status=200)
    except SessionNotFoundError as e:
        return Response(response=str(e), status=404)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/user-profiles/<user_id>', methods=['POST'])
def create_user_profile(user_id: str):
    body = request.json
    if body is None:
        return Response(response="Missing request body.", status=400)
    
    try:
        user_name = read_item_property_with_type(body, 'user_name', str)
        description = read_item_property_with_type(body, "description", str)
        sample_questions = read_item_property_with_type(body, "sample_questions", list, optional=True)

        sample_questions = sample_questions if sample_questions is not None else []
        for question in sample_questions:
            if not isinstance(question, str):
                raise Exception(f"Invalid UserProfile payload. sample_questions must be a list of strings.")

        user_profile = entities_manager.create_user_profile(user_id, user_name, description, sample_questions)
        return Response(response=json.dumps(user_profile.to_item()), status=201)
    except (TypeError, NullValueError, MissingPropertyError) as e:
        return Response(response=str(e), status=400)
    except CosmosConflictError as e:
        return Response(response=str(e), status=409)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/user-profiles/<user_id>', methods=['GET'])
def get_user_profile(user_id: str):
    
    try:
        user_profile = entities_manager.get_user_profile(user_id)
        if user_profile is None:
            return Response(response=f"User profile with user_id {user_id} not found.", status=404)
        else:
            return Response(response=json.dumps(user_profile.to_item()), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)

@app.route('/user-profiles', methods=['GET'])
def get_all_user_profiles():
    try:
        user_profiles = entities_manager.get_all_user_profiles()
        json_user_profiles = [user_profile.to_item() for user_profile in user_profiles]
        return Response(response=json.dumps(json_user_profiles), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/user-groups/<group_id>', methods=['POST'])
def create_user_group(group_id: str):
    body = request.json
    if body is None:
        return Response(response="Missing request body.", status=400)
    
    try:
        group_name = read_item_property_with_type(body, 'group_name', str)
        users_dict = read_item_property_with_type(body, "users", list, optional=True)

        users: Set[User] = set()
        if (not users_dict is None):
            for user_dict in users_dict:
                users.add(User.as_item(user_dict))

        user_group = entities_manager.create_user_group(group_id, group_name, users)
        return Response(response=json.dumps(user_group.to_item()), status=201)
    except (TypeError, NullValueError, MissingPropertyError) as e:
        return Response(response=str(e), status=400)
    except CosmosConflictError as e:
        return Response(response=str(e), status=409)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/user-groups/<group_id>', methods=['GET'])
def get_user_group(group_id: str):
    try:
        user_group = entities_manager.get_user_group(group_id)
        if user_group is None:
            return Response(response=f"User group with group_id {group_id} not found.", status=404)
        else:
            return Response(response=json.dumps(user_group.to_item()), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/user-groups/user/<user_id>', methods=['GET'])
def get_user_member_groups(user_id: str):
    try:
        user_groups = entities_manager.get_user_member_groups(user_id)
        if user_groups is None:
            return Response(response=f"User with user_id {user_id} not found.", status=404)
        else:
            return Response(response=json.dumps([user_group.to_item_no_users() for user_group in user_groups]), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/user-groups/<group_id>', methods=['PUT'])
def update_user_group(group_id: str):
    body = request.json
    if body is None:
        return Response(response="Missing request body.", status=400)
    
    try:
        users_dict = read_item_property_with_type(body, "users", list)

        new_users: Set[User] = set()
        for user_dict in users_dict:
            new_users.add(User.as_item(user_dict))
    
        user_group = entities_manager.add_users_to_user_group(group_id, new_users)
        return Response(response=json.dumps(user_group.to_item()), status=200)
    except (TypeError, NullValueError, MissingPropertyError, ValueError) as e:
        return Response(response=str(e), status=400)
    except SessionNotFoundError as e:
        return Response(response=str(e), status=404)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/resources/<resource_id>', methods=['POST'])
def create_resource(resource_id: str):
    body = request.json
    if body is None:
        return Response(response="Missing request body.", status=400)
    
    try:
        valid_resource_types = [resource.value for resource in ResourceTypes]
        resource_type = read_item_property_with_enum(body, 'resource_type', valid_resource_types, ResourceTypes)

        resource = entities_manager.create_resource(resource_id, resource_type)
        return Response(response=json.dumps(resource.to_item()), status=201)
    except (TypeError, NullValueError, MissingPropertyError) as e:
        return Response(response=str(e), status=400)
    except CosmosConflictError as e:
        return Response(response=str(e), status=409)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id: str):
    try:
        resource = entities_manager.get_resource(resource_id)
        if resource is None:
            return Response(response=f"Resource with resource_id {resource_id} not found.", status=404)
        else:
            return Response(response=json.dumps(resource.to_item()), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/resources/user/<user_id>', methods=['GET'])
def get_user_resources(user_id: str):
    try:
        user_profile = entities_manager.get_user_profile(user_id)
        if user_profile is None:
            return Response(response=f"User with user_id {user_id} not found.", status=404)
        user_groups = entities_manager.get_user_member_groups(user_id)
        resources = permissions_manager.get_user_resources(user_profile, user_groups)
        
        resource_profiles: List[ResourceProfile] = []
        for resource in resources:
            resource_profile = entities_manager.get_resource(resource.resource_id)
            if resource_profile is not None:
                resource_profiles.append(resource_profile)
            else:
                return Response(response="Could not find resource profile for resource ID {resource.resource_id}.", status=500)
        return Response(response=json.dumps([resource_profile.to_item() for resource_profile in resource_profiles]), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/access-rules/<rule_id>', methods=['POST'])
def create_access_rule(rule_id: str):
    body = request.json
    if body is None:
        return Response(response="Missing request body.", status=400)
    
    try:
        members_dict = read_item_property_with_type(body, "members", list)
        resources_dict = read_item_property_with_type(body, "resources", list)

        members: List[Member] = []
        for member_dict in members_dict:
            members.append(Member.as_item(member_dict))
        
        resources: List[Resource] = []
        for resource_dict in resources_dict:
            resources.append(Resource.as_item(resource_dict))

        access_rule = permissions_manager.create_access_rule(rule_id, resources, members)
        return Response(response=json.dumps(access_rule.to_item()), status=201)
    except (TypeError, NullValueError, MissingPropertyError) as e:
        return Response(response=str(e), status=400)
    except CosmosConflictError as e:
        return Response(response=str(e), status=409)
    except Exception as e:
        return Response(response=str(e), status=500)
    
@app.route('/access-rules/<rule_id>', methods=['GET'])
def get_access_rule(rule_id: str):
    try:
        access_rule = permissions_manager.get_access_rule(rule_id)
        if access_rule is None:
            return Response(response=f"Access rule with rule_id {rule_id} not found.", status=404)
        else:
            return Response(response=json.dumps(access_rule.to_item()), status=200)
    except Exception as e:
        return Response(response=str(e), status=500)

def get_log_properties(request, user_id: str) -> dict:
    conversation_id = request.headers.get('Conversation-Id')
    dialog_id = request.headers.get('Dialog-id')
    
    logger.set_conversation_and_dialog_ids(conversation_id, dialog_id)

    dim = logger.get_converation_and_dialog_ids()
    return logger.get_updated_properties({**dim, "user_id": user_id})
    
if __name__ == '__main__':
    host = DefaultConfig.DATA_SERVICE_HOST
    port = int(DefaultConfig.DATA_SERVICE_PORT)
    app.run(host=host, port=port)