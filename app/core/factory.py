from typing import Type, Optional, Dict, Any

from app.services.core.llm.base import BaseLLMService
from app.services.core.search.base import BaseSearchService
from app.services.core.storage.base import BaseStorageService

# These will be implemented later
from app.services.core.llm.openai import OpenAIService
from app.services.core.llm.claude import ClaudeService
from app.services.core.search.perplexity import PerplexityService
from app.services.core.search.google import GoogleService
from app.services.core.storage.github import GitHubService
from app.services.core.storage.file import FileStorageService

from .config import get_settings
from .exceptions import ConfigError


class ServiceFactory:
    """Factory for creating service instances"""

    @staticmethod
    def create_llm_service(
        provider: Optional[str] = None, 
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> BaseLLMService:
        """
        Create an LLM service instance based on provider and model parameters
        
        Args:
            provider: LLM provider (openai, claude). If None, uses default from settings
            model_name: Model name to use. If None, uses default from settings
            max_tokens: Maximum tokens. If None, uses default from settings
            temperature: Temperature. If None, uses default from settings
            
        Returns:
            BaseLLMService: LLM service instance
        """
        settings = get_settings()
        provider = provider or settings.DEFAULT_LLM_PROVIDER
        
        # Create service based on provider
        if provider == "openai":
            service = OpenAIService()
        elif provider == "claude":
            service = ClaudeService()
        else:
            raise ConfigError(f"Unknown LLM provider: {provider}")
        
        # Override default parameters if specified
        if model_name is not None:
            service.model = model_name
        if max_tokens is not None:
            service.max_tokens = max_tokens
        if temperature is not None:
            service.temperature = temperature
            
        return service
    
    @staticmethod
    def create_llm_service_for_phase(phase: str) -> BaseLLMService:
        """
        Create an LLM service instance for a specific phase
        
        Args:
            phase: Phase name (prepare, research, edit)
            
        Returns:
            BaseLLMService: LLM service instance configured for the phase
        """
        settings = get_settings()
        
        if phase == "prepare":
            return ServiceFactory.create_llm_service(
                provider=settings.PREPARE_LLM_PROVIDER,
                model_name=settings.PREPARE_MODEL_NAME,
                max_tokens=settings.PREPARE_MAX_TOKENS,
                temperature=settings.PREPARE_TEMPERATURE
            )
        elif phase == "research":
            return ServiceFactory.create_llm_service(
                provider=settings.RESEARCH_LLM_PROVIDER,
                model_name=settings.RESEARCH_MODEL_NAME,
                max_tokens=settings.RESEARCH_MAX_TOKENS,
                temperature=settings.RESEARCH_TEMPERATURE
            )
        elif phase == "edit":
            return ServiceFactory.create_llm_service(
                provider=settings.EDIT_LLM_PROVIDER,
                model_name=settings.EDIT_MODEL_NAME,
                max_tokens=settings.EDIT_MAX_TOKENS,
                temperature=settings.EDIT_TEMPERATURE
            )
        else:
            raise ConfigError(f"Unknown phase: {phase}")

    @staticmethod
    def create_search_service(provider: str = "perplexity") -> BaseSearchService:
        """Create a search service instance"""
        if provider == "perplexity":
            return PerplexityService()
        elif provider == "google":
            return GoogleService()
        else:
            raise ConfigError(f"Unknown search provider: {provider}")

    @staticmethod
    def create_storage_service(provider: str = "github") -> BaseStorageService:
        """Create a storage service instance"""
        if provider == "github":
            return GitHubService()
        elif provider == "file":
            return FileStorageService()
        else:
            raise ConfigError(f"Unknown storage provider: {provider}")


# Singleton instance for easy access
service_factory = ServiceFactory()
