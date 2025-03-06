from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseLLMService(ABC):
    """Base class for LLM services"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Stream text from prompt"""
        pass 