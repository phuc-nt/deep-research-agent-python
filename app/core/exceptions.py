from typing import Any, Dict, Optional


class ResearchException(Exception):
    """Base exception for all research related errors"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details
        super().__init__(self.message)


class LLMServiceError(ResearchException):
    """Raised when there's an error with LLM services (OpenAI, Claude)"""
    pass


class SearchError(ResearchException):
    """Raised when there's an error with search services"""
    pass


class StorageError(ResearchException):
    """Raised when there's an error with storage services"""
    pass


class ValidationError(ResearchException):
    """Raised when there's a validation error in the research process"""
    pass


class PrepareError(ResearchException):
    """Raised when there's an error in the prepare phase"""
    pass


class ResearchError(ResearchException):
    """Raised when there's an error in the research phase"""
    pass


class EditError(ResearchException):
    """Raised when there's an error in the edit phase"""
    pass


class ConfigError(ResearchException):
    """Raised when there's a configuration error"""
    pass
