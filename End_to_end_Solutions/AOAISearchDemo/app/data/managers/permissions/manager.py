from azure.cosmos import CosmosClient
from common.contracts.access_rule import AccessRule, Member, MemberType, Resource
from common.contracts.group import UserGroup
from common.contracts.user_profile import UserProfile
from data.cosmosdb.container import CosmosConflictError, CosmosDBContainer
from typing import Any, Dict, List, Set, Optional

"""
Manager API for creating and retrieving resources and resource access rules.
"""
class PermissionsManager:
    PARTITION_KEY_NAME = "partition_key"
    PARTITION_KEY_VALUE = "access_rule"
    UNIQUE_KEYS = [
        {"paths": ["/rule_id"]}
    ]

    def __init__(self, cosmos_db_endpoint: str, cosmos_db_credential: Any, cosmos_db_name: str, cosmos_db_permissions_container_name: str):
        cosmos_client = CosmosClient(url=cosmos_db_endpoint, credential=cosmos_db_credential, consistency_level="Session")
        self.container = CosmosDBContainer(cosmos_db_name, cosmos_db_permissions_container_name, self.PARTITION_KEY_NAME, cosmos_client, self.UNIQUE_KEYS)
    
    """
    Create a new resource access rule with the specified rule properties.
    """
    def create_access_rule(self, rule_id: str, resources: List[Resource], members: List[Member]) -> AccessRule:
        access_rule = AccessRule(rule_id, resources, members)
        try:
            item = access_rule.to_item()
            partition_key = self.PARTITION_KEY_VALUE
            created_item = self.container.create_item(rule_id, partition_key, item)
            return AccessRule.as_item(created_item)
        except CosmosConflictError:
            raise CosmosConflictError(f"Resource access rule with rule ID {rule_id} already exists.")
        
    """
    Retrieves and deserializes a resource access rule with the specified rule ID.
    Returns None if no such rule exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_access_rule(self, rule_id: str) -> Optional[AccessRule]:
        item = self.container.get_item(rule_id, self.PARTITION_KEY_VALUE)
        if item is None:
            return None
        
        return AccessRule.as_item(item)
    
    """
    Retrives and deserializes the set of resources the user with the specified user profile has access to.
    """
    def get_user_resources(self, user: UserProfile, user_groups: Optional[List[UserGroup]]) -> Set[Resource]:        
        query = "SELECT * FROM c WHERE ARRAY_CONTAINS(c.members, {'id': @id, 'member_type': @member_type})"
        params: List[Dict[str, object]] = [
            dict(name="@id", value=user.user_id),
            dict(name="@member_type", value=MemberType.USER.value)
        ]
        partition_key = self.PARTITION_KEY_VALUE
        items = self.container.query_items(query, params, partition_key)

        if not user_groups is None:
            for user_group in user_groups:
                params: List[Dict[str, object]] = [
                    dict(name="@id", value=user_group.group_id),
                    dict(name="@member_type", value=MemberType.GROUP.value)
                ]
                items.extend(self.container.query_items(query, params, partition_key))

        resources: Set[Resource] = set()
        for item in items:
            rule = AccessRule.as_item(item)
            for resource in rule.resources:
                resources.add(resource)

        return resources
