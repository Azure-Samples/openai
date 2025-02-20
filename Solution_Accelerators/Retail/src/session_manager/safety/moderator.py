from typing import Any
from abc import ABC, abstractmethod

class Moderator(ABC):
    """
    Abstract class for a moderator
    """
    @abstractmethod
    async def is_safe_async(self, content: Any):
        """
        Analyze the content object
        """
        pass