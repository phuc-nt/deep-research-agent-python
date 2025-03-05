from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStorageService(ABC):
    @abstractmethod
    async def save(self, content: str, metadata: Dict[str, Any]) -> str:
        """Save content and return URL"""
        pass

    @abstractmethod
    async def get(self, id: str) -> str:
        """Get content by ID"""
        pass 