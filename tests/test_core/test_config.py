import pytest
from app.core.config import Settings, get_settings, get_prepare_prompts, get_research_prompts, get_edit_prompts

def test_settings_default_values():
    """Test default values in Settings"""
    settings = Settings()
    assert settings.API_VERSION == "v1"
    assert settings.ENVIRONMENT == "test"
    assert settings.DEBUG is True
    assert settings.MAX_TOKENS == 4000
    assert settings.TEMPERATURE == 0.7
    assert settings.MODEL_NAME == "gpt-4"

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
    research_prompt = research_prompts.RESEARCH_SECTION.format(
        query="Test Query",
        section="Test Section"
    )
    assert "Test Query" in research_prompt
    assert "Test Section" in research_prompt

    # Test EditPrompts
    edit_prompt = edit_prompts.EDIT_CONTENT.format(
        content="Test Content"
    )
    assert "Test Content" in edit_prompt 