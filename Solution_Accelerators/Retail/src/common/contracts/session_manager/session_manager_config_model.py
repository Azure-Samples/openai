from typing import Optional
from pydantic import BaseModel

class SessionManagerConfig(BaseModel):
    """
    Configuration / overrides for the Session Manager service.
    """
    
    azure_storage_account: Optional[str] = None
    azure_storage_container: Optional[str] = None
    azure_storage_image_container: Optional[str] = None
    orchestrator_service_uri: Optional[str] = None
    session_manager_uri: Optional[str] = None