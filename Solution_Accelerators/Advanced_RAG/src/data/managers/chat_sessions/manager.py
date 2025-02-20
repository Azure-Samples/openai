from azure.cosmos.aio import CosmosClient
from common.contracts.common.conversation import Conversation, Dialog
from common.clients.cosmosdb.container import CosmosDBContainer, CosmosConflictError
from typing import Any, Optional

"""
Manager API for creating, retrieving and updating chat sessions in storage.
"""
class ChatSessionManager:
    PARTITION_KEY_NAME = "partition_key"
    UNIQUE_KEYS = [
        {"paths": [f"/{PARTITION_KEY_NAME}"]}
    ]

    def __init__(self, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_chat_sessions_container_name: str):
        self.cosmos_db_endpoint = cosmos_db_endpoint
        self.cosmos_db_credential = cosmos_db_credential
        self.cosmos_db_name = cosmos_db_name
        self.cosmos_db_chat_sessions_container_name = cosmos_db_chat_sessions_container_name
        self.container = None
        
    @classmethod
    async def create(cls, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_chat_sessions_container_name: str):
        self =cls(cosmos_db_endpoint, cosmos_db_credential, cosmos_db_name, cosmos_db_chat_sessions_container_name)
        await self._initialize_container()
        return self
    
    async def _initialize_container(self):
        cosmos_client = CosmosClient(url=self.cosmos_db_endpoint, credential=self.cosmos_db_credential, consistency_level="Session")
        self.container = await CosmosDBContainer.create(
            self.cosmos_db_name, 
            self.cosmos_db_chat_sessions_container_name, 
            self.PARTITION_KEY_NAME, 
            cosmos_client, 
            self.UNIQUE_KEYS
        )
    
    """
    Creates a new chat session with the specified conversation ID and optional initial conversation.
    """
    async def create_chat_session(self, user_id: str, conversation_id: str, chat_session: Conversation) -> Conversation:
        try:
            item = chat_session.model_dump()
            partition_key = f"{user_id}|{conversation_id}"
            created_item = await self.container.create_item(conversation_id, partition_key, item)
            return Conversation(**created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"Chat session with conversation ID {chat_session.conversation_id} already exists.")

    """
    Retrieves and deserializes a chat session using the specified user Id, conversation ID.
    Returns empty chat session if the specified userId, conversation ID does not exists.
    """
    async def get_chat_session(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        try:
            item = await self.container.get_item(conversation_id, f"{user_id}|{conversation_id}")
            return Conversation(**item) if item else Conversation()
        except Exception as e:
            raise Exception(f"Error retrieving chat session: {str(e)}")
    
    """
    Clears the chat session with the specified conversation ID.
    Raises an exception if no chat session exists with the specified conversation ID.
    """
    async def clear_chat_session(self, user_id: str, conversation_id: str):
        try:
            chat_session = await self.get_chat_session(user_id, conversation_id)
            if len(chat_session.dialogs) == 0:
                return
            
            chat_session.dialogs = []
            item = chat_session.model_dump()
            partition_key = f"{user_id}|{conversation_id}"
            await self.container.upsert_item(conversation_id, partition_key, item)
        except Exception as e:
            raise Exception(f"Error clearing chat session: {str(e)}")

    """
    Adds a new dialog to the chat session with the specified conversation ID.
    Raises an exception if no chat session exists with the specified conversation ID.
    """
    async def add_dialog_to_chat_session(self, user_id: str, conversation_id: str, dialog: Dialog) -> Conversation:
        try:
            chat_session = await self.get_chat_session(user_id, conversation_id)
            # if chat_session is None:
            #     raise SessionNotFoundError(f"Chat session with conversation ID {conversation_id} could not be found.")
            chat_session.add_dialog(dialog)
            item = chat_session.model_dump()
            partition_key = f"{user_id}|{conversation_id}"
            updated_item = await self.container.upsert_item(conversation_id, partition_key, item)
            return Conversation(**updated_item)
        except Exception as e:
            raise Exception(f"Error adding dialog to chat session: {str(e)}")