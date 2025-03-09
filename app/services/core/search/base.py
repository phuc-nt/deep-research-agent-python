from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseSearchService(ABC):
    """Base class for search services"""
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 5, task_id: Optional[str] = None, purpose: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for information
        
        Args:
            query: Search query
            num_results: Number of results to return
            task_id: Task ID for cost tracking
            purpose: Purpose of the search request
            **kwargs: Additional arguments
            
        Returns:
            list: List of search results
        """
        pass
    
    async def check_connection(self) -> bool:
        """
        Kiểm tra kết nối đến search service
        
        Returns:
            bool: True nếu kết nối thành công, False nếu không
        """
        try:
            # Thực hiện một tìm kiếm đơn giản để kiểm tra kết nối
            results = await self.search("test connection", num_results=1)
            return len(results) > 0
        except Exception as e:
            from app.core.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Lỗi khi kiểm tra kết nối đến search service: {str(e)}")
            return False 