# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# filepath: c:\Users\manniarora\dev\cxe-eng\agents\src\solution_accelerators\customer_assist\conversation_simulator\conversation_simulator.py
# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime
import json
import logging
import os
import base64
import random
from typing import List, Dict, Optional
import yaml

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


# Define agent roles and instructions
ADVISOR_AGENT_NAME = "AdvisorAgent"
ADVISOR_INSTRUCTIONS = """
You are John. Begin the conversation with a brief, friendly greeting that states your name and asks how you can help. 
Always generate small, natural sentences and avoid long speeches.
When customer share their problem, suggest suitable products from the following options:
• Personal Loan
• Business Loan

Once the customer agrees to the type of loan, gradually collect these key details in small increments (ask them as needed, not all at once). 
Confirm each detail before moving on to the next. For any form field and verification document, ask for one at a time.
 Once the customer provides any document, say that the document is received and this might take a few minutes to process. 
Avoid any long speeches or overwhelming the customer with information. Always ask for all of the following information:
• First and Last Name
• Email Address
• Address
• Agreed Loan Type
• Agreed Loan Amount
• Loan Term (in months)
• Credit Score
• Verification Documents ID Proof
• Verification Documents Utility Bill

Ask for all of the above information.
Once the customer has provided all the necessary information, confirm that the application is complete. If any more information is needed, you will reach out to them. 
Otherwise, they'll hear from us once the application is processed. Never generate dialogs from the customer perspective. Once all the information is collected, say that you need to process the application and it might take a few minutes.
And after two to three dialogs, say that the application is complete and you will reach out to them once it is processed.
"""

CUSTOMER_AGENT_NAME = "CustomerAgent"
CUSTOMER_BASE_INSTRUCTIONS = """
You are a banking customer. You want to apply for personal loan (e.g., to buy a bike, clear your credit card debt, or medical expenses) or business loan (for your coffee shop). 
Speak naturally and share relevant information as the conversation progresses. Ask clarifying questions if unsure about banking products or requirements.
Provide details as the advisor requests them without overwhelming the conversation or asking what's next. If you are missing any information, mention that you will provide it later. 
By the end, you should either have a loan application filled or a clear follow-up plan. 
Always generate small but natural sentences and avoid long speeches.
When asked for verification documents:
- If asked for ID proof, say "Here's my driver's license" or "I'm sending you my identification proof now"
- If asked for utility bill, say "Here's my water bill" or "I'm sending you my utility bill"

End the conversation by saying 'goodbye.' Never generate dialogs from the advisor's perspective.

Here are your details:
"""

TASK = "To simulate a conversation between a banking advisor and a customer, the customer needs to apply for a loan. The advisor should guide the customer through the process."


# Path to verification documents and user details
VERIFICATION_DOCS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "verification_documents",
)

USER_DETAILS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "user_details.yaml")


def load_image_as_base64(image_name):
    """Load an image from the verification documents folder and encode it as base64."""
    try:
        image_path = os.path.join(VERIFICATION_DOCS_PATH, image_name)
        if not os.path.exists(image_path):
            return None, f"Image file not found: {image_path}"

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_string, None
    except Exception as e:
        return None, f"Error loading image: {str(e)}"


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    """Create a kernel with Azure chat completion service."""
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "goodbye" in history[-1].content.lower()


class Message:
    """Message class to store conversation messages."""

    def __init__(
        self,
        role: str,
        text: str,
        image_url: Optional[str] = None,
        image_description: Optional[str] = None,
    ):
        self.role = role  # 'advisor' or 'customer'
        self.text = text
        self.timestamp = datetime.now().isoformat()
        self.image_url = image_url
        self.image_description = image_description

    def to_dict(self):
        """Convert message to dictionary."""
        message_dict = {
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp,
        }

        # Add image data if available
        if self.image_url:
            message_dict["image_url"] = self.image_url
            message_dict["image_description"] = self.image_description

        return message_dict


