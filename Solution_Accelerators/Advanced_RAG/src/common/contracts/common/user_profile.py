from enum import Enum
from pydantic import BaseModel, field_serializer
from typing import Optional

class UserGender(Enum):
    male = "Male"
    female = "Female"
    other = "Other"

"""
Model representing a user profile.
"""
class UserProfile(BaseModel):
    id: str
    user_name: str
    description: str
    gender: UserGender
    age: Optional[int] = None

    @field_serializer("gender")
    def serialize_gender(self, gender: UserGender, _info) -> str:
        return str(gender.value)
