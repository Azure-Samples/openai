import datetime
from typing import List, Optional
from data.faqs.contracts.faq import InsuranceType
from data.user_profiles.contracts.user_profile import AutoInsuranceClaim, AutoInsuranceProperties, FloodInsuranceProperties, HomeInsuranceProperties, PropertyStatus, UserProfile
from data.cosmosdb.api.container import CosmosDBContainer
from data.cosmosdb.utilities.property_item_reader import read_item_property_with_type, read_item_property_with_enum

"""
Manager API for creating and retrieving user profiles.
"""
class UserProfileManager:
    PARTITION_KEY_NAME = "user_id"
    UNIQUE_KEYS = [
        {'paths': ['/user_id']}
    ]

    def __init__(self, database_name: str, container_name: str):
        self.container = CosmosDBContainer(database_name, container_name, self.PARTITION_KEY_NAME, self.UNIQUE_KEYS)
    
    """
    Create a new user profile with the specified user properties.
    """
    def create_user_profile(self, user_id: str, user_name: str, home_address: str, customer_since: datetime.date, 
                            insurance_types: List[InsuranceType] = [], bundles: List[InsuranceType] = [],
                            auto_insurance_properties: Optional[AutoInsuranceProperties] = None, home_insurance_properties: Optional[HomeInsuranceProperties] = None,
                            flood_insurance_properties: Optional[FloodInsuranceProperties] = None):
        user_profile = UserProfile(user_id, user_name, home_address, customer_since, insurance_types, bundles, auto_insurance_properties, home_insurance_properties, flood_insurance_properties)
        self.container.create_item(user_id, user_profile.to_item())

    """
    Retrieves and deserializes a user profile with the specified user ID.
    Returns None if no such profile exists.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        item = self.container.get_item(user_id)
        if item is None:
            return None
        
        user_name = read_item_property_with_type(item, "user_name", str, UserProfile)
        insurance_types = read_item_property_with_type(item, "insurance_types", list, UserProfile)
        valid_insurance_types = [type.value for type in InsuranceType]
        if not are_valid_enum_vals(insurance_types, valid_insurance_types):
            raise Exception("Invalid value for property insurance_types in object of type UserProfile. Property value must be one of the following: " + str([val.value for val in InsuranceType]))
        bundles = read_item_property_with_type(item, "bundles", list, UserProfile)
        if not are_valid_enum_vals(bundles, valid_insurance_types):
            raise Exception("Invalid value for property bundles in object of type UserProfile. Property value must be one of the following: " + str([val.value for val in InsuranceType]))
        home_address = read_item_property_with_type(item, "home_address", str, UserProfile)
        customer_since = read_item_property_with_type(item, "customer_since", datetime.date, UserProfile, datetime.date.fromisoformat)
        
        auto_insurance_properties_dict = read_item_property_with_type(item, "auto_insurance_properties", AutoInsuranceProperties, UserProfile, nullable=True)
        auto_insurance_properties: Optional[AutoInsuranceProperties] = None
        if auto_insurance_properties_dict != None:
            safe_driver_rating = read_item_property_with_type(auto_insurance_properties_dict, "safe_driver_rating", float, AutoInsuranceProperties, float)
            claim_history_dict = read_item_property_with_type(auto_insurance_properties_dict, "claim_history", list, AutoInsuranceProperties)
            claim_history = []
            for claim_dict in claim_history_dict:
                claim_date = read_item_property_with_type(claim_dict, "claim_date", datetime.date, AutoInsuranceClaim, datetime.date.fromisoformat)
                claim_amount = read_item_property_with_type(claim_dict, "claim_amount", float, AutoInsuranceClaim, float)
                claim_reason = read_item_property_with_type(claim_dict, "claim_reason", str, AutoInsuranceClaim)
                claim = AutoInsuranceClaim(claim_date, claim_amount, claim_reason)
                claim_history.append(claim)
            deductible = read_item_property_with_type(auto_insurance_properties_dict, "deductible", float, AutoInsuranceProperties, float)
            discount = read_item_property_with_type(auto_insurance_properties_dict, "discount", bool, AutoInsuranceProperties)
            auto_insurance_properties = AutoInsuranceProperties(safe_driver_rating, claim_history, deductible, discount)
        
        home_insurance_properties_dict = read_item_property_with_type(item, "home_insurance_properties", HomeInsuranceProperties, UserProfile, nullable=True)
        home_insurance_properties: Optional[HomeInsuranceProperties] = None
        if home_insurance_properties_dict != None:
            valid_property_statuses = [status.value for status in PropertyStatus]
            property_status = read_item_property_with_enum(home_insurance_properties_dict, "property_status", valid_property_statuses, PropertyStatus, HomeInsuranceProperties)
            home_insurance_properties = HomeInsuranceProperties(property_status)

        flood_insurance_properties_dict = read_item_property_with_type(item, "flood_insurance_properties", FloodInsuranceProperties, UserProfile, nullable=True)
        flood_insurance_properties: Optional[FloodInsuranceProperties] = None
        if flood_insurance_properties_dict != None:
            flood_risk_factor = read_item_property_with_type(flood_insurance_properties_dict, "flood_risk_factor", float, FloodInsuranceProperties, float)
            flood_insurance_properties = FloodInsuranceProperties(flood_risk_factor)

        return UserProfile(user_id, user_name, home_address, customer_since, insurance_types, bundles, auto_insurance_properties, home_insurance_properties, flood_insurance_properties)

def are_valid_enum_vals(vals: List[str], enum_vals: List[str]) -> bool:
    for val in vals:
        if val not in enum_vals:
            return False

    return True