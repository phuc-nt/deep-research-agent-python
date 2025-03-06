from typing import Any, Dict, List
from googleapiclient.discovery import build

from app.services.search.base import BaseSearchService
from app.core.config import get_settings

settings = get_settings()

class GoogleService(BaseSearchService):
    """Google search service implementation"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.cx = settings.GOOGLE_CX
        self.service = build("customsearch", "v1", developerKey=self.api_key)
        
    async def search(self, query: str, **kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        response = self.service.cse().list(q=query, cx=self.cx, **kwargs).execute()
        return response.get("items", [])
