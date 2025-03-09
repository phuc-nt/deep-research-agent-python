import httpx
import json
from typing import List, Dict, Any, Optional
import time

from app.services.core.search.base import BaseSearchService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PerplexityService(BaseSearchService):
    """Perplexity search service implementation"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Perplexity service
        
        Args:
            config: Configuration dictionary, optional
        """
        settings = get_settings()
        self.api_key = config.get("PERPLEXITY_API_KEY") if config else settings.PERPLEXITY_API_KEY
        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0  # Tăng timeout lên 120 giây
        )
        self.provider_name = "perplexity"

    async def search(self, query: str, num_results: int = 5, task_id: Optional[str] = None, purpose: Optional[str] = None, **kwargs) -> list[dict]:
        """
        Search using Perplexity API
        
        Args:
            query: Search query
            num_results: Number of results to return
            task_id: Task ID for cost tracking
            purpose: Purpose of the search request
            **kwargs: Additional arguments
            
        Returns:
            list: List of search results
        """
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
            duration_ms = int((end_time - start_time) * 1000)
            logger.info(f"Nhận được phản hồi từ Perplexity API trong {duration_ms} ms")
            
            # Lấy nội dung phản hồi
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            # Trích xuất thông tin token từ response
            token_info = data.get("usage", {})
            input_tokens = token_info.get("prompt_tokens", 0)
            output_tokens = token_info.get("completion_tokens", 0)
            
            logger.info(f"Perplexity tokens: {input_tokens} input, {output_tokens} output")
            logger.info(f"Số lượng citations: {len(citations)}")
            
            # Ghi nhận chi phí nếu có task_id
            if task_id:
                try:
                    # Import lazily để tránh vòng lặp import
                    from app.core.factory import get_service_factory
                    
                    # Lấy cost monitoring service
                    factory = get_service_factory()
                    cost_service = factory.get_cost_monitoring_service()
                    
                    # Cập nhật log_search_request để bao gồm thông tin token
                    cost_service.log_search_request(
                        task_id=task_id,
                        provider=self.provider_name,
                        query=query,
                        duration_ms=duration_ms,
                        num_results=len(citations[:num_results]),
                        purpose=purpose,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens
                    )
                    
                    logger.info(f"Đã ghi nhận chi phí search cho task {task_id}")
                except Exception as e:
                    logger.error(f"Lỗi khi ghi nhận chi phí search: {str(e)}")
            
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

    async def check_connection(self) -> bool:
        """
        Kiểm tra kết nối đến Perplexity API
        
        Returns:
            bool: True nếu kết nối thành công, False nếu không
        """
        try:
            # Kiểm tra API key
            if not self.api_key or self.api_key == "your_perplexity_api_key":
                logger.error("API key không hợp lệ hoặc chưa được cấu hình")
                return False
                
            logger.info(f"Kiểm tra kết nối đến Perplexity API với API key: {self.api_key[:5]}...")
            
            # Thử gọi API với một query đơn giản
            logger.info("Gửi request kiểm tra kết nối đến Perplexity API...")
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant."
                        },
                        {
                            "role": "user",
                            "content": "Hello, this is a connection test."
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 10,
                    "stream": False
                }
            )
            
            # In thông tin response để debug
            status_code = response.status_code
            logger.info(f"Nhận được phản hồi từ Perplexity API với status code: {status_code}")
            
            if status_code != 200:
                logger.error(f"Phản hồi không thành công: {response.text}")
                return False
                
            # Kiểm tra nội dung phản hồi
            data = response.json()
            if "choices" not in data or not data["choices"]:
                logger.error(f"Phản hồi không chứa dữ liệu choices: {data}")
                return False
                
            logger.info("Kết nối đến Perplexity API thành công")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra kết nối đến Perplexity API: {str(e)}")
            # In thêm thông tin chi tiết về lỗi
            import traceback
            logger.error(f"Chi tiết lỗi: {traceback.format_exc()}")
            return False
