# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from pydantic import BaseModel, field_serializer
from typing import Optional


class UserGender(Enum):
    """
    The gender of the user.
    """

    male = "Male"
    female = "Female"
    other = "Other"


class UserRole(str, Enum):
    """
    Enum for user roles in the system.
    """

    CUSTOMER = "customer"
    ADVISOR = "advisor"
    USER = "user"


class UserProfile(BaseModel):
    """ "
    Represents a user's profile information including name, description and demographic details.
    """

    id: str
    user_name: str
    description: str
    gender: UserGender
    age: Optional[int] = None
    role: Optional[UserRole] = UserRole.USER

    @field_serializer("gender")
    def serialize_gender(self, gender: UserGender, _info) -> str:
        return str(gender.value)

    @field_serializer("role")
    def serialize_role(self, role: UserRole, _info) -> str:
        return str(role.value)
