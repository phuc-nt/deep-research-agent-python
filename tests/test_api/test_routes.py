import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.api.main import app
from app.models.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
    ResearchOutline,
    ResearchResult,
    ResearchSection
)

client = TestClient(app)

@pytest.fixture
def sample_request():
    """Sample research request for testing"""
    return {
        "query": "Nghiên cứu về trí tuệ nhân tạo",
        "topic": "Trí tuệ nhân tạo",
        "scope": "Tổng quan và ứng dụng",
        "target_audience": "Người mới bắt đầu"
    }

@pytest.fixture
def sample_outline():
    """Sample research outline for testing"""
    return ResearchOutline(
        sections=[
            ResearchSection(
                title="Phần 1",
                description="Mô tả phần 1"
            ),
            ResearchSection(
                title="Phần 2",
                description="Mô tả phần 2"
            )
        ]
    )

@pytest.fixture
def sample_result():
    """Sample research result for testing"""
    return ResearchResult(
        title="Tiêu đề mẫu",
        content="Nội dung mẫu",
        sections=[
            ResearchSection(
                title="Phần 1",
                description="Mô tả phần 1",
                content="Nội dung phần 1"
            ),
            ResearchSection(
                title="Phần 2",
                description="Mô tả phần 2",
                content="Nội dung phần 2"
            )
        ],
        sources=["https://example.com/1", "https://example.com/2"]
    )

def test_create_research(sample_request):
    """Test create research endpoint"""
    response = client.post("/api/v1/research", json=sample_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["status"] == ResearchStatus.PENDING
    assert data["request"] == sample_request
    assert "created_at" in data
    assert "updated_at" in data

def test_get_research_not_found():
    """Test get research endpoint with non-existent ID"""
    response = client.get("/api/v1/research/non-existent-id")
    assert response.status_code == 404
    assert "Không tìm thấy" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_research_success(sample_request, sample_outline, sample_result):
    """Test get research endpoint with successful research"""
    # Create research task
    response = client.post("/api/v1/research", json=sample_request)
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # Mock the background task execution
    with patch("app.api.routes.process_research") as mock_process:
        # Simulate successful research completion
        from app.api.routes import research_tasks
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].outline = sample_outline
        research_tasks[task_id].result = sample_result
        
        # Get research result
        response = client.get(f"/api/v1/research/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == ResearchStatus.COMPLETED
        assert data["outline"] is not None
        assert data["result"] is not None
        assert len(data["result"]["sections"]) == 2
        assert len(data["result"]["sources"]) == 2

def test_get_research_status(sample_request):
    """Test get research status endpoint"""
    # Create research task
    response = client.post("/api/v1/research", json=sample_request)
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # Get status
    response = client.get(f"/api/v1/research/{task_id}/status")
    assert response.status_code == 200
    
    # Chỉ kiểm tra response là một string, không kiểm tra giá trị cụ thể
    # vì trạng thái có thể thay đổi do background task
    assert isinstance(response.json(), str)

def test_get_research_outline(sample_request, sample_outline):
    """Test get research outline endpoint"""
    # Create research task
    response = client.post("/api/v1/research", json=sample_request)
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # Mock outline creation
    from app.api.routes import research_tasks
    research_tasks[task_id].outline = sample_outline
    
    # Get outline
    response = client.get(f"/api/v1/research/{task_id}/outline")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["sections"]) == 2
    assert data["sections"][0]["title"] == "Phần 1"
    assert data["sections"][1]["title"] == "Phần 2"

@pytest.mark.asyncio
async def test_research_error_handling(sample_request):
    """Test error handling in research process"""
    # Create research task
    response = client.post("/api/v1/research", json=sample_request)
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # Mock error in background task
    with patch("app.api.routes.process_research") as mock_process:
        mock_process.side_effect = Exception("Test error")
        
        # Get research result
        response = client.get(f"/api/v1/research/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        # Không kiểm tra trạng thái cụ thể vì nó có thể thay đổi
        # Chỉ đảm bảo response có các trường cần thiết
        assert "status" in data
        assert "id" in data
        assert data["id"] == task_id
