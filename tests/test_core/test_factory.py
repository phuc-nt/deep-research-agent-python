import pytest
from unittest.mock import patch, MagicMock

from app.core.exceptions import ConfigError
from app.services.core.llm.base import BaseLLMService
from app.services.core.search.base import BaseSearchService
from app.services.core.storage.base import BaseStorageService
from app.core.factory import ServiceFactory, service_factory

def test_create_llm_service():
    """Test creating LLM services"""
    # Test OpenAI service
    openai_service = ServiceFactory.create_llm_service("openai")
    assert isinstance(openai_service, BaseLLMService)

    # Test Claude service
    claude_service = ServiceFactory.create_llm_service("claude")
    assert isinstance(claude_service, BaseLLMService)

    # Test invalid provider
    with pytest.raises(ConfigError):
        ServiceFactory.create_llm_service("invalid")

def test_create_search_service():
    """Test creating search services"""
    # Test Perplexity service
    perplexity_service = ServiceFactory.create_search_service("perplexity")
    assert isinstance(perplexity_service, BaseSearchService)

    # Test Google service
    google_service = ServiceFactory.create_search_service("google")
    assert isinstance(google_service, BaseSearchService)

    # Test invalid provider
    with pytest.raises(ConfigError):
        ServiceFactory.create_search_service("invalid")

@patch('app.services.core.storage.github.Github')
def test_create_storage_service(mock_github):
    """Test creating storage services"""
    # Mock GitHub client and repository
    mock_repo = MagicMock()
    mock_github.return_value.get_repo.return_value = mock_repo

    # Test GitHub service
    github_service = ServiceFactory.create_storage_service("github")
    assert isinstance(github_service, BaseStorageService)

    # Test invalid provider
    with pytest.raises(ConfigError):
        ServiceFactory.create_storage_service("invalid")

def test_singleton_factory():
    """Test singleton factory instance"""
    # Test that multiple instances are different
    factory1 = ServiceFactory()
    factory2 = ServiceFactory()
    assert factory1 is not factory2

    # Test that singleton instance is the same
    assert service_factory is service_factory 