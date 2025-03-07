from typing import Any, Dict, Optional


class BaseError(Exception):
    """Base exception class for the application"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigError(BaseError):
    """Raised when there is a configuration error"""
    pass


class ServiceError(BaseError):
    """Base exception for service errors"""
    pass


class LLMError(ServiceError):
    """Raised when there is an error with LLM service"""
    pass


class SearchError(ServiceError):
    """Raised when there is an error with search service"""
    pass


class StorageError(ServiceError):
    """Raised when there is an error with storage service"""
    pass


class PrepareError(ServiceError):
    """Raised when there is an error in prepare phase"""
    pass


class ResearchError(ServiceError):
    """Raised when there is an error in research phase"""
    pass


class EditError(ServiceError):
    """Raised when there is an error in edit phase"""
    pass


class ValidationError(BaseError):
    """Raised when there's a validation error in the research process"""
    pass
