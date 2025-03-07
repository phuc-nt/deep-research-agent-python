import pytest
from app.core.config import (
    get_settings,
    get_prepare_prompts,
    get_research_prompts,
    get_edit_prompts
)

def test_settings_default_values():
    """Test if settings have correct default values"""
    settings = get_settings()
    
    assert settings.API_VERSION == "v1"
    assert settings.ENVIRONMENT == "test"
    assert settings.DEBUG == True
    assert settings.DEFAULT_LLM_PROVIDER == "openai"
    assert settings.MODEL_NAME == "gpt-4"
    assert settings.MAX_TOKENS == 4000
    assert settings.TEMPERATURE == 0.7

def test_prompts_format():
    """Test if prompts can be formatted without errors"""
    prepare_prompts = get_prepare_prompts()
    research_prompts = get_research_prompts()
    edit_prompts = get_edit_prompts()
    
    # Test PreparePrompts
    analysis_prompt = prepare_prompts.ANALYZE_QUERY.format(
        query="Test Query"
    )
    assert "Test Query" in analysis_prompt
    
    # Test ResearchPrompts
    search_prompt = research_prompts.SEARCH_QUERY.format(
        topic="Test Topic",
        scope="Test Scope",
        section_title="Test Title",
        section_description="Test Description"
    )
    assert "Test Topic" in search_prompt
    assert "Test Scope" in search_prompt
    assert "Test Title" in search_prompt
    assert "Test Description" in search_prompt
    
    # Test EditPrompts
    edit_prompt = edit_prompts.EDIT_CONTENT.format(
        content="Test Content",
        topic="Test Topic",
        scope="Test Scope",
        target_audience="Test Audience"
    )
    assert "Test Content" in edit_prompt
    assert "Test Topic" in edit_prompt
    assert "Test Scope" in edit_prompt
    assert "Test Audience" in edit_prompt 