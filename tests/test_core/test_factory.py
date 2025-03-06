import pytest
from unittest.mock import patch, MagicMock

from app.core.factory import ServiceFactory, ConfigError
from app.services.llm.base import BaseLLMService
from app.services.search.base import BaseSearchService
from app.services.storage.base import BaseStorageService

def test_create_llm_service():
    """Test LLM service creation"""
    factory = ServiceFactory()
    
    # Test OpenAI service
    with patch("app.services.llm.openai.AsyncOpenAI"):
        openai_service = factory.create_llm_service("openai")
        assert isinstance(openai_service, BaseLLMService)
    
    # Test Claude service
    with patch("app.services.llm.claude.AsyncAnthropic"):
        claude_service = factory.create_llm_service("claude")
        assert isinstance(claude_service, BaseLLMService)
    
    # Test invalid provider
    with pytest.raises(ConfigError):
        factory.create_llm_service("invalid")

def test_create_search_service():
    """Test search service creation"""
    factory = ServiceFactory()
    
    # Test Perplexity service
    with patch("app.services.search.perplexity.httpx.AsyncClient"):
        perplexity_service = factory.create_search_service("perplexity")
        assert isinstance(perplexity_service, BaseSearchService)
    
    # Test Google service
    with patch("app.services.search.google.build"):
        google_service = factory.create_search_service("google")
        assert isinstance(google_service, BaseSearchService)
    
    # Test invalid provider
    with pytest.raises(ConfigError):
        factory.create_search_service("invalid")

def test_create_storage_service():
    """Test storage service creation"""
    factory = ServiceFactory()
    
    # Test GitHub service
    with patch("app.services.storage.github.Github"):
        github_service = factory.create_storage_service("github")
        assert isinstance(github_service, BaseStorageService)
    
    # Test invalid provider
    with pytest.raises(ConfigError):
        factory.create_storage_service("invalid")

def test_singleton_factory():
    """Test singleton factory instance"""
    from app.core.factory import service_factory
    
    factory1 = ServiceFactory()
    factory2 = ServiceFactory()
    
    # Different instances should be different
    assert factory1 is not factory2
    
    # But singleton instance should be the same
    assert service_factory is service_factory 