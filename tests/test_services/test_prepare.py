import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import PrepareError
from app.services.research.base import ResearchRequest, ResearchOutline
from app.services.research.prepare import PrepareService

@pytest.fixture
def prepare_service():
    """Fixture tạo instance của PrepareService với các mock dependencies"""
    with patch("app.services.research.prepare.service_factory") as mock_factory:
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_factory.create_llm_service.return_value = mock_llm
        
        # Mock search service
        mock_search = AsyncMock()
        mock_factory.create_search_service.return_value = mock_search
        
        service = PrepareService()
        service.llm_service = mock_llm
        service.search_service = mock_search
        
        yield service

@pytest.mark.asyncio
async def test_analyze_query_success(prepare_service):
    """Test phân tích yêu cầu nghiên cứu thành công"""
    # Mock data
    request = ResearchRequest(query="Test research request")
    mock_response = {
        "Topic": "Test Topic",
        "Scope": "Test Scope",
        "Target Audience": "Test Audience"
    }
    prepare_service.llm_service.generate.return_value = json.dumps(mock_response)
    
    # Thực thi
    result = await prepare_service.analyze_query(request)
    
    # Kiểm tra kết quả
    assert result == mock_response
    assert request.topic == mock_response["Topic"]
    assert request.scope == mock_response["Scope"]
    assert request.target_audience == mock_response["Target Audience"]

@pytest.mark.asyncio
async def test_analyze_query_error(prepare_service):
    """Test phân tích yêu cầu nghiên cứu thất bại"""
    # Mock data
    request = ResearchRequest(query="Test research request")
    prepare_service.llm_service.generate.side_effect = Exception("Test error")
    
    # Kiểm tra exception
    with pytest.raises(PrepareError) as exc_info:
        await prepare_service.analyze_query(request)
    
    assert "Lỗi khi phân tích yêu cầu nghiên cứu" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_outline_success(prepare_service):
    """Test tạo dàn ý nghiên cứu thành công"""
    # Mock data
    analysis = {
        "Topic": "Test Topic",
        "Scope": "Test Scope",
        "Target Audience": "Test Audience"
    }
    mock_response = {
        "researchSections": [
            {
                "title": "Section 1",
                "description": "Description 1"
            },
            {
                "title": "Section 2",
                "description": "Description 2"
            }
        ]
    }
    prepare_service.llm_service.generate.return_value = json.dumps(mock_response)
    
    # Thực thi
    result = await prepare_service.create_outline(analysis)
    
    # Kiểm tra kết quả
    assert isinstance(result, ResearchOutline)
    assert len(result.sections) == 2
    assert result.sections[0].title == "Section 1"
    assert result.sections[0].description == "Description 1"
    assert result.sections[1].title == "Section 2"
    assert result.sections[1].description == "Description 2"

@pytest.mark.asyncio
async def test_create_outline_error(prepare_service):
    """Test tạo dàn ý nghiên cứu thất bại"""
    # Mock data
    analysis = {
        "Topic": "Test Topic",
        "Scope": "Test Scope",
        "Target Audience": "Test Audience"
    }
    prepare_service.llm_service.generate.side_effect = Exception("Test error")
    
    # Kiểm tra exception
    with pytest.raises(PrepareError) as exc_info:
        await prepare_service.create_outline(analysis)
    
    assert "Lỗi khi tạo dàn ý nghiên cứu" in str(exc_info.value)

@pytest.mark.asyncio
async def test_execute_success(prepare_service):
    """Test thực thi toàn bộ phase chuẩn bị thành công"""
    # Mock data
    request = ResearchRequest(query="Test research request")
    mock_analysis = {
        "Topic": "Test Topic",
        "Scope": "Test Scope",
        "Target Audience": "Test Audience"
    }
    mock_outline = {
        "researchSections": [
            {
                "title": "Section 1",
                "description": "Description 1"
            }
        ]
    }
    
    # Mock responses
    prepare_service.llm_service.generate.side_effect = [
        json.dumps(mock_analysis),
        json.dumps(mock_outline)
    ]
    
    # Thực thi
    result = await prepare_service.execute(request)
    
    # Kiểm tra kết quả
    assert isinstance(result, ResearchOutline)
    assert len(result.sections) == 1
    assert result.sections[0].title == "Section 1"
    assert result.sections[0].description == "Description 1"

@pytest.mark.asyncio
async def test_execute_error(prepare_service):
    """Test thực thi toàn bộ phase chuẩn bị thất bại"""
    # Mock data
    request = ResearchRequest(query="Test research request")
    prepare_service.llm_service.generate.side_effect = Exception("Test error")
    
    # Kiểm tra exception
    with pytest.raises(PrepareError) as exc_info:
        await prepare_service.execute(request)
    
    assert "Lỗi trong quá trình chuẩn bị" in str(exc_info.value)
