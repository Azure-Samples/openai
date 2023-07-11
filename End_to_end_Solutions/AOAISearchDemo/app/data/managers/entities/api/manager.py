from azure.cosmos import CosmosClient
from common.contracts.group import User, UserGroup
from common.contracts.user_profile import UserProfile
from common.contracts.resource import ResourceProfile, ResourceTypes
from data.cosmosdb.container import CosmosConflictError, CosmosDBContainer
from enum import Enum
from typing import Any, Dict, List, Optional, Set

class UserGroupNotFoundError(BaseException):
    pass

class PartitionType(Enum):
    USER = "user"
    GROUP = "group"
    RESOURCE = "resource"

"""
Manager API for creating and retrieving user profiles and user groups access rules.
"""
class EntitiesManager:
    PARTITION_KEY_NAME = "partition_key"
    UNIQUE_KEYS = [
        {"paths": [f"/user_id", "/group_id", "/resource_id"]}
    ]

    def __init__(self, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_entities_container_name: str):
        cosmos_client = CosmosClient(url=cosmos_db_endpoint, credential=cosmos_db_credential, consistency_level="Session")
        self.container = CosmosDBContainer(cosmos_db_name, cosmos_db_entities_container_name, self.PARTITION_KEY_NAME, cosmos_client, self.UNIQUE_KEYS)
    
    """
    Create a new user profile with the specified user properties.
    """
    def create_user_profile(self, user_id: str, user_name: str, description: str, sample_questions: List[str] = []) -> UserProfile:
        user_profile = UserProfile(user_id, user_name, description, sample_questions)
        try:
            item = user_profile.to_item()
            partition_key = PartitionType.USER.value
            created_item = self.container.create_item(user_id, partition_key, item)
            return UserProfile.as_item(created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"User profile with user ID {user_id} already exists.")

    """
    Retrieves and deserializes a user profile with the specified user ID.
    Returns None if no such profile exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        item = self.container.get_item(user_id, PartitionType.USER.value)
        if item is None:
            return None
        
        return UserProfile.as_item(item)
    
    """
    Retrieves and deserializes all user profiles.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_all_user_profiles(self) -> List[UserProfile]:
        items = self.container.get_all_items(PartitionType.USER.value)
        user_profiles: List[UserProfile] = []

        for item in items:
            user_profiles.append(UserProfile.as_item(item))

        return user_profiles
    
    """
    Create a new user group with the specified group properties.
    """
    def create_user_group(self, group_id: str, group_name: str, users: Set[User] = set()) -> UserGroup:
        user_group = UserGroup(group_id, group_name, users)
        try:
            item = user_group.to_item()
            partition_key = PartitionType.GROUP.value
            created_item = self.container.create_item(group_id, partition_key, item)

            return UserGroup.as_item(created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"User group with group ID {group_id} already exists.")

    """
    Retrieves and deserializes a user group with the specified group ID.
    Returns None if no such user group exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_user_group(self, group_id: str) -> Optional[UserGroup]:
        item = self.container.get_item(group_id, PartitionType.GROUP.value)
        if item is None:
            return None
        
        return UserGroup.as_item(item)
    
    """
    Retrieves and deserializes all user groups the user with the specified user ID belongs to.
    Returns None if no such user exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_user_member_groups(self, user_id: str) -> Optional[List[UserGroup]]:
        if self.get_user_profile(user_id) is None:
            return None

        query = "SELECT * FROM c WHERE ARRAY_CONTAINS(c.users, {'user_id': @user_id})"
        params: List[Dict[str, object]] = [
            dict(name="@user_id", value=user_id)
        ]
        partition_key = PartitionType.GROUP.value
        items = self.container.query_items(query, params, partition_key)        
        groups: List[UserGroup] = []
        for item in items:
            groups.append(UserGroup.as_item(item))

        return groups
    
    """
    Adds a new user or users to the user group with the specified group ID.
    Raises an exception if no user group exists with the specified group ID.
    """
    def add_users_to_user_group(self, group_id: str, users: Set[User]) -> UserGroup:
        user_group = self.get_user_group(group_id)
        if user_group is None:
            raise UserGroupNotFoundError(f"User group with group ID {group_id} could not be found.")
        user_group.add_users(users)
        item = user_group.to_item()
        partition_key = PartitionType.GROUP.value
        updated_item = self.container.update_item(group_id, partition_key, item)
        return UserGroup.as_item(updated_item)

    """
    Create a new resource with the specified resource properties.
    """
    def create_resource(self, resource_id: str, resource_name: ResourceTypes) -> ResourceProfile:
        resource = ResourceProfile(resource_id, resource_name)
        try:
            item = resource.to_item()
            partition_key = PartitionType.RESOURCE.value
            created_item = self.container.create_item(resource_id, partition_key, item)
            return ResourceProfile.as_item(created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"Resource with resource ID {resource_id} already exists.")
        
    """
    Retrieves and deserializes a resource with the specified resource ID.
    Returns None if no such resource exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_resource(self, resource_id: str) -> Optional[ResourceProfile]:
        item = self.container.get_item(resource_id, PartitionType.RESOURCE.value)
        if item is None:
            return None
        
        return ResourceProfile.as_item(item)