'''
This is a duplicate of the file src/skills/cognitiveSearch/src/components/models/config_models.py
'''

import json
import logging
import os

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator
from pydantic.config import ConfigDict

class SearchType(str, Enum):
    keywords = "keywords"
    semantic = "semantic"
    vector = "vector"
    hybrid_keywords = "hybrid_keywords"
    hybrid_semantic = "hybrid_semantic"

class IndexApplicationType(str, Enum):
    image_description_search = "image_description_search"
    stock_search = "stock_search"
    price_search = "price_search"

class SearchFieldConfig(BaseModel):
    name: str = Field(description="Azure AI Search Index Field Name")
    is_item_id: bool = Field(description="Field contains item id - unique key", default=False)
    is_product_id: bool = Field(description="Field contains product id", default=False)
    is_product_category: bool = Field(description="Field is filterable and facetable that contains item categories", default=False)
    contains_image_description: bool = Field(description="Field contains image description of an item", default=False)
    contains_stock_data: bool = Field(description="Field contains stock related data", default=False)
    contains_price_data: bool = Field(description="Field contains price related data", default=False)

class IndexConfig(BaseModel):
    index_name: str = Field(
        description="Must match with the Index Name used in the Azure AI Search resource", )
    index_application: IndexApplicationType = Field(
        description="Application of the Search Index field data"
    )
    select_fields: List[SearchFieldConfig] = Field(
        description="Index Search Fields to be retrieved on search results")
    search_type: SearchType = Field(
        description="search type to be performed on the Search Index",
    )
    vector_configs: List[str] = Field(
        description="vector config names to be used for vector or hybrid search", default=[])
    semantic_config: Optional[str] = Field(
        description="semantic config names to be used for semantic or hybrid semantic search", default=None)

    @root_validator(pre=True, allow_reuse=True)
    def validate_search_type_configs(cls, values):
        search_type = values.get("search_type")
        vector_configs = values.get("vector_configs")
        semantic_config = values.get("semantic_config")

        if (search_type == SearchType.vector.value or search_type == SearchType.hybrid_keywords.value) and len(vector_configs) == 0:
            raise ValueError(f"'vector_config' must be provided when using 'search_type={search_type}'")

        if (search_type == SearchType.semantic.value or search_type == SearchType.hybrid_semantic.value) and len(semantic_config) == 0:
            raise ValueError(f"'semantic_config' must be provided when using 'search_type={search_type}'")
        
        return values
    
    @root_validator(pre=True, allow_reuse=True)
    def validate_select_fields(cls, values):
        select_fields: List[SearchFieldConfig] = values.get("select_fields")
        app_type = values.get("index_application")

        item_ids_fields = list()
        categories_fields = list()
        description_fields = list()
        for raw_field in select_fields:
            field = SearchFieldConfig(**raw_field)
            if field.is_item_id:
                item_ids_fields.append(field.name)
            if field.contains_image_description:
                description_fields.append(field.name)
            if field.is_product_category:
                categories_fields.append(field.name)

        # Item Id validation
        if len(item_ids_fields) == 0:
            raise ValueError("At least 1 field must be marked as 'is_item_id'")
        if len(item_ids_fields) > 1:
            raise ValueError(f"Only 1 field must be marked as 'is_item_id'. Check fields {item_ids_fields}")
        
        # Category validation
        if len(categories_fields) > 1:
            raise ValueError(f"Only 1 field must be marked as 'is_product_category'. Check fields {item_ids_fields}")
        
        # Image description search validation
        if app_type == IndexApplicationType.image_description_search.value and len(description_fields) == 0:
            raise ValueError("When an index is used for 'image_description_search' at least 1 field must be marked as 'contains_image_description'")

        return values


class CognitiveSearchSkillConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure AI Search Skill Configuration",
        json_schema_extra={"$id": "./cognitiveSearchSkill.schema.json"})
    
    config: List[IndexConfig]


def generate_json_config_schema_file(output_path: str):
    output = json.dumps(CognitiveSearchSkillConfig.model_json_schema(), indent=2)
    print(output)
    with open(output_path, "w") as outfile:
        outfile.write(output)

def get_valid_config(config_path: str):
    try:
        # validate vs schema file
        if not os.path.exists(config_path):
            logging.error("Config path must exist for validation")
            return False

        with open(config_path) as config_file:
            config_content = json.load(config_file)

        config = CognitiveSearchSkillConfig(**config_content)
        return True, config
    
    except ValueError as e:
        print(f"validation failed: {e}")
        return False, {}


if __name__ == "__main__":
    generate_json_config_schema_file(
        output_path="../templates/cognitiveSearchSkill.schema.json")
    generate_json_config_schema_file(
        output_path="../../../searchConfigs/cognitiveSearchSkill.schema.json")