class ConversationSimulator:
    """Class to manage a simulated conversation between a banking advisor and a customer."""

    def __init__(
        self,
        session_id: str,
        logger: logging.Logger,
    ):
        """Initialize the conversation simulator."""
        self.session_id = session_id
        self.logger = logger
        self.group_chat = None
        self.chat_generator = None
        self.messages: List[Message] = []
        self.is_running = False

    async def start(self) -> bool:
        """Start the conversation simulation."""
        try:
            # Load user details
            self.user_details, error = load_user_details()
            if error:
                self.logger.error(f"[Session {self.session_id}] Error loading user details: {error}")
                return False

            # Format customer instructions with user details
            customer_instructions = CUSTOMER_BASE_INSTRUCTIONS + format_user_details(self.user_details)

            # Create the advisor agent
            advisor_agent = ChatCompletionAgent(
                kernel=_create_kernel_with_chat_completion("advisor"),
                name=ADVISOR_AGENT_NAME,
                instructions=ADVISOR_INSTRUCTIONS,
            )

            # Create the customer agent
            customer_agent = ChatCompletionAgent(
                kernel=_create_kernel_with_chat_completion("customer"),
                name=CUSTOMER_AGENT_NAME,
                instructions=customer_instructions,
            )

            # Set up the group chat
            self.group_chat = AgentGroupChat(
                agents=[advisor_agent, customer_agent],
                termination_strategy=ApprovalTerminationStrategy(
                    agents=[advisor_agent, customer_agent],
                    maximum_iterations=40,
                ),
            )

            # Add the task as a message to the group chat
            await self.group_chat.add_chat_message(message=TASK)

            # Initialize the generator
            self.chat_generator = self.group_chat.invoke()

            # Mark conversation as running
            self.is_running = True
            return True
        except Exception as e:
            self.logger.error(f"[Session {self.session_id}] Error starting conversation: {str(e)}")
            import traceback
            self.logger.error(f"[Session {self.session_id}] Traceback: {traceback.format_exc()}")
            return False

    async def get_next_message(self) -> Optional[Message]:
        """Get the next message in the conversation."""
        if not self.is_running or not self.group_chat:
            self.logger.warning(f"[Session {self.session_id}] Cannot get next message: conversation not running")
            return None

        try:
            # Get the next message from the generator
            content = await anext(self.chat_generator)

            # Format the role name for output
            agent_role = "advisor" if content.name == "AdvisorAgent" else "customer"

            # Check if this message should include an image (only for customer messages)
            image_url = None
            image_description = None

            if agent_role == "customer":
                message_text = content.content.lower()

                # Check for ID proof references
                if any(
                    phrase in message_text
                    for phrase in [
                        "driver's license",
                        "identification",
                        "driver license",
                    ]
                ):
                    image_name = self.user_details["id_proof"]
                    encoded_image, error = load_image_as_base64(image_name)
                    if encoded_image:
                        image_url = f"data:image/png;base64,{encoded_image}"
                        image_description = "Driver's License - ID Proof"
                    else:
                        self.logger.error(f"[Session {self.session_id}] Error loading ID proof image: {error}")

                # Check for utility bill references
                elif any(phrase in message_text for phrase in ["water bill", "utility bill", "bill"]):
                    image_name = self.user_details["utility_bill"]
                    encoded_image, error = load_image_as_base64(image_name)
                    if encoded_image:
                        image_url = f"data:image/png;base64,{encoded_image}"
                        image_description = "Water Bill - Utility Bill"
                    else:
                        self.logger.error(f"[Session {self.session_id}] Error loading utility bill image: {error}")

            # Create a message object
            message = Message(
                role=agent_role,
                text=content.content,
                image_url=image_url,
                image_description=image_description,
            )

            # Add to message history
            self.messages.append(message)

            return message
        except StopAsyncIteration:
            # End of conversation
            self.logger.info(f"[Session {self.session_id}] Conversation completed naturally")
            self.is_running = False

            return None
        except Exception as e:
            self.logger.error(f"[Session {self.session_id}] Error getting next message: {str(e)}")
            return None

    async def stop(self) -> bool:
        """Stop the conversation simulation."""
        if not self.is_running:
            self.logger.warning(f"[Session {self.session_id}] Conversation already stopped")
            return True

        try:
            # Mark conversation as not running
            self.is_running = False

            self.logger.info(f"[Session {self.session_id}] Conversation stopped manually")
            return True
        except Exception as e:
            self.logger.error(f"[Session {self.session_id}] Error stopping conversation: {str(e)}")
            return False

    def get_all_messages(self) -> List[Dict]:
        """Get all messages from the conversation."""
        return [msg.to_dict() for msg in self.messages]


def load_user_details(user_id: int = None) -> Optional[Dict]:
    """Load user details from the YAML file."""
    try:
        if not os.path.exists(USER_DETAILS_PATH):
            return None, f"User details file not found: {USER_DETAILS_PATH}"

        with open(USER_DETAILS_PATH, "r") as file:
            user_data = yaml.safe_load(file)

        # Randomly select a user if no user_id is provided
        if not user_id:
            user_id = random.choice(user_data.get("user_profiles", [])).get("user_id")

        # Find the user with the specified ID
        for user in user_data.get("user_profiles", []):
            if user.get("user_id") == user_id:
                return user, None

        return None, f"User with ID {user_id} not found"
    except Exception as e:
        return None, f"Error loading user details: {str(e)}"


def format_user_details(user: Dict) -> str:
    """Format user details for inclusion in agent instructions."""
    return f"""
        First Name: {user.get('first_name', 'Unknown')}
        Last Name: {user.get('last_name', 'Unknown')}
        Address: {user.get('address', 'Unknown')}
        Credit Score: {user.get('credit_score', 'Unknown')}
        Preferred Loan Type: {user.get('loan_type', 'Unknown')}
        Customer Sentiment: {user.get('customer_sentiment', 'Neutral')}
        Email: {user.get('email', 'Unknown')}
    """
