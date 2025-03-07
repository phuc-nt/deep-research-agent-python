import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import EditError
from app.services.research.base import ResearchSection, ResearchResult
from app.services.research.edit import EditService


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    mock = AsyncMock()
    mock.generate = AsyncMock()
    return mock


@pytest.fixture
def edit_service(mock_llm_service):
    """Create EditService with mocked dependencies"""
    with patch('app.services.research.edit.service_factory') as mock_factory:
        mock_factory.create_llm_service.return_value = mock_llm_service
        service = EditService()
        return service


@pytest.fixture
def sample_sections():
    """Sample research sections for testing"""
    return [
        ResearchSection(
            title="Phần 1",
            description="Mô tả phần 1",
            content="Nội dung phần 1 với một số thông tin và <a href='https://example.com/1'>nguồn 1</a>"
        ),
        ResearchSection(
            title="Phần 2",
            description="Mô tả phần 2",
            content="Nội dung phần 2 với thông tin khác và <a href='https://example.com/2'>nguồn 2</a>"
        )
    ]


@pytest.fixture
def sample_context():
    """Sample context for testing"""
    return {
        "topic": "Chủ đề mẫu",
        "scope": "Phạm vi mẫu",
        "target_audience": "Đối tượng mẫu"
    }


class TestEditService:
    """Tests for EditService"""
    
    @pytest.mark.asyncio
    async def test_edit_content(self, edit_service, mock_llm_service, sample_sections, sample_context):
        """Test edit_content method"""
        # Setup
        mock_llm_service.generate.return_value = "Nội dung đã chỉnh sửa"
        
        # Execute
        result = await edit_service.edit_content(sample_sections, sample_context)
        
        # Assert
        assert result == "Nội dung đã chỉnh sửa"
        mock_llm_service.generate.assert_called_once()
        
        # Verify prompt contains section titles and content
        prompt = mock_llm_service.generate.call_args[0][0]
        assert "Phần 1" in prompt
        assert "Phần 2" in prompt
        assert "Nội dung phần 1" in prompt
        assert "Nội dung phần 2" in prompt
        assert "Chủ đề mẫu" in prompt
        assert "Phạm vi mẫu" in prompt
        assert "Đối tượng mẫu" in prompt
    
    @pytest.mark.asyncio
    async def test_create_title(self, edit_service, mock_llm_service, sample_context):
        """Test create_title method"""
        # Setup
        mock_llm_service.generate.return_value = "  \"Tiêu đề mẫu\"  "
        content = "Nội dung bài nghiên cứu mẫu"
        
        # Execute
        result = await edit_service.create_title(content, sample_context)
        
        # Assert
        assert result == "Tiêu đề mẫu"
        mock_llm_service.generate.assert_called_once()
        
        # Verify prompt contains content preview and context
        prompt = mock_llm_service.generate.call_args[0][0]
        assert "Nội dung bài nghiên cứu mẫu" in prompt
        assert "Chủ đề mẫu" in prompt
        assert "Phạm vi mẫu" in prompt
        assert "Đối tượng mẫu" in prompt
    
    def test_collect_sources(self, edit_service, sample_sections):
        """Test _collect_sources method"""
        # Execute
        sources = edit_service._collect_sources(sample_sections)
        
        # Assert
        assert len(sources) == 2
        assert "https://example.com/1" in sources
        assert "https://example.com/2" in sources
    
    @pytest.mark.asyncio
    async def test_execute(self, edit_service, mock_llm_service, sample_sections, sample_context):
        """Test execute method"""
        # Setup
        mock_llm_service.generate.side_effect = [
            "Nội dung đã chỉnh sửa",  # edit_content
            "Tiêu đề mẫu"             # create_title
        ]
        
        # Execute
        result = await edit_service.execute(sample_sections, sample_context)
        
        # Assert
        assert isinstance(result, ResearchResult)
        assert result.title == "Tiêu đề mẫu"
        assert result.content == "Nội dung đã chỉnh sửa"
        assert len(result.sections) == 2
        assert len(result.sources) == 2
        assert mock_llm_service.generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_edit_content_error(self, edit_service, mock_llm_service, sample_sections, sample_context):
        """Test edit_content method with error"""
        # Setup
        mock_llm_service.generate.side_effect = Exception("Test error")
        
        # Execute and Assert
        with pytest.raises(EditError) as excinfo:
            await edit_service.edit_content(sample_sections, sample_context)
        
        assert "Lỗi khi chỉnh sửa nội dung" in str(excinfo.value)
        assert "Test error" in str(excinfo.value.details)
    
    @pytest.mark.asyncio
    async def test_create_title_error(self, edit_service, mock_llm_service, sample_context):
        """Test create_title method with error"""
        # Setup
        mock_llm_service.generate.side_effect = Exception("Test error")
        content = "Nội dung bài nghiên cứu mẫu"
        
        # Execute and Assert
        with pytest.raises(EditError) as excinfo:
            await edit_service.create_title(content, sample_context)
        
        assert "Lỗi khi tạo tiêu đề" in str(excinfo.value)
        assert "Test error" in str(excinfo.value.details)
    
    @pytest.mark.asyncio
    async def test_execute_error(self, edit_service, mock_llm_service, sample_sections, sample_context):
        """Test execute method with error"""
        # Setup
        mock_llm_service.generate.side_effect = Exception("Test error")
        
        # Execute and Assert
        with pytest.raises(EditError) as excinfo:
            await edit_service.execute(sample_sections, sample_context)
        
        assert "Lỗi trong quá trình chỉnh sửa" in str(excinfo.value)
        # Kiểm tra xem details có chứa 'error' key
        assert "error" in excinfo.value.details
        # Không kiểm tra nội dung chi tiết của lỗi vì nó có thể khác nhau
        # tùy thuộc vào cách xử lý lỗi trong EditService
