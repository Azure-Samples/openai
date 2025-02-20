from azure.cosmos.aio import CosmosClient
from common.contracts.common.user_profile import UserProfile
from common.clients.cosmosdb.container import CosmosDBContainer, CosmosConflictError
from enum import Enum
from typing import Any, List, Optional

class UserGroupNotFoundError(BaseException):
    pass

class PartitionType(Enum):
    USER = "user"

"""
Manager API for creating and retrieving user profiles and user groups access rules.
"""
class EntitiesManager:
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
    Create a new user profile with the specified user properties.
    """
    async def create_user_profile(self, user_id: str, user_profile: UserProfile) -> UserProfile:
        try:
            item = user_profile.model_dump()
            partition_key = PartitionType.USER.value
            created_item = await self.container.create_item(user_id, partition_key, item)
            return UserProfile(**created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"User profile with user ID {user_id} already exists.")
        except Exception as e:
            raise Exception(f"Error creating user profile: {str(e)}")
        
    """
    Retrieves and deserializes a user profile with the specified user ID.
    Returns None if no such profile exists.
    Raises an exception if deserialization of any expected property fails.
    """
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        try:
            item = await self.container.get_item(user_id, PartitionType.USER.value)
            if item is None:
                return None
            
            return UserProfile(**item)
        except Exception as e:
            raise Exception(f"Error getting user profile with user ID {user_id}: {str(e)}")
    
    """
    Retrieves and deserializes all user profiles.
    Raises an exception if deserialization of any expected property fails.
    """
    async def get_all_user_profiles(self) -> List[UserProfile]:
        try:
            items = await self.container.get_all_items(PartitionType.USER.value)
            user_profiles: List[UserProfile] = []

            for item in items:
                user_profiles.append(UserProfile(**item))

            return user_profiles
        except Exception as e:
            raise Exception(f"Error getting all user profiles: {str(e)}")
    