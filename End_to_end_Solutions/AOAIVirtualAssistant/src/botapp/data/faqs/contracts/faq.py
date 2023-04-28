from enum import Enum
from typing import Optional

class InsuranceType(Enum):
    auto = "auto"
    home = "home"
    flood = "flood"
    renters = "renters"
    life = "life"

"""
Object representing all the information regarding a specific kind of insurance.
"""
class InsuranceInformation():
    def __init__(self, relevant_info: str, aux_info: Optional[str] = None):
        self.relevant_info = relevant_info
        self.aux_info = aux_info

"""
Object representing an FAQ for a specific kind of insurance.
"""
class FAQ:
    def __init__(self, insurance_type: InsuranceType, relevant_info: str, aux_info: Optional[str] = None):
        self.insurance_type = insurance_type
        self.info = InsuranceInformation(relevant_info, aux_info)