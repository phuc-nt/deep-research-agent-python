from abc import ABC, abstractmethod
import time
from typing import Dict, List, Any, Optional
import uuid

from app.core.logging import get_logger
from app.services.core.monitoring.cost import get_cost_service

logger = get_logger(__name__)

class BaseLLMService(ABC):
    """
    Base class for LLM services
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def get_completion(self, prompt: str, max_tokens: int = None, temperature: float = None, **kwargs) -> str:
        """
        Get a completion from the LLM
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a string
        """
        pass
    
    def _log_request_cost(
        self, 
        task_id: Optional[str], 
        model: str, 
        input_tokens: int, 
        output_tokens: int, 
        prompt: str, 
        duration_ms: int, 
        purpose: Optional[str] = None
    ):
        """Log request cost if task_id is provided"""
        if task_id:
            try:
                cost_service = get_cost_service()
                cost_service.log_llm_request(
                    task_id=task_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    prompt=prompt,
                    duration_ms=duration_ms,
                    endpoint=self.name,
                    purpose=purpose
                )
            except Exception as e:
                logger.error(f"Error logging LLM request cost: {str(e)}")
    
    async def generate(
        self, 
        prompt: str, 
        task_id: Optional[str] = None,
        purpose: Optional[str] = None,
        max_tokens: Optional[int] = None, 
        temperature: Optional[float] = None, 
        **kwargs
    ) -> str:
        """
        Generate text from a prompt
        
        Args:
            prompt: The prompt to generate from
            task_id: ID of the research task (for cost tracking)
            purpose: Purpose of the request (for cost tracking)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            **kwargs: Additional model-specific parameters
            
        Returns:
            str: The generated text
        """
        start_time = time.time()
        input_token_count = self.count_tokens(prompt)
        
        logger.info(f"Gửi prompt tới {self.name} ({input_token_count} tokens)")
        
        # Reset last usage if exists
        if hasattr(self, '_last_usage'):
            self._last_usage = None
        
        # Use _get_completion_async if available, otherwise fall back to get_completion
        if hasattr(self, '_get_completion_async') and callable(getattr(self, '_get_completion_async')):
            result = await self._get_completion_async(
                prompt, 
                max_tokens=max_tokens or self.config.get("MAX_TOKENS"),
                temperature=temperature or self.config.get("TEMPERATURE"),
                **kwargs
            )
        else:
            result = self.get_completion(
                prompt, 
                max_tokens=max_tokens or self.config.get("MAX_TOKENS"),
                temperature=temperature or self.config.get("TEMPERATURE"),
                **kwargs
            )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Ưu tiên sử dụng thông tin token từ _last_usage nếu có (từ Anthropic, OpenAI API)
        if hasattr(self, '_last_usage') and self._last_usage:
            input_token_count = self._last_usage.get('input_tokens', input_token_count)
            output_token_count = self._last_usage.get('output_tokens')
        else:
            # Nếu không có _last_usage, tính toán bằng cách đếm token
            output_token_count = self.count_tokens(result)
        
        logger.info(f"Nhận phản hồi từ {self.name} ({output_token_count} tokens) trong {duration_ms}ms")
        
        # Log the cost if task_id is provided
        if task_id:
            # Xác định model name từ các thuộc tính có thể có
            model_name = "unknown"
            if hasattr(self, "model_name"):
                model_name = self.model_name
            elif hasattr(self, "model"):
                model_name = self.model
            elif "MODEL_NAME" in self.config:
                model_name = self.config["MODEL_NAME"]
                
            self._log_request_cost(
                task_id=task_id,
                model=model_name,
                input_tokens=input_token_count,
                output_tokens=output_token_count,
                prompt=prompt,
                duration_ms=duration_ms,
                purpose=purpose
            )
        
        return result
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Stream text from prompt"""
        pass 