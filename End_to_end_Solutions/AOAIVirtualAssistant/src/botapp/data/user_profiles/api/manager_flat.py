import datetime
from typing import List, Optional
from data.user_profiles.contracts.user_profile_flat import UserProfileFlat
from data.user_profiles.contracts.user_profile import AutoInsuranceClaim
from data.cosmosdb.api.container import CosmosDBContainer
from data.cosmosdb.utilities.property_item_reader import read_item_property_with_type

"""
Manager API for creating and retrieving user profiles.
"""
class UserProfileManagerFlat:
    PARTITION_KEY_NAME = "user_id"
    UNIQUE_KEYS = [
        {'paths': ['/user_id']}
    ]

    def __init__(self, database_name: str, container_name: str):
        self.container = CosmosDBContainer(database_name, container_name, self.PARTITION_KEY_NAME, self.UNIQUE_KEYS)
    
    """
    Create a new user profile with the specified user properties.
    """
    def create_user_profile(self, user_id: str, user_name: str, home_address: str, customer_since: datetime.date, auto_insurance: bool, auto_insurance_deductible: float, 
                 auto_insurance_claim_history: List[AutoInsuranceClaim], safe_driver_rating: float, home_insurance: bool, flood_insurance: bool, 
                 flood_risk_factor: float, bundling_discount: bool, safe_driver_discount: bool, tracking_device_discount: bool):
        user_profile = UserProfileFlat(user_id, user_name, home_address, customer_since, auto_insurance, auto_insurance_deductible, auto_insurance_claim_history, safe_driver_rating,
            home_insurance, flood_insurance, flood_risk_factor, bundling_discount, safe_driver_discount, tracking_device_discount)
        self.container.create_item(user_id, user_profile.to_item())

    """
    Retrieves and deserializes a user profile with the specified user ID.
    Returns None if no such profile exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_user_profile(self, user_id: str) -> Optional[UserProfileFlat]:
        item = self.container.get_item(user_id)
        if item is None:
            return None
        
        user_name = read_item_property_with_type(item, "user_name", str, UserProfileFlat)
        home_address = read_item_property_with_type(item, "home_address", str, UserProfileFlat)
        customer_since = read_item_property_with_type(item, "customer_since", datetime.date, UserProfileFlat, datetime.date.fromisoformat)
        auto_insurance = read_item_property_with_type(item, "auto_insurance", bool, UserProfileFlat)
        auto_insurance_deductible = read_item_property_with_type(item, "auto_insurance_deductible", float, UserProfileFlat, float)
        auto_insurance_claim_history_dict = read_item_property_with_type(item, "auto_insurance_claim_history", list, UserProfileFlat)
        auto_insurance_claim_history = []
        for claim_dict in auto_insurance_claim_history_dict:
            claim_date = read_item_property_with_type(claim_dict, "claim_date", datetime.date, AutoInsuranceClaim, datetime.date.fromisoformat)
            claim_amount = read_item_property_with_type(claim_dict, "claim_amount", float, AutoInsuranceClaim, float)
            claim_reason = read_item_property_with_type(claim_dict, "claim_reason", str, AutoInsuranceClaim)
            claim = AutoInsuranceClaim(claim_date, claim_amount, claim_reason)
            auto_insurance_claim_history.append(claim)
        safe_driver_rating = read_item_property_with_type(item, "safe_driver_rating", float, UserProfileFlat, float)
        home_insurance = read_item_property_with_type(item, "home_insurance", bool, UserProfileFlat)
        flood_insurance = read_item_property_with_type(item, "flood_insurance", bool, UserProfileFlat)
        flood_risk_factor = read_item_property_with_type(item, "flood_risk_factor", float, UserProfileFlat, float)
        bundling_discount = read_item_property_with_type(item, "bundling_discount", bool, UserProfileFlat)
        safe_driver_discount = read_item_property_with_type(item, "safe_driver_discount", bool, UserProfileFlat)
        tracking_device_discount = read_item_property_with_type(item, "tracking_device_discount", bool, UserProfileFlat)

        return UserProfileFlat(user_id, user_name, home_address, customer_since, auto_insurance, auto_insurance_deductible, auto_insurance_claim_history, safe_driver_rating,
            home_insurance, flood_insurance, flood_risk_factor, bundling_discount, safe_driver_discount, tracking_device_discount)