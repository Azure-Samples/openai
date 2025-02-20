from typing import Optional
from pydantic import BaseModel, validator, ValidationError


class CreateConfigRequest(BaseModel):
    config_id: str
    config_version: Optional[str] = None
    config_file_url: Optional[str] = None
    config_body: dict = {}

    @validator('config_body', always=True, pre=True)
    def check_at_least_one(cls, v, values, **kwargs):
        if 'config_file_url' in values and values['config_file_url'] and v:
            return v
        if not values.get('config_file_url') and not v:
            raise ValidationError('At least one of config_file_url or config_body must be set')
        return v


class CreateConfigResponse(BaseModel):
    config_id: str = ""
    config_version: str = ""
    error: str = ""

    def to_dict(self):
        return self.model_dump()