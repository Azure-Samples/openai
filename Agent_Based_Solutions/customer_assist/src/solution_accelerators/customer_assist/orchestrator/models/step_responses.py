# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from models.advisor_customer_conversation import AdvisorCustomerChatHistory
from models.loan_application_form import LoanApplicationForm


class LoanPolicyInsights(BaseModel):
    max_loan_amount: float = 0.0
    min_loan_term: int = 0
    max_loan_term: int = 0
    min_interest_rate: float = 0.0
    max_interest_rate: float = 0.0
    policy_summary: str = ""


class AdvisorInsights(BaseModel):
    missing_fields: List[str] = []
    next_question: str = ""
    document_verification_insights: str = ""
    document_verification_status: str = ""
    loan_policy_insights: LoanPolicyInsights = LoanPolicyInsights()

    def get_fields(self):
        return json.dumps(self.model_dump(), indent=2)


class Sentiment(Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class SentimentAnalysis(BaseModel):
    sentiment: str
    reasoning: str

    def __init__(self, sentiment: str, reasoning: str = ""):
        super().__init__(sentiment=sentiment, reasoning=reasoning)


class PostCallAnalysis(BaseModel):
    next_steps: List[str]
    summary: str
    overall_sentiment: str = ""
    overall_engagement: str = ""
    advisor_feedback: str = ""

    def __init__(
        self,
        next_steps: List[str] = [],
        summary: str = "",
        overall_sentiment: str = "",
        overall_engagement: str = "",
        advisor_feedback: str = "",
    ):
        super().__init__(
            next_steps=next_steps,
            summary=summary,
            overall_sentiment=overall_sentiment,
            overall_engagement=overall_engagement,
            advisor_feedback=advisor_feedback,
        )


class ConsolidatedInsights(BaseModel):
    advisor_insights: AdvisorInsights
    sentiment_analysis: SentimentAnalysis
    post_call_analysis: PostCallAnalysis
    advisor_customer_chat_history: AdvisorCustomerChatHistory
    form_data: LoanApplicationForm = None

    def __init__(
        self,
        advisor_insights: AdvisorInsights,
        sentiment_analysis: SentimentAnalysis,
        post_call_analysis: PostCallAnalysis,
        advisor_customer_chat_history: AdvisorCustomerChatHistory = None,
    ):
        super().__init__(
            advisor_insights=advisor_insights,
            sentiment_analysis=sentiment_analysis,
            post_call_analysis=post_call_analysis,
            advisor_customer_chat_history=advisor_customer_chat_history or AdvisorCustomerChatHistory(),
            form_data=LoanApplicationForm(),
        )
