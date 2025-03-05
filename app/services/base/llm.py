from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseLLMService(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """Generate text from prompt using LLM"""
        pass 