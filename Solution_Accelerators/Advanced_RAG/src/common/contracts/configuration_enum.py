from enum import Enum

class ConfigurationEnum(Enum):
    """
    Enum for different configuration types
    """
    
    SEARCH_RUNTIME = "search_runtime"
    ORCHESTRATOR_RUNTIME = "orchestrator_runtime"
    SESSION_MANAGER_RUNTIME = "session_manager_runtime"