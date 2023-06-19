import json

from typing import Set
from common.utilities.property_item_reader import MissingPropertyError, read_item_property_with_type

class User:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def __hash__(self):
        return hash(self.user_id)

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        else:
            return False

    def to_item(self) -> dict:
        return {
            "user_id": self.user_id
        }
    
    @staticmethod
    def as_item(dct: dict):
        user_id = read_item_property_with_type(dct, "user_id", str, User)
        
        return User(user_id)

"""
Object representing a user group.
"""
class UserGroup:
    def __init__(self, group_id: str, group_name: str, users: Set[User] = set()):
        self.group_id = group_id
        self.group_name = group_name
        self.users = users

    def add_users(self, users: Set[User]):
        self.users.update(users)

    def to_item(self) -> dict:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "users": [user.to_item() for user in self.users]
        }
    
    def to_item_no_users(self) -> dict:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
        }
    
    @staticmethod
    def as_item(dct: dict):
        group_id = read_item_property_with_type(dct, "group_id", str, UserGroup)
        group_name = read_item_property_with_type(dct, "group_name", str, UserGroup)
        users_dict = read_item_property_with_type(dct, "users", list, UserGroup)

        users: Set[User] = set()
        for user_dict in users_dict:
            users.add(User.as_item(user_dict))
        
        return UserGroup(group_id, group_name, users)
    
    @staticmethod
    def as_payload(payload: str):
        dct = json.loads(payload)

        try:
            return UserGroup.as_item(dct)
        except MissingPropertyError:
            raise Exception(f"Invalid UserGroup payload.")