from typing import Any, Dict, Optional
import time
import asyncio
import anthropic

from app.services.core.llm.base import BaseLLMService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClaudeService(BaseLLMService):
    """Anthropic Claude service implementation"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Claude service with config
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.config.get("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY))
        self.model_name = self.config.get("ANTHROPIC_MODEL_NAME", "claude-3-5-sonnet-latest")
        self.max_tokens = self.config.get("MAX_TOKENS", settings.MAX_TOKENS)
        self.temperature = self.config.get("TEMPERATURE", settings.TEMPERATURE)
        self.name = "Claude"

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
        try:
            start_time = time.time()
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Claude response time: {duration_ms}ms")
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            
            logger.info(f"Claude tokens: {input_tokens} input, {output_tokens} output")
            
            self._last_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            
            if hasattr(response, 'content') and len(response.content) > 0:
                return response.content[0].text
            else:
                logger.warning("Claude response has no content")
                return ""
                
        except Exception as e:
            logger.error(f"Error generating text with Claude: {str(e)}")
            raise
        
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a string using Anthropic's tokenizer
        
        Args:
            text: The text to count tokens in
            
        Returns:
            int: The number of tokens
        """
        try:
            if hasattr(self.client, 'count_tokens'):
                response = self.client.count_tokens(text)
                return response.tokens
            else:
                logger.warning("No token counting method available in anthropic package, using fallback")
                return len(text) // 4
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}, using fallback method")
            return len(text) // 4
    
    async def generate(self, prompt: str, task_id: Optional[str] = None, purpose: Optional[str] = None, 
                      max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs) -> str:
        """
        Generate text using Claude API
        
        Args:
            prompt: The prompt to generate from
            task_id: ID for cost tracking
            purpose: Purpose for cost tracking
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: The generated text
        """
        return await super().generate(prompt, task_id, purpose, max_tokens, temperature, **kwargs)
        
    async def stream(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """
        Stream text using Claude API
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            str: The generated text
        """
        raise NotImplementedError("Streaming not implemented")
        
    async def _get_completion_async(self, prompt: str, max_tokens: int = None, temperature: float = None, **kwargs) -> str:
        """
        Get a completion from Claude API (async wrapper around sync API)
        
        Args:
            prompt: The prompt to generate from
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: The generated text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.get_completion(prompt, max_tokens, temperature, **kwargs)
        )
