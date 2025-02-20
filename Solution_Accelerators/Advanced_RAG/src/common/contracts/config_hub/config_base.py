from typing import Optional
from pydantic import BaseModel

class ConfigBase(BaseModel):
    config_id: str
    config_version: Optional[str] = None