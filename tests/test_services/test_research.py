import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ResearchError
from app.services.research.base import (
    ResearchRequest,
    ResearchOutline,
    ResearchSection
)
from app.services.research.research import ResearchService

@pytest.fixture
def research_service():
    """Fixture tạo instance của ResearchService với các mock dependencies"""
    with patch("app.services.research.research.service_factory") as mock_factory:
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_factory.create_llm_service.return_value = mock_llm
        
        # Mock search service
        mock_search = AsyncMock()
        mock_factory.create_search_service.return_value = mock_search
        
        service = ResearchService()
        service.llm_service = mock_llm
        service.search_service = mock_search
        
        yield service

@pytest.fixture
def mock_request():
    """Fixture tạo mock ResearchRequest"""
    return ResearchRequest(
        query="Test research request",
        topic="Test Topic",
        scope="Test Scope",
        target_audience="Test Audience"
    )

@pytest.fixture
def mock_outline():
    """Fixture tạo mock ResearchOutline"""
    return ResearchOutline(
        sections=[
            ResearchSection(
                title="Section 1",
                description="Description 1"
            ),
            ResearchSection(
                title="Section 2",
                description="Description 2"
            )
        ]
    )

@pytest.mark.asyncio
async def test_research_section_success(research_service):
    """Test nghiên cứu một phần thành công"""
    # Mock data
    section = ResearchSection(
        title="Test Section",
        description="Test Description"
    )
    context = {
        "topic": "Test Topic",
        "scope": "Test Scope",
        "target_audience": "Test Audience"
    }
    mock_search_results = [
        {"title": "Result 1", "content": "Content 1"},
        {"title": "Result 2", "content": "Content 2"}
    ]
    mock_content = "Synthesized content with citations"
    
    # Setup mocks
    research_service.search_service.search.return_value = mock_search_results
    research_service.llm_service.generate.return_value = mock_content
    
    # Thực thi
    result = await research_service.research_section(section, context)
    
    # Kiểm tra kết quả
    assert result.title == section.title
    assert result.description == section.description
    assert result.content == mock_content
    
    # Verify calls
    research_service.search_service.search.assert_called_once()
    research_service.llm_service.generate.assert_called_once()

@pytest.mark.asyncio
async def test_research_section_error(research_service):
    """Test nghiên cứu một phần thất bại"""
    # Mock data
    section = ResearchSection(
        title="Test Section",
        description="Test Description"
    )
    context = {
        "topic": "Test Topic",
        "scope": "Test Scope",
        "target_audience": "Test Audience"
    }
    
    # Setup mock error
    research_service.search_service.search.side_effect = Exception("Search error")
    
    # Kiểm tra exception
    with pytest.raises(ResearchError) as exc_info:
        await research_service.research_section(section, context)
    
    assert f"Lỗi khi nghiên cứu phần '{section.title}'" in str(exc_info.value)

@pytest.mark.asyncio
async def test_execute_success(research_service, mock_request, mock_outline):
    """Test thực thi toàn bộ phase nghiên cứu thành công"""
    # Mock data
    mock_search_results = [
        {"title": "Result 1", "content": "Content 1"}
    ]
    mock_content = "Synthesized content"
    
    # Setup mocks
    research_service.search_service.search.return_value = mock_search_results
    research_service.llm_service.generate.return_value = mock_content
    
    # Thực thi
    results = await research_service.execute(mock_request, mock_outline)
    
    # Kiểm tra kết quả
    assert len(results) == len(mock_outline.sections)
    for result in results:
        assert isinstance(result, ResearchSection)
        assert result.content == mock_content
    
    # Verify number of calls
    assert research_service.search_service.search.call_count == len(mock_outline.sections)
    assert research_service.llm_service.generate.call_count == len(mock_outline.sections)

@pytest.mark.asyncio
async def test_execute_error(research_service, mock_request, mock_outline):
    """Test thực thi toàn bộ phase nghiên cứu thất bại"""
    # Setup mock error
    research_service.search_service.search.side_effect = Exception("Search error")
    
    # Kiểm tra exception
    with pytest.raises(ResearchError) as exc_info:
        await research_service.execute(mock_request, mock_outline)
    
    assert "Lỗi trong quá trình nghiên cứu" in str(exc_info.value)
