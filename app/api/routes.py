from fastapi import APIRouter, HTTPException, BackgroundTasks
from uuid import uuid4
from datetime import datetime
from typing import Dict, Optional

from app.models.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
    ResearchOutline,
    ResearchResult,
    ResearchError
)
from app.services.research.prepare import PrepareService
from app.services.research.research import ResearchService
from app.services.research.edit import EditService
from app.core.exceptions import BaseError

router = APIRouter()

# Lưu trữ tạm thời các research tasks (trong thực tế nên dùng database)
research_tasks: Dict[str, ResearchResponse] = {}

async def process_research(task_id: str, request: ResearchRequest):
    """
    Xử lý yêu cầu nghiên cứu trong background
    
    Args:
        task_id: ID của research task
        request: Yêu cầu nghiên cứu
    """
    try:
        # Khởi tạo các services
        prepare_service = PrepareService()
        research_service = ResearchService()
        edit_service = EditService()
        
        # Cập nhật trạng thái: Đang phân tích
        research_tasks[task_id].status = ResearchStatus.ANALYZING
        research_tasks[task_id].updated_at = datetime.utcnow()
        
        # Phase 1: Prepare - Phân tích yêu cầu và tạo dàn ý
        research_tasks[task_id].status = ResearchStatus.OUTLINING
        research_tasks[task_id].updated_at = datetime.utcnow()
        outline = await prepare_service.execute(request)
        research_tasks[task_id].outline = outline
        
        # Phase 2: Research - Nghiên cứu chi tiết
        research_tasks[task_id].status = ResearchStatus.RESEARCHING
        research_tasks[task_id].updated_at = datetime.utcnow()
        researched_sections = await research_service.execute(request, outline)
        
        # Phase 3: Edit - Chỉnh sửa và hoàn thiện
        research_tasks[task_id].status = ResearchStatus.EDITING
        research_tasks[task_id].updated_at = datetime.utcnow()
        result = await edit_service.execute(researched_sections, {
            "topic": request.topic,
            "scope": request.scope,
            "target_audience": request.target_audience
        })
        
        # Cập nhật kết quả và trạng thái
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].result = result
        research_tasks[task_id].updated_at = datetime.utcnow()
        
    except BaseError as e:
        # Xử lý lỗi từ services
        research_tasks[task_id].status = ResearchStatus.FAILED
        research_tasks[task_id].error = ResearchError(
            message=str(e),
            details=e.details
        )
        research_tasks[task_id].updated_at = datetime.utcnow()
        
    except Exception as e:
        # Xử lý lỗi không xác định
        research_tasks[task_id].status = ResearchStatus.FAILED
        research_tasks[task_id].error = ResearchError(
            message="Lỗi không xác định",
            details={"error": str(e)}
        )
        research_tasks[task_id].updated_at = datetime.utcnow()

@router.post("/research", response_model=ResearchResponse)
async def create_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
) -> ResearchResponse:
    """
    Tạo một yêu cầu nghiên cứu mới.
    
    Args:
        request: Yêu cầu nghiên cứu
        background_tasks: Background tasks runner
        
    Returns:
        ResearchResponse: Thông tin về research task
    """
    # Tạo task ID mới
    task_id = str(uuid4())
    
    # Tạo response object
    response = ResearchResponse(
        id=task_id,
        status=ResearchStatus.PENDING,
        request=request,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Lưu task
    research_tasks[task_id] = response
    
    # Thêm task vào background processing
    background_tasks.add_task(process_research, task_id, request)
    
    return response

@router.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(research_id: str) -> ResearchResponse:
    """
    Lấy thông tin và kết quả của một research task.
    
    Args:
        research_id: ID của research task
        
    Returns:
        ResearchResponse: Thông tin và kết quả của research task
        
    Raises:
        HTTPException: Nếu không tìm thấy research task
    """
    if research_id not in research_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy research task với ID: {research_id}"
        )
    
    return research_tasks[research_id]

@router.get("/research/{research_id}/status", response_model=ResearchStatus)
async def get_research_status(research_id: str) -> ResearchStatus:
    """
    Lấy trạng thái của một research task.
    
    Args:
        research_id: ID của research task
        
    Returns:
        ResearchStatus: Trạng thái hiện tại của research task
        
    Raises:
        HTTPException: Nếu không tìm thấy research task
    """
    if research_id not in research_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy research task với ID: {research_id}"
        )
    
    return research_tasks[research_id].status

@router.get("/research/{research_id}/outline", response_model=Optional[ResearchOutline])
async def get_research_outline(research_id: str) -> Optional[ResearchOutline]:
    """
    Lấy dàn ý của một research task.
    
    Args:
        research_id: ID của research task
        
    Returns:
        Optional[ResearchOutline]: Dàn ý của research task hoặc None nếu chưa có
        
    Raises:
        HTTPException: Nếu không tìm thấy research task
    """
    if research_id not in research_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy research task với ID: {research_id}"
        )
    
    return research_tasks[research_id].outline 