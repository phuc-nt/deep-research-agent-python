import httpx
import json
from typing import List, Dict, Any
import time

from app.services.core.search.base import BaseSearchService
from app.core.config import get_settings
from app.core.logging import logger


class PerplexityService(BaseSearchService):
    """Perplexity search service implementation"""

    def __init__(self):
        """Initialize Perplexity service"""
        settings = get_settings()
        self.api_key = settings.PERPLEXITY_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0  # Tăng timeout lên 120 giây
        )

    async def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Search using Perplexity API"""
        logger.info(f"=== BẮT ĐẦU TÌM KIẾM VỚI PERPLEXITY API ===")
        logger.info(f"Query: {query}")
        logger.info(f"Số kết quả yêu cầu: {num_results}")
        
        try:
            start_time = time.time()
            
            # Gọi API chat completions
            logger.info(f"Gửi request đến Perplexity API...")
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful search assistant. Provide detailed and accurate information about the query."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "stream": False
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            end_time = time.time()
            logger.info(f"Nhận được phản hồi từ Perplexity API trong {end_time - start_time:.2f} giây")
            
            # Lấy nội dung phản hồi
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            logger.info(f"Số lượng citations: {len(citations)}")
            
            # Tạo kết quả từ citations
            results = []
            for i, citation in enumerate(citations[:num_results]):
                # Kiểm tra nếu citation là chuỗi (URL)
                if isinstance(citation, str):
                    url = citation
                    # Tạo tiêu đề từ URL
                    title = url.split("/")[-1].replace("-", " ").replace(".html", "").title()
                    # Trích xuất đoạn văn bản từ nội dung
                    snippet = f"Nguồn tham khảo từ: {url}"
                else:
                    # Trường hợp citation là dictionary
                    title = citation.get("metadata", {}).get("title", "")
                    url = citation.get("metadata", {}).get("url", "")
                    snippet = citation.get("text", "")
                
                logger.info(f"Kết quả {i+1}: Tiêu đề: '{title[:50]}...', URL: {url}")
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet
                })
            
            logger.info(f"Tìm thấy {len(results)} kết quả từ Perplexity API")
            logger.info(f"=== KẾT THÚC TÌM KIẾM VỚI PERPLEXITY API - THÀNH CÔNG ===")
            return results
            
        except Exception as e:
            logger.error(f"=== KẾT THÚC TÌM KIẾM VỚI PERPLEXITY API - THẤT BẠI ===")
            logger.error(f"Lỗi khi tìm kiếm với Perplexity API: {str(e)}")
            
            # Nếu có lỗi, trả về danh sách trống hoặc kết quả mẫu
            logger.info("Trả về danh sách kết quả trống")
            return []
