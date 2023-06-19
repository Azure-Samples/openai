import json

from common.utilities.property_item_reader import read_item_property_with_type, read_item_property_with_enum, MissingPropertyError
from enum import Enum
from typing import List

class MemberType(Enum):
    USER="user"
    GROUP="group"

class Member:
    def __init__(self, id: str, member_type: MemberType):
        self.id = id
        self.member_type = member_type

    def to_item(self) -> dict:
        return {
            "id": self.id,
            "member_type": self.member_type.value
        }
    
    @staticmethod
    def as_item(dct: dict):
        id = read_item_property_with_type(dct, "id", str, Member)
        valid_member_types = [type.value for type in MemberType]
        member_type = read_item_property_with_enum(dct, "member_type", valid_member_types, MemberType, Member)
        return Member(id, member_type)
    
class Resource:
    def __init__(self, resource_id: str):
        self.resource_id = resource_id

    def to_item(self) -> dict:
        return {
            "resource_id": self.resource_id,
        }
    
    @staticmethod
    def as_item(dct: dict):
        resource_id = read_item_property_with_type(dct, "resource_id", str, Resource)
        return Resource(resource_id)

"""
Object representing a resource access rule.
"""
class AccessRule:
    def __init__(self, rule_id: str, resources: List[Resource], members: List[Member]):
        self.rule_id = rule_id
        self.resources = resources
        self.members = members

    def to_item(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "resources": [resource.to_item() for resource in self.resources],
            "members": [member.to_item() for member in self.members]
        }
    
    @staticmethod
    def as_item(dct: dict):
        rule_id = read_item_property_with_type(dct, "rule_id", str, AccessRule)
        resources_dict = read_item_property_with_type(dct, "resources", list, AccessRule)
        members_dict = read_item_property_with_type(dct, "members", list, AccessRule)

        resources: List[Resource] = []
        for resource_dict in resources_dict:
            resources.append(Resource.as_item(resource_dict))
        
        members: List[Member] = []
        for member_dict in members_dict:
            members.append(Member.as_item(member_dict))

        return AccessRule(rule_id, resources, members)
    
    @staticmethod
    def as_payload(payload: str):
        dct = json.loads(payload)

        try:
            return AccessRule.as_item(dct)
        except MissingPropertyError:
            raise Exception(f"Invalid AccessRule payload.")