from googleapiclient.discovery import build

from app.services.core.search.base import BaseSearchService
from app.core.config import get_settings


class GoogleService(BaseSearchService):
    """Google search service implementation"""

    def __init__(self):
        """Initialize Google service"""
        settings = get_settings()
        self.service = build(
            "customsearch", "v1",
            developerKey=settings.GOOGLE_API_KEY
        )
        self.cx = settings.GOOGLE_CSE_ID

    async def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Search using Google Custom Search API"""
        results = []
        response = self.service.cse().list(
            q=query,
            cx=self.cx,
            num=num_results
        ).execute()

        for item in response.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })

        return results
