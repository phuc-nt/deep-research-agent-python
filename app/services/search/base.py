from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseSearchService(ABC):
    """Base class for search services"""
    
    @abstractmethod
    async def search(self, query: str, **kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for query and return results"""
        pass 