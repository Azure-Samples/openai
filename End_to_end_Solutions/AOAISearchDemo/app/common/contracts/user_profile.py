import json
from typing import List

from common.utilities.property_item_reader import MissingPropertyError, read_item_property_with_type

"""
Object representing a user profile.
"""
class UserProfile:
    def __init__(self, user_id: str, user_name: str, description: str, sample_questions: List[str] = []):
        self.user_id = user_id
        self.user_name = user_name
        self.description = description
        self.sample_questions = sample_questions

    def to_item(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "description": self.description,
            "sample_questions": [question for question in self.sample_questions]
        }
    
    @staticmethod
    def as_item(dct: dict):
        user_id = read_item_property_with_type(dct, "user_id", str, UserProfile)
        user_name = read_item_property_with_type(dct, "user_name", str, UserProfile)
        description = read_item_property_with_type(dct, "description", str, UserProfile)
        sample_questions = read_item_property_with_type(dct, "sample_questions", list, UserProfile, optional=True)
        
        sample_questions = sample_questions if sample_questions is not None else []
        for question in sample_questions:
            if not isinstance(question, str):
                raise Exception(f"Invalid UserProfile payload. sample_questions must be a list of strings.")
        
        return UserProfile(user_id, user_name, description, sample_questions)
    
    @staticmethod
    def as_payload(payload: str):
        dct = json.loads(payload)

        try:
            return UserProfile.as_item(dct)
        except MissingPropertyError:
            raise Exception(f"Invalid UserProfile payload.")