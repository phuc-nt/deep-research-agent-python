from typing import Any, Dict, Optional
from anthropic import AsyncAnthropic

from app.services.llm.base import BaseLLMService
from app.core.config import get_settings

settings = get_settings()

class ClaudeService(BaseLLMService):
    """Claude service implementation"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.MODEL_NAME
        
    async def generate(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Generate text from prompt using Claude"""
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
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
