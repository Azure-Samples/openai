import datetime
from typing import List
from data.user_profiles.contracts.user_profile import AutoInsuranceClaim

"""
Object representing a flat-structure user profile.
"""
class UserProfileFlat:
    def __init__(self, user_id: str, user_name: str, home_address: str, customer_since: datetime.date, auto_insurance: bool, auto_insurance_deductible: float, 
                 auto_insurance_claim_history: List[AutoInsuranceClaim], safe_driver_rating: float, home_insurance: bool, flood_insurance: bool, 
                 flood_risk_factor: float, bundling_discount: bool, safe_driver_discount: bool, tracking_device_discount: bool):
        self.user_id = user_id
        self.user_name = user_name
        self.home_address = home_address
        self.customer_since = customer_since
        self.auto_insurance = auto_insurance
        self.auto_insurance_deductible = auto_insurance_deductible
        self.auto_insurance_claim_history = auto_insurance_claim_history
        self.safe_driver_rating = safe_driver_rating
        self.home_insurance = home_insurance
        self.flood_insurance = flood_insurance
        self.flood_risk_factor = flood_risk_factor
        self.bundling_discount = bundling_discount
        self.safe_driver_discount = safe_driver_discount
        self.tracking_device_discount = tracking_device_discount

    def to_item(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "home_address": self.home_address,
            "customer_since": self.customer_since.isoformat(),
            "auto_insurance": self.auto_insurance,
            "auto_insurance_deductible": self.auto_insurance_deductible,
            "auto_insurance_claim_history": [claim.to_item() for claim in self.auto_insurance_claim_history],
            "safe_driver_rating": self.safe_driver_rating,
            "home_insurance": self.home_insurance,
            "flood_insurance": self.flood_insurance,
            "flood_risk_factor": self.flood_risk_factor,
            "bundling_discount": self.bundling_discount,
            "safe_driver_discount": self.safe_driver_discount,
            "tracking_device_discount": self.tracking_device_discount
        }

    def __str__(self):
        dict = {
            "Insurer's Name": self.user_name,
            "Membership Start Date": self.customer_since.strftime("%B %Y"),
            "Home Address": self.home_address,            
            "Auto Insurance": "Yes" if self.auto_insurance == True else "No",
            "Auto Insurance Deductible": f"${int(self.auto_insurance_deductible)} per incident",
            "Auto Insurance Claims History": "; ".join([str(claim) for claim in self.auto_insurance_claim_history]) if len(self.auto_insurance_claim_history) > 0 else "None",
            "Safe Driver Rating": f"{int(self.safe_driver_rating * 100)} of 100",
            "Home Insurance": "Yes" if self.home_insurance == True else "No",
            "Flood Insurance": "Yes" if self.flood_insurance == True else "No",
            "Flood Risk Factor": f"{int(self.flood_risk_factor * 10)} of 10",
            "Bundling Discount": "Yes" if self.bundling_discount == True else "No",
            "Safe Driver Discount": "Yes" if self.safe_driver_discount == True else "No",
            "Driving Habit Tracking Device Discount": "Yes" if self.tracking_device_discount == True else "No"
        }
        return str('\n'.join("{}: {}".format(k, v) for k, v in dict.items()))