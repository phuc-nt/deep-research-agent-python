from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # API version
    API_VERSION: str = "v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Keys
    OPENAI_API_KEY: str = "your_openai_api_key"
    ANTHROPIC_API_KEY: str = "your_anthropic_api_key"
    PERPLEXITY_API_KEY: str = "your_perplexity_api_key"
    GOOGLE_API_KEY: str = "your_google_api_key"
    GOOGLE_CX: str = "your_google_cx"
    GITHUB_ACCESS_TOKEN: str = "your_github_token"
    GITHUB_USERNAME: str = "your_github_username"
    GITHUB_REPO: str = "your_github_repo"
    
    # LLM settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    MODEL_NAME: str = "gpt-4"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


class PreparePrompts:
    """Prompts for prepare phase"""
    
    ANALYZE_QUERY = """
    Analyze the following query and extract key information:
    {query}
    """
    
    GENERATE_PLAN = """
    Generate a research plan for:
    {query}
    """


class ResearchPrompts:
    """Prompts for research phase"""
    
    SEARCH_QUERY = """
    Generate a search query for:
    {query}
    """
    
    ANALYZE_RESULTS = """
    Analyze these search results:
    {results}
    """


class EditPrompts:
    """Prompts for edit phase"""
    
    GENERATE_EDIT = """
    Generate edits for:
    {content}
    """
    
    REVIEW_EDIT = """
    Review these edits:
    {edits}
    """


# Global instances
_settings = Settings()
_prepare_prompts = PreparePrompts()
_research_prompts = ResearchPrompts()
_edit_prompts = EditPrompts()


def get_settings() -> Settings:
    """Get settings instance"""
    return _settings


def get_prepare_prompts() -> PreparePrompts:
    """Get prepare prompts instance"""
    return _prepare_prompts


def get_research_prompts() -> ResearchPrompts:
    """Get research prompts instance"""
    return _research_prompts


def get_edit_prompts() -> EditPrompts:
    """Get edit prompts instance"""
    return _edit_prompts
