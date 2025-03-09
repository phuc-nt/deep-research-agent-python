from typing import Any, Dict, Optional
import time
import tiktoken
from openai import AsyncOpenAI

from app.services.core.llm.base import BaseLLMService
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

class OpenAIService(BaseLLMService):
    """OpenAI LLM service implementation"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI service with config
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=self.config.get("OPENAI_API_KEY"))
        self.model_name = self.config.get("MODEL_NAME", "gpt-4")
        
    def get_completion(self, prompt: str, max_tokens: int = None, temperature: float = None, **kwargs) -> str:
        """
        Synchronous method to get completion (to be used by base class)
        
        Args:
            prompt: The prompt to generate from
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: The generated text
        """
        # This is a stub method to satisfy the abstract method requirements
        # In practice, it will never be called directly as we override the async generate method
        raise NotImplementedError("OpenAIService does not support synchronous completions")
        
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a string using tiktoken
        
        Args:
            text: The text to count tokens in
            
        Returns:
            int: The number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}, using fallback method")
            # Fallback to approximate count: ~4 chars per token
            return len(text) // 4
    
    async def generate(self, prompt: str, task_id: Optional[str] = None, purpose: Optional[str] = None, 
                      max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs) -> str:
        """
        Generate text using OpenAI API
        
        Args:
            prompt: The prompt to generate from
            task_id: ID for cost tracking
            purpose: Purpose for cost tracking
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: The generated text
        """
        # Use parent's generate method which handles logging
        return await super().generate(prompt, task_id, purpose, max_tokens, temperature, **kwargs)
        
    async def stream(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """
        Stream text using OpenAI API
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            str: The generated text
        """
        raise NotImplementedError("Streaming not implemented")
        
    # This is the real implementation used by the parent generate method
    async def _get_completion_async(self, prompt: str, max_tokens: int = None, temperature: float = None, **kwargs) -> str:
        """
        Get a completion from OpenAI API
        
        Args:
            prompt: The prompt to generate from
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: The generated text
        """
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.config.get("MAX_TOKENS", 2000),
                temperature=temperature or self.config.get("TEMPERATURE", 0.7),
                **kwargs
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"OpenAI response time: {duration_ms}ms")
            
            # Trích xuất thông tin token từ response
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            logger.info(f"OpenAI tokens: {input_tokens} input, {output_tokens} output")
            
            # Lưu trữ thông tin token để BaseLLMService có thể truy cập
            self._last_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise
