# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Any, Dict, List

from pydantic import BaseModel
from common.contracts.common.user_profile import UserRole


class AdvisorCustomerDialog(BaseModel):
    """Model for advisor-customer chat history."""

    message: str
    user_role: UserRole

    def to_dict(self) -> Dict[str, Any]:
        """Convert the chat history to a dictionary."""
        return {
            "message": self.message,
            "user_role": self.user_role.value,
        }


class AdvisorCustomerChatHistory(BaseModel):
    """Model for advisor-customer chat history."""

    dialogs: List[AdvisorCustomerDialog] = []

    def append_dialog(self, message: str, user_role: UserRole) -> None:
        """Add a message to the chat history."""
        self.dialogs.append(AdvisorCustomerDialog(message=message, user_role=user_role))

    def append_advisor_customer_dialog(self, advisor_customer_dialog: AdvisorCustomerDialog) -> None:
        """Add a advisor-customer dialog to the chat history."""
        self.dialogs.append(advisor_customer_dialog)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert the chat history to a list of dictionaries."""
        return [dialog.to_dict() for dialog in self.dialogs]
