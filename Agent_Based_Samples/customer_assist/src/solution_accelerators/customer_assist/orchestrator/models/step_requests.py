# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from semantic_kernel.contents import ChatHistory
from common.contracts.common.user_profile import UserRole
from models.advisor_customer_conversation import (
    AdvisorCustomerChatHistory,
    AdvisorCustomerDialog,
)
from models.loan_application_form import LoanApplicationForm
from models.step_responses import SentimentAnalysis, PostCallAnalysis, AdvisorInsights


class ProcessConversationRequest(BaseModel):
    """Request model for ProcessConversationStep."""

    # Customer information from existing user profile
    customer_profile: Dict[str, Any] = None
    advisor_customer_dialog: AdvisorCustomerDialog = None


class SentimentAnalysisRequest(BaseModel):
    """Request model for SentimentAnalysisStep."""

    advisor_customer_chat_history: AdvisorCustomerChatHistory = None


class PostCallAnalysisRequest(BaseModel):
    """Request model for PostCallAnalysisStep."""

    chat_history: AdvisorCustomerChatHistory = None
    completed_form: LoanApplicationForm = None
    sentiment_analysis: SentimentAnalysis = None


class ConsolidateInsightsRequest(BaseModel):
    """Request model for ConsolidateInsightsStep."""

    advisor_insights: Optional[AdvisorInsights] = None
    advisor_customer_chat_history: Optional[AdvisorCustomerChatHistory] = None
    sentiment_analysis: Optional[SentimentAnalysis] = None
    post_call_analysis: Optional[PostCallAnalysis] = None
    form_data: Optional[LoanApplicationForm] = None
