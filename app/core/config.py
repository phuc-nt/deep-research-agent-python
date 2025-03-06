from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from dataclasses import dataclass


class Settings(BaseSettings):
    """Application settings"""
    
    # API version
    API_VERSION: str = "v1"
    
    # Environment
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    
    # API Keys
    OPENAI_API_KEY: str = "your_openai_api_key"
    ANTHROPIC_API_KEY: str = "your_anthropic_api_key"
    PERPLEXITY_API_KEY: str = "your_perplexity_api_key"
    GOOGLE_API_KEY: str = "your_google_api_key"
    GOOGLE_CSE_ID: str = "your_google_cse_id"
    GITHUB_ACCESS_TOKEN: str = "your_github_token"
    GITHUB_USERNAME: str = "your_github_username"
    GITHUB_REPO: str = "your_github_repo"
    
    # LLM settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    MODEL_NAME: str = "gpt-4"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@dataclass
class PreparePrompts:
    """Prompts for prepare phase"""
    ANALYZE_QUERY: str = """
    Analyze the following research query:
    {query}
    """

    CREATE_OUTLINE: str = """
    Create an outline for the following research query:
    {query}
    """


@dataclass
class ResearchPrompts:
    """Prompts for research phase"""
    RESEARCH_SECTION: str = """
    Research the following section:
    Query: {query}
    Section: {section}
    """


@dataclass
class EditPrompts:
    """Prompts for edit phase"""
    EDIT_CONTENT: str = """
    Edit the following content:
    {content}
    """


# Global instances
_settings = Settings()
_prepare_prompts = PreparePrompts()
_research_prompts = ResearchPrompts()
_edit_prompts = EditPrompts()


def get_settings() -> Settings:
    """Get application settings"""
    return _settings


def get_prepare_prompts() -> PreparePrompts:
    """Get prepare phase prompts"""
    return _prepare_prompts


def get_research_prompts() -> ResearchPrompts:
    """Get research phase prompts"""
    return _research_prompts


def get_edit_prompts() -> EditPrompts:
    """Get edit phase prompts"""
    return _edit_prompts
