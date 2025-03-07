import pytest
from app.core.exceptions import (
    BaseError,
    ConfigError,
    ServiceError,
    LLMError,
    SearchError,
    StorageError,
    PrepareError,
    ResearchError,
    EditError,
    ValidationError
)

def test_base_exception():
    """Test base exception class"""
    error = BaseError("Test error")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.details == {}
    
    error_with_details = BaseError(
        "Test error",
        details={"key": "value"}
    )
    assert error_with_details.details == {"key": "value"}

def test_exceptions_inheritance():
    """Test inheritance của các exceptions"""
    # Service errors
    assert issubclass(ServiceError, BaseError)
    assert issubclass(LLMError, ServiceError)
    assert issubclass(SearchError, ServiceError)
    assert issubclass(StorageError, ServiceError)
    assert issubclass(PrepareError, ServiceError)
    assert issubclass(ResearchError, ServiceError)
    assert issubclass(EditError, ServiceError)
    
    # Other errors
    assert issubclass(ConfigError, BaseError)
    assert issubclass(ValidationError, BaseError)

def test_exception_with_details():
    """Test exception với details"""
    details = {
        "error_code": 500,
        "service": "test_service",
        "additional_info": "test info"
    }
    
    error = ServiceError(
        message="Test service error",
        details=details
    )
    
    assert error.message == "Test service error"
    assert error.details == details 