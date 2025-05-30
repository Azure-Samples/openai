# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from string import Template

from azure.identity import ClientAssertionCredential, ManagedIdentityCredential
from msgraph import GraphServiceClient
from msgraph.generated.models import email_address as EmailAddress
from msgraph.generated.models import item_body as ItemBody
from msgraph.generated.models import message as Message
from msgraph.generated.models import recipient as Recipient
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)
from semantic_kernel.functions import kernel_function

from common.telemetry.app_logger import AppLogger

# Default Microsoft Entra Audience for Federated Identity Credentials
AUDIENCE = 'api://AzureADTokenExchange'

class NotificationPlugin:
    def __init__(
        self,
        logger: AppLogger,
        sender_email: str,
        receiver_email: str,
        email_template: Template,
        tenant_id: str,
        client_id: str,
        managed_identity_client_id: str,
    ):
        """
        Initializes the NotificationPlugin with Microsoft Graph credentials and email template.

        :param logger: Logger instance for logging messages
        :param sender_email: Email address of the sender
        :param receiver_email: Email address of the receiver
        :param email_template: Email template to use for the notification
        :param tenant_id: Azure AD tenant ID
        :param client_id: Azure AD application (client) ID
        :param managed_identity_client_id: Managed Identity client ID for authentication
        """
        self.logger = logger
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.email_template: Template = email_template

        def get_managed_identity_token(credential: ManagedIdentityCredential, audience: str):
            return credential.get_token(audience).token

        managed_identity_credential = ManagedIdentityCredential(client_id=managed_identity_client_id)
        credential = ClientAssertionCredential(
            tenant_id,
            client_id,
            lambda: get_managed_identity_token(managed_identity_credential, AUDIENCE)
        )

        self.client = GraphServiceClient(credential)

    @kernel_function(name="send_email", description="Send an email with the input message using Microsoft Graph.")
    def send_email(self, message: str) -> None:
        """
        Sends an email using Microsoft Graph.

        Args:
        message (str): Message body to be included in the email.
        """
        try:
            email_body = self.email_template.safe_substitute(message=message)

            # Create the email message
            message_obj = Message(
                subject="Release Manager: Update Notification",
                body=ItemBody(
                    content_type=BodyType.Html,
                    content=email_body,
                ),
                from_=Recipient(
                    email_address=EmailAddress(address=self.sender_email)
                ),
                to_recipients=[
                    Recipient(
                        email_address=EmailAddress(address=self.receiver_email)
                    )
                ],
            )

            # Create the request body for sending the email
            send_mail_body = SendMailPostRequestBody(message=message_obj, save_to_sent_items=True)

            # Use the GraphServiceClient to send the email
            asyncio.get_event_loop().run_until_complete(self.client.users.by_user_id(self.sender_email).send_mail.post(body=send_mail_body))

            self.logger.info(f"Email successfully sent to {self.receiver_email}")
        except Exception as ex:
            self.logger.error(f"Unexpected error: {ex}")
            raise
