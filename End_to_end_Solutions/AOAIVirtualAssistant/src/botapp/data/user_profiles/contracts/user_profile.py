import datetime
from enum import Enum
from typing import List, Optional
from data.faqs.contracts.faq import InsuranceType

class AutoInsuranceClaim():
    def __init__(self, claim_date: datetime.date, claim_amount: float, claim_reason: str):
        self.claim_date = claim_date
        self.claim_amount = claim_amount
        self.claim_reason = claim_reason

    def to_item(self) -> dict:
        return {
            "claim_date": self.claim_date.isoformat(),
            "claim_amount": self.claim_amount,
            "claim_reason": self.claim_reason
        }
    
    def __str__(self):
        return f"{self.claim_reason} in {self.claim_date.strftime('%B %Y')}"

class AutoInsuranceProperties():
    def __init__(self, safe_driver_rating: float, claim_history: List[AutoInsuranceClaim], deductible: float , discount: bool):
        self.safe_driver_rating = safe_driver_rating
        self.claim_history = claim_history
        self.deductible = deductible
        self.discount = discount

    def to_item(self) -> dict:
        return {
            "safe_driver_rating": self.safe_driver_rating,
            "claim_history": [claim.to_item() for claim in self.claim_history],
            "deductible": self.deductible,
            "discount": self.discount
        }

class PropertyStatus(Enum):
    renter = "renter"
    owner = "owner"

class HomeInsuranceProperties():
    def __init__(self, property_status: PropertyStatus):
        self.property_status = property_status

    def to_item(self) -> dict:
        return {
            "property_status": self.property_status.value
        }

class FloodInsuranceProperties():
    def __init__(self, flood_risk_factor: float):
        self.flood_risk_factor = flood_risk_factor

    def to_item(self) -> dict:
        return {
            "flood_risk_factor": self.flood_risk_factor
        }

"""
Object representing a user profile.
"""
class UserProfile:
    def __init__(self, user_id: str, user_name: str, home_address: str, customer_since: datetime.date, 
                    insurance_types: List[InsuranceType] = [], bundles: List[InsuranceType] = [],
                    auto_insurance_properties: Optional[AutoInsuranceProperties] = None, home_insurance_properties: Optional[HomeInsuranceProperties] = None,
                    flood_insurance_properties: Optional[FloodInsuranceProperties] = None):
        self.user_id = user_id
        self.user_name = user_name
        self.insurance_types = insurance_types
        self.bundles = bundles
        self.home_address = home_address
        self.customer_since = customer_since
        self.auto_insurance_properties = auto_insurance_properties
        self.home_insurance_properties = home_insurance_properties
        self.flood_insurance_properties = flood_insurance_properties

    def to_item(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "insurance_types": [insurance_type.value for insurance_type in self.insurance_types],
            "bundles": [insurance_type.value for insurance_type in self.bundles],
            "home_address": self.home_address,
            "customer_since": self.customer_since.isoformat(),
            "auto_insurance_properties": self.auto_insurance_properties.to_item() if self.auto_insurance_properties is not None else None,
            "home_insurance_properties": self.home_insurance_properties.to_item() if self.home_insurance_properties is not None else None,
            "flood_insurance_properties": self.flood_insurance_properties.to_item() if self.flood_insurance_properties is not None else None
        }