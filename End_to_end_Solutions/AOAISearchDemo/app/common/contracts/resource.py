import json

from enum import Enum
from common.utilities.property_item_reader import read_item_property_with_type, read_item_property_with_enum, MissingPropertyError

class ResourceTypes(Enum):
    COGNITIVE_SEARCH = "COGNITIVE_SEARCH"
    SQL_DB = "SQL_DB"

class ResourceProfile:
    def __init__(self, resource_id: str, resource_type: ResourceTypes):
        self.resource_id = resource_id
        self.resource_type = resource_type

    def to_item(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value
        }
    
    @staticmethod
    def as_item(dct: dict):
        resource_id = read_item_property_with_type(dct, "resource_id", str, ResourceProfile)
        valid_resource_types = [type.value for type in ResourceTypes]
        resource_type = read_item_property_with_enum(dct, "resource_type", valid_resource_types, ResourceTypes, ResourceProfile)
        return ResourceProfile(resource_id, resource_type)
    
    @staticmethod
    def as_payload(payload: str):
        dct = json.loads(payload)

        try:
            return ResourceProfile.as_item(dct)
        except MissingPropertyError:
            raise Exception(f"Invalid Resource payload.")