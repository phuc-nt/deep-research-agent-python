from typing import Type

from app.services.core.llm.base import BaseLLMService
from app.services.core.search.base import BaseSearchService
from app.services.core.storage.base import BaseStorageService

# These will be implemented later
from app.services.core.llm.openai import OpenAIService
from app.services.core.llm.claude import ClaudeService
from app.services.core.search.perplexity import PerplexityService
from app.services.core.search.google import GoogleService
from app.services.core.storage.github import GitHubService

from .config import get_settings
from .exceptions import ConfigError


class ServiceFactory:
    """Factory for creating service instances"""

    @staticmethod
    def create_llm_service(provider: str = None) -> BaseLLMService:
        """
        Create an LLM service instance based on provider
        If provider is None, uses default from settings
        """
        settings = get_settings()
        provider = provider or settings.DEFAULT_LLM_PROVIDER

        if provider == "openai":
            return OpenAIService()
        elif provider == "claude":
            return ClaudeService()
        else:
            raise ConfigError(f"Unknown LLM provider: {provider}")

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
        else:
            raise ConfigError(f"Unknown storage provider: {provider}")


# Singleton instance for easy access
service_factory = ServiceFactory()
