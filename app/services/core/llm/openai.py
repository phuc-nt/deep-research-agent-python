from typing import Any, Dict, Optional
from openai import AsyncOpenAI

from app.services.core.llm.base import BaseLLMService
from app.core.config import get_settings

settings = get_settings()

class OpenAIService(BaseLLMService):
    """OpenAI LLM service implementation"""

    def __init__(self):
        """Initialize OpenAI service"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_NAME
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        
    async def generate(self, prompt: str) -> str:
        """Generate text using OpenAI"""
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    async def stream(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Stream text from prompt using OpenAI"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                
        return full_response
