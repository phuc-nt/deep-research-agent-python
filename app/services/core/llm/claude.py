from typing import Any, Dict, Optional
from anthropic import AsyncAnthropic

from app.services.core.llm.base import BaseLLMService
from app.core.config import get_settings


class ClaudeService(BaseLLMService):
    """Claude LLM service implementation"""

    def __init__(self):
        """Initialize Claude service"""
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.MODEL_NAME
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE

    async def generate(self, prompt: str) -> str:
        """Generate text using Claude"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
        
    async def stream(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Stream text from prompt using Claude"""
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        
        full_response = ""
        async for chunk in response:
            if chunk.delta.text:
                full_response += chunk.delta.text
                
        return full_response
