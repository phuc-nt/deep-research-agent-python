import pytest
from app.core.exceptions import (
    ResearchException,
    LLMServiceError,
    SearchError,
    StorageError,
    ValidationError,
    PrepareError,
    ResearchError,
    EditError,
    ConfigError
)

def test_base_exception():
    """Test ResearchException base class"""
    error_msg = "Test error"
    error_details = {"key": "value"}
    
    exc = ResearchException(error_msg, error_details)
    assert str(exc) == error_msg
    assert exc.message == error_msg
    assert exc.details == error_details

def test_exceptions_inheritance():
    """Test if all exceptions inherit from ResearchException"""
    exceptions = [
        LLMServiceError,
        SearchError,
        StorageError,
        ValidationError,
        PrepareError,
        ResearchError,
        EditError,
        ConfigError
    ]
    
    for exc_class in exceptions:
        exc = exc_class("Test")
        assert isinstance(exc, ResearchException)

def test_exception_with_details():
    """Test exceptions with different types of details"""
    details = {
        "error_code": 500,
        "service": "openai",
        "params": {"model": "gpt-4"}
    }
    
    exc = LLMServiceError("API Error", details)
    assert exc.details == details
    assert "API Error" in str(exc) 