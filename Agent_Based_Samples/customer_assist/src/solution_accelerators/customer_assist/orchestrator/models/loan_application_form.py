# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import Optional, List
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, constr


class LoanPurpose(str, Enum):
    """Valid loan purposes."""

    BUSINESS = "BUSINESS"
    PERSONAL = "PERSONAL"


class PersonalInformation(BaseModel):
    """Personal information section of loan application."""

    first_name: str | None = Field(None, min_length=2)
    last_name: str | None = Field(None, min_length=2)
    email: str | None = None


class LoanInformation(BaseModel):
    """Loan-specific information."""

    loan_purpose: LoanPurpose | None = None
    loan_amount: float | None = Field(None, gt=0)
    loan_term: str | None = None  # Loan term in months
    loan_term_expiration_date: str | None = None # Expiration date of the loan term


class FinancialInformation(BaseModel):
    """Financial background information."""

    credit_score: Optional[int] = Field(None, ge=300, le=850)


class IdentificationDetails(BaseModel):
    """Identification details for the applicant."""

    drivers_license_number: str | None = Field(None, min_length=5)
    expiry_date: str | None = None


class AddressVerification(BaseModel):
    full_address: str | None = Field(None, min_length=5)
    is_verified: bool = False  # Set to true if verified using a document


class LoanApplicationForm(BaseModel):
    """Complete loan application form with all sections."""

    personal_info: PersonalInformation | None = None
    loan_info: LoanInformation | None = None
    financial_info: FinancialInformation | None = None
    address_verification: AddressVerification | None = None
    identification_details: IdentificationDetails | None = None

    def get_fields(self):
        return json.dumps(self.model_dump(), indent=2)
