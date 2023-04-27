from typing import Optional
from data.faqs.contracts.faq import InsuranceInformation
from data.faqs.contracts.faq import FAQ, InsuranceType
from data.cosmosdb.utilities.property_item_reader import read_item_property_with_type
from data.cosmosdb.api.container import CosmosDBContainer

"""
Manager API for retrieving insurance FAQs.
"""
class FAQManager:
    PARTITION_KEY_NAME = "insurance_type"
    UNIQUE_KEYS = [
        {'paths': ['/insurance_type']}
    ]

    def __init__(self, database_name: str, container_name: str):
        self.container = CosmosDBContainer(database_name, container_name, self.PARTITION_KEY_NAME)

    """
    Retrieves the FAQs for the specified type of insurance.
    Returns None if no FAQs exist for the specified type of insurance.
    Raises an exception if deserialization of any expected property fails.
    """
    def get_faqs(self, insurance_type: InsuranceType) -> Optional[FAQ]:
        item = self.container.get_item(insurance_type.value)
        if item is None:
            return None
        
        info = read_item_property_with_type(item, "info", dict, FAQ)
        relevant_info = read_item_property_with_type(info, "relevant_info", str, InsuranceInformation)
        aux_info = read_item_property_with_type(info, "aux_info", str, InsuranceInformation, nullable=True)
        return FAQ(insurance_type, relevant_info, aux_info)