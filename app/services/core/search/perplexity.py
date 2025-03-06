import httpx

from app.services.core.search.base import BaseSearchService
from app.core.config import get_settings


class PerplexityService(BaseSearchService):
    """Perplexity search service implementation"""

    def __init__(self):
        """Initialize Perplexity service"""
        settings = get_settings()
        self.api_key = settings.PERPLEXITY_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Search using Perplexity API"""
        response = await self.client.post(
            "/search",
            json={
                "query": query,
                "num_results": num_results
            }
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("text", "")
            })

        return results
