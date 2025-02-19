from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class DocumentPayload(BaseModel):
    filename: str = Field(description="The name of the document.")
    reported_year: str = Field(description="The reported year as part of the document report.")
    subsidiary: str = Field(description="The subsidiary being report as part of the document.")

class CatalogItem(BaseModel):
    article_id: str = Field(description="The unique article id associated with the item.")
    product_name: str = Field(description="The name of the product.")
    product_type: str = Field(description="The type of the product represented in the item.")
    index_group_name: str = Field(description="The category name for the item.")
    gender: str = Field(description="The gender associated with the item.")
    detail_description: str = Field(description="The description of the item.")

class CatalogPayload(BaseModel):
    items: List[CatalogItem] = Field(description="The catalog items to be ingested.")

class EnrichmentType(str, Enum):
    NONE = "NONE"
    TABLE_AS_LIST = "TABLE_AS_LIST"
    IMAGE_DESCRIPTION = "IMAGE_DESCRIPTION"

class IngestionRequest(BaseModel):
    storage_container_name: str = Field(description="The storage container name where the documents/images are stored.")
    index_name: str = Field(description="The index name where the documents/images are to be ingested.")
    payload: Union[DocumentPayload, CatalogPayload] = Field("The request payload.")
    enrichment: EnrichmentType = Field("Optional enrichment applied at the item level to a certain field type.")