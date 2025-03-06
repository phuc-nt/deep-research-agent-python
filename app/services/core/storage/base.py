from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseStorageService(ABC):
    """Base class for storage services"""
    
    @abstractmethod
    async def save(self, data: Dict[str, Any], **kwargs: Dict[str, Any]) -> str:
        """Save data and return identifier"""
        pass
        
    @abstractmethod
    async def load(self, identifier: str, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Load data by identifier"""
        pass
        
    @abstractmethod
    async def delete(self, identifier: str, **kwargs: Dict[str, Any]) -> bool:
        """Delete data by identifier"""
        pass 