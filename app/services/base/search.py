from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    content: str
    url: str
    source: str

class BaseSearchService(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search for information using the search service"""
        pass 