# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from datetime import date

from common.telemetry.app_logger import AppLogger
from models.loan_application_form import (
    AddressVerification,
    IdentificationDetails,
    LoanApplicationForm,
    PersonalInformation,
    LoanInformation,
    FinancialInformation,
    LoanPurpose,
)


class FormPlugin:
    """Plugin for handling loan application form updates."""

    _logger: AppLogger = None

    def __init__(self, logger):
        self._logger = logger
        self.form = LoanApplicationForm(
            submission_date=date.today(),
            personal_info=PersonalInformation(),
            loan_info=LoanInformation(),
            financial_info=FinancialInformation(),
            address_verification=AddressVerification(),
            identification_details=IdentificationDetails(),
        )

    @kernel_function
    def update_first_name(self, first_name: str) -> str:
        self._logger.info(f"Updating first name to: {first_name}")
        self.form.personal_info.first_name = first_name
        return f"✅ First name updated to: {first_name}"

    @kernel_function
    def update_last_name(self, last_name: str) -> str:
        self._logger.info(f"Updating last name to: {last_name}")
        self.form.personal_info.last_name = last_name
        return f"✅ Last name updated to: {last_name}"

    @kernel_function
    def update_email(self, email: str) -> str:
        self._logger.info(f"Updating email to: {email}")
        self.form.personal_info.email = email
        return f"✅ Email updated to: {email}"

    @kernel_function
    def update_loan_amount(self, amount: str) -> str:
        self._logger.info(f"Updating loan amount to: {amount}")
        self.form.loan_info.loan_amount = float(amount)
        return f"✅ Loan amount updated to: {amount}"

    @kernel_function
    def update_loan_purpose(self, purpose: str) -> str:
        try:
            self._logger.info(f"Updating loan purpose to: {purpose}")
            self.form.loan_info.loan_purpose = LoanPurpose(purpose)
            return f"✅ Loan purpose updated to: {purpose}"
        except ValueError:
            return f"❌ Invalid loan purpose: {purpose}. Valid options are: {[p.value for p in LoanPurpose]}."

    @kernel_function
    def update_credit_score(self, score: str) -> str:
        if not score or not score.isdigit():
            score = "0"
        self._logger.info(f"Updating credit score to: {score}")
        self.form.financial_info.credit_score = int(score)
        return f"✅ Credit score updated to: {score}"

    @kernel_function(
        description="Update identification details of the applicant, including extracted document number and expiry date."
    )
    def update_identification_details(self, drivers_license_number: str, expiry_date: str) -> str:
        self._logger.info(
            f"Updating identification details: Document Number: {drivers_license_number}, Expiry Date: {expiry_date}"
        )
        self.form.identification_details.drivers_license_number = drivers_license_number
        self.form.identification_details.expiry_date = expiry_date
        return (
            f"✅ Identification details updated: Document Number: {drivers_license_number}, Expiry Date: {expiry_date}"
        )

    @kernel_function(
        description="Update address verification status. Set is_verified to true if verified using a document."
    )
    def update_address_verification(self, full_address: str, is_verified: bool) -> str:
        self._logger.info(f"Updating address verification: {full_address}, Verified: {is_verified}")
        self.form.address_verification.full_address = full_address
        self.form.address_verification.is_verified = is_verified
        return f"✅ Address verification updated: {full_address}, Verified: {is_verified}"
    
    @kernel_function(description="Update the loan term in months and calculate the expiration date.")
    def update_loan_term(self, loan_term: str) -> str:
        self._logger.info(f"Updating loan term to: {loan_term} months")
        self.form.loan_info.loan_term = loan_term

        # Get current date
        current_date = date.today()
        total_months = current_date.month + int(loan_term)

        # Compute new year and month
        new_year = current_date.year + (total_months - 1) // 12
        new_month = (total_months - 1) % 12 + 1

        # Set expiration date to the 1st of that month
        expiration_date = date(new_year, new_month, 1).strftime("%Y-%m-%d")
        self.form.loan_info.loan_term_expiration_date = expiration_date

        self._logger.info(f"Loan term expiration date set to: {expiration_date}")
        return f"✅ Loan term updated to: {loan_term} months, Expiration Date: {expiration_date}"
