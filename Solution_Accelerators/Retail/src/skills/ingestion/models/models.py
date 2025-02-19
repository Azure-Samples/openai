from typing import List

from models.api_models import CatalogItem
from pydantic import BaseModel


class DocumentIndexerRequestPayload(BaseModel):
    task_id: str
    storage_container_name: str
    index_name: str
    document_path: str
    document_name: str
    reported_year: str
    subsidiary: str

class CatalogIndexerRequestPayload(BaseModel):
    task_id: str
    images_storage_container: str
    index_name: str
    enrichment: bool # Only one enrichment is currently supported, so bool seems appropriate.
    items: List[CatalogItem]
