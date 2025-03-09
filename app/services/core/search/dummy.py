import json
import random
from typing import List, Dict, Any, Optional

from app.services.core.search.base import BaseSearchService
from app.core.logging import get_logger

logger = get_logger(__name__)


class DummySearchService(BaseSearchService):
    """
    Dummy search service implementation that returns mock results
    Sử dụng khi không có API key hợp lệ cho các search provider thực
    """

    def __init__(self):
        """Initialize Dummy search service"""
        self.provider_name = "dummy"
        logger.info("Khởi tạo DummySearchService")

    async def search(self, query: str, num_results: int = 5, task_id: Optional[str] = None, purpose: Optional[str] = None, **kwargs) -> list[dict]:
        """
        Return mock search results
        
        Args:
            query: Search query
            num_results: Number of results to return
            task_id: Task ID for cost tracking
            purpose: Purpose of the search request
            **kwargs: Additional arguments
            
        Returns:
            list: List of mock search results
        """
        logger.info(f"=== BẮT ĐẦU TÌM KIẾM VỚI DUMMY SEARCH SERVICE ===")
        logger.info(f"Query: {query}")
        logger.info(f"Số kết quả yêu cầu: {num_results}")
        
        # Tạo kết quả giả
        results = []
        for i in range(min(num_results, 5)):
            # Tạo tiêu đề dựa trên query
            words = query.split()
            title_words = random.sample(words, min(len(words), 3))
            title = f"Kết quả về {' '.join(title_words)}"
            
            # Tạo snippet với một số từ khóa từ query
            snippet = f"Đây là thông tin về {query}. Bài viết này cung cấp dữ liệu và phân tích về chủ đề này."
            
            # Tạo URL giả
            url = f"https://example.com/result-{i+1}"
            
            results.append({
                "title": title,
                "snippet": snippet,
                "url": url
            })
        
        logger.info(f"Đã tạo {len(results)} kết quả giả")
        
        # Ghi nhận chi phí nếu có cost_monitoring_service
        if hasattr(self, 'cost_monitoring_service') and self.cost_monitoring_service and task_id:
            self.cost_monitoring_service.record_search_request(
                task_id=task_id,
                provider=self.provider_name,
                query=query,
                num_results=len(results),
                purpose=purpose,
                cost=0.0  # Không tính phí cho dummy search
            )
        
        return results 

    async def check_connection(self) -> bool:
        """
        Kiểm tra kết nối đến Dummy search service
        
        Returns:
            bool: Luôn trả về True vì đây là dummy service
        """
        logger.info("Kiểm tra kết nối đến Dummy search service")
        logger.info("Dummy search service luôn sẵn sàng")
        return True 