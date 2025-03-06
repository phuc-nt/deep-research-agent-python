from typing import Any, Dict, List
import httpx

from app.services.search.base import BaseSearchService
from app.core.config import get_settings

settings = get_settings()

class PerplexityService(BaseSearchService):
    """Perplexity search service implementation"""
    
    def __init__(self):
        super().__init__()
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/search"
        
    async def search(self, query: str, **kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search using Perplexity API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"query": query, **kwargs}
            )
            response.raise_for_status()
            data = response.json()
            return data["results"]
