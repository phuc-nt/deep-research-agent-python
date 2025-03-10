from fastapi import APIRouter, HTTPException, BackgroundTasks
from uuid import uuid4
from datetime import datetime
from typing import Dict, Optional, List, Any
import time
import asyncio
import json

from pydantic import ValidationError

from app.models.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
    ResearchOutline,
    ResearchSection,
    ResearchResult,
    ResearchError,
    ResearchCostInfo,
    EditRequest
)
from app.models.cost import PhaseTimingInfo, ResearchCostMonitoring
from app.services.research.prepare import PrepareService
from app.services.research.research import ResearchService
from app.services.research.edit import EditService
from app.services.research.storage import ResearchStorageService
from app.services.core.storage.github import GitHubService
from app.core.exceptions import BaseError
from app.core.config import get_settings
from app.core.factory import get_service_factory
from app.core.logging import logger

router = APIRouter()

# Health check endpoint
@router.get("/health", tags=["Health"])
async def health_check():
    """
    Kiểm tra trạng thái hoạt động của API.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "deep-research-agent",
        "version": "1.0.0"
    }

# Lưu trữ tạm thời các research tasks (trong thực tế nên dùng database)
research_tasks: Dict[str, ResearchResponse] = {}

# Khởi tạo ResearchStorageService
research_storage_service = ResearchStorageService()

async def process_research(task_id: str, request: ResearchRequest):
    """
    Xử lý yêu cầu nghiên cứu trong background
    
    Args:
        task_id: ID của research task
        request: Yêu cầu nghiên cứu
    """
    try:
        logger.info(f"=== BẮT ĐẦU XỬ LÝ RESEARCH TASK {task_id} ===")
        logger.info(f"Thông tin yêu cầu: Query: '{request.query}', Topic: '{request.topic}', Scope: '{request.scope}', Target Audience: '{request.target_audience}'")
        
        # Khởi tạo các services
        prepare_service = PrepareService()
        research_service = ResearchService()
        
        # Thiết lập callback để cập nhật tiến độ
        async def update_progress_callback(progress_info: Dict[str, Any]):
            if task_id in research_tasks:
                research_tasks[task_id].progress_info = progress_info
                research_tasks[task_id].updated_at = datetime.utcnow()
                await research_storage_service.save_task(research_tasks[task_id])
        
        # Gán callback cho research_service
        research_service.update_progress_callback = update_progress_callback
        
        # Gán task_id vào request để các service có thể sử dụng
        request.task_id = task_id
        
        # Phase 1: Chuẩn bị
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHUẨN BỊ ===")
        research_tasks[task_id].status = ResearchStatus.ANALYZING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "analyzing",
            "message": "Đang phân tích yêu cầu nghiên cứu",
            "timestamp": datetime.utcnow().isoformat()
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        analysis = await prepare_service.analyze_query(request.query, task_id)
        end_time = time.time()
        
        # Chuẩn hóa kết quả phân tích (kiểm tra cả viết hoa và viết thường)
        topic = analysis.get("Topic") or analysis.get("topic", request.query)
        scope = analysis.get("Scope") or analysis.get("scope", "Phân tích toàn diện")
        target_audience = analysis.get("Target Audience") or analysis.get("target_audience", "Người đọc quan tâm đến chủ đề")
        
        logger.info(f"[Task {task_id}] Phân tích yêu cầu hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Kết quả phân tích: Topic: '{topic}', Scope: '{scope}', Target Audience: '{target_audience}'")
        
        # Cập nhật request với thông tin phân tích đã chuẩn hóa
        request.topic = topic
        request.scope = scope
        request.target_audience = target_audience
        
        # Cập nhật task với request đã cập nhật
        research_tasks[task_id].request = request
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "analyzed",
            "message": "Đã phân tích xong yêu cầu nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": {
                "topic": topic,
                "scope": scope,
                "target_audience": target_audience
            }
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Tạo dàn ý
        logger.info(f"[Task {task_id}] === BẮT ĐẦU TẠO DÀN Ý ===")
        research_tasks[task_id].status = ResearchStatus.OUTLINING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "outlining",
            "message": "Đang tạo dàn ý cho bài nghiên cứu",
            "timestamp": datetime.utcnow().isoformat()
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        outline = await prepare_service.create_outline(request, task_id)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Tạo dàn ý hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Dàn ý có {len(outline.sections)} phần")
        
        # Lưu outline vào task
        research_tasks[task_id].outline = outline
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "outlined",
            "message": "Đã tạo xong dàn ý cho bài nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "outline_sections_count": len(outline.sections)
        }
        await research_storage_service.save_outline(task_id, outline)
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Phase 2: Nghiên cứu
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE NGHIÊN CỨU ===")
        research_tasks[task_id].status = ResearchStatus.RESEARCHING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "researching",
            "message": "Đang bắt đầu nghiên cứu các phần",
            "timestamp": datetime.utcnow().isoformat(),
            "current_section": 0,
            "total_sections": len(outline.sections),
            "completed_sections": 0
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        # Đảm bảo outline có task_id
        outline.task_id = task_id
        researched_sections = await research_service.execute(request, outline)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase nghiên cứu hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Đã nghiên cứu {len(researched_sections)}/{len(outline.sections)} phần")
        
        # Lưu researched_sections vào task
        research_tasks[task_id].sections = researched_sections
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "researched",
            "message": "Đã hoàn thành nghiên cứu tất cả các phần",
            "timestamp": datetime.utcnow().isoformat(),
            "total_sections": len(outline.sections),
            "completed_sections": len(researched_sections),
            "time_taken": f"{end_time - start_time:.2f} giây"
        }
        await research_storage_service.save_sections(task_id, researched_sections)
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Cập nhật trạng thái task thành completed
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "completed",
            "message": "Đã hoàn thành nghiên cứu, sẵn sàng cho giai đoạn chỉnh sửa",
            "timestamp": datetime.utcnow().isoformat(),
            "sections_count": len(researched_sections),
            "outline_sections_count": len(outline.sections),
            "total_time": f"{(datetime.utcnow() - research_tasks[task_id].created_at).total_seconds():.2f} giây"
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"[Task {task_id}] === HOÀN THÀNH RESEARCH TASK ===")
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Lỗi khi xử lý research task: {str(e)}")
        
        # Cập nhật trạng thái task thành failed
        if task_id in research_tasks:
            research_tasks[task_id].status = ResearchStatus.FAILED
            research_tasks[task_id].error = ResearchError(
                message="Lỗi trong quá trình xử lý research task",
                details={"error": str(e)}
            )
            research_tasks[task_id].updated_at = datetime.utcnow()
            research_tasks[task_id].progress_info = {
                "phase": "failed",
                "message": f"Lỗi trong quá trình xử lý: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            await research_storage_service.save_task(research_tasks[task_id])

@router.post("/research", response_model=ResearchResponse)
async def create_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
) -> ResearchResponse:
    """
    Tạo một yêu cầu nghiên cứu mới
    
    Endpoint này khởi tạo một yêu cầu nghiên cứu mới và thực hiện các bước phân tích, tạo dàn ý và nghiên cứu. 
    **Lưu ý**: Sau khi nghiên cứu hoàn thành, bạn cần gọi thêm endpoint `/api/v1/research/edit_only` để chỉnh sửa và hoàn thiện nội dung.
    
    Args:
        request: Thông tin yêu cầu nghiên cứu
        background_tasks: Background tasks để xử lý nghiên cứu
        
    Returns:
        ResearchResponse: Thông tin về research task đã tạo
        
    Examples:
        ```json
        # Request
        {
          "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
          "topic": "Trí tuệ nhân tạo trong giáo dục",
          "scope": "Tổng quan và ứng dụng thực tế",
          "target_audience": "Giáo viên và nhà quản lý giáo dục"
        }
        
        # Response
        {
          "id": "ca214ee5-6204-4f3d-98c4-4f558e27399b",
          "status": "pending",
          "request": {
            "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
            "topic": "Trí tuệ nhân tạo trong giáo dục",
            "scope": "Tổng quan và ứng dụng thực tế",
            "target_audience": "Giáo viên và nhà quản lý giáo dục"
          },
          "outline": null,
          "result": null,
          "error": null,
          "github_url": null,
          "progress_info": {
            "phase": "pending",
            "message": "Đã nhận yêu cầu nghiên cứu, đang chuẩn bị xử lý",
            "timestamp": "2023-03-11T10:15:30.123456"
          },
          "created_at": "2023-03-11T10:15:30.123456",
          "updated_at": "2023-03-11T10:15:30.123456"
        }
        ```
        
        > **Lưu ý**: Khi chỉ cung cấp `query`, hệ thống sẽ tự động phân tích để xác định `topic`, `scope` và `target_audience`.
    """
    try:
        logger.info(f"Nhận yêu cầu nghiên cứu mới: {request.topic or request.query}")
        
        # Tạo ID cho research task
        task_id = str(uuid4())
        
        # Tạo research task với thông tin tiến độ ban đầu
        research_tasks[task_id] = ResearchResponse(
            id=task_id,
            request=request,
            status=ResearchStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            progress_info={
                "phase": "pending",
                "message": "Đã nhận yêu cầu nghiên cứu, đang chuẩn bị xử lý",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Lưu task vào file
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"Đã tạo research task {task_id}")
        
        # Chạy quá trình nghiên cứu trong background
        background_tasks.add_task(process_research, task_id, request)
        
        return research_tasks[task_id]
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo research task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo research task: {str(e)}"
        )

@router.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(research_id: str) -> ResearchResponse:
    """
    Lấy thông tin đầy đủ về một research task
    
    Endpoint này trả về toàn bộ thông tin của một research task bao gồm yêu cầu gốc,
    dàn ý, nội dung đã nghiên cứu, kết quả hoàn chỉnh (nếu có), và các thông tin khác.
    
    Args:
        research_id: ID của research task
    
    Returns:
        ResearchResponse: Thông tin đầy đủ của research task
        
    Raises:
        HTTPException: Nếu không tìm thấy research task
        
    Examples:
        ```
        {
          "id": "ca214ee5-6204-4f3d-98c4-4f558e27399b",
          "status": "completed",
          "request": {
            "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
            "topic": "Trí tuệ nhân tạo trong giáo dục",
            "scope": "Tổng quan và ứng dụng thực tế",
            "target_audience": "Giáo viên và nhà quản lý giáo dục"
          },
          "outline": {
            "sections": [
              {
                "title": "Giới thiệu về trí tuệ nhân tạo trong giáo dục",
                "description": "Tổng quan về AI và vai trò trong lĩnh vực giáo dục",
                "content": "..."
              }
            ]
          },
          "result": {
            "title": "Trí tuệ nhân tạo trong giáo dục: Hiện tại và tương lai",
            "content": "...",
            "sections": [],
            "sources": [
              "https://example.com/source1",
              "https://example.com/source2"
            ]
          },
          "error": null,
          "github_url": "https://github.com/username/repo/research-123",
          "progress_info": {
            "phase": "completed",
            "message": "Đã hoàn thành toàn bộ quá trình nghiên cứu",
            "timestamp": "2023-03-11T10:20:45.678901",
            "time_taken": "302.5 giây",
            "content_length": 12405,
            "sources_count": 15,
            "total_time": "305.3 giây"
          },
          "created_at": "2023-03-11T10:15:30.123456",
          "updated_at": "2023-03-11T10:20:45.678901"
        }
        ```
    """
    try:
        logger.info(f"Lấy thông tin đầy đủ research task {research_id}")
        
        # Kiểm tra trong bộ nhớ
        if research_id not in research_tasks:
            # Thử tải từ file
            logger.info(f"Task {research_id} không có trong bộ nhớ, thử tải từ file...")
            task = await research_storage_service.load_full_task(research_id)
            
            if task:
                # Cập nhật vào bộ nhớ
                research_tasks[research_id] = task
                logger.info(f"Đã tải đầy đủ task {research_id} từ file, trạng thái: {task.status}")
            else:
                logger.error(f"Không tìm thấy research task {research_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Research task {research_id} not found"
                )
        else:
            # Nếu task đã có trong bộ nhớ nhưng chưa có đầy đủ thông tin
            task = research_tasks[research_id]
            
            # Tải outline nếu chưa có
            if not task.outline:
                outline = await research_storage_service.load_outline(research_id)
                if outline:
                    task.outline = outline
            
            # Tải sections nếu chưa có
            if not task.sections and task.status in [ResearchStatus.EDITING, ResearchStatus.COMPLETED]:
                sections = await research_storage_service.load_sections(research_id)
                if sections:
                    task.sections = sections
            
            # Tải result nếu chưa có
            if not task.result and task.status == ResearchStatus.COMPLETED:
                result = await research_storage_service.load_result(research_id)
                if result:
                    task.result = result
            
        return research_tasks[research_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin research task {research_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/research/{research_id}/status", response_model=Dict[str, Any])
async def get_research_status(research_id: str) -> Dict[str, Any]:
    """
    Lấy trạng thái của một research task.
    
    Args:
        research_id: ID của research task
        
    Returns:
        Dict[str, Any]: Trạng thái hiện tại và thông tin chi tiết về tiến độ của research task
        
    Raises:
        HTTPException: Nếu không tìm thấy research task
    """
    if research_id not in research_tasks:
        # Thử tải từ file
        task = await research_storage_service.load_task(research_id)
        if task:
            research_tasks[research_id] = task
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy research task với ID: {research_id}"
            )
    
    task = research_tasks[research_id]
    
    # Tạo response với thông tin chi tiết
    response = {
        "status": task.status,
        "progress_info": task.progress_info or {}
    }
    
    # Bổ sung thông tin chi tiết dựa trên trạng thái
    if task.status == ResearchStatus.RESEARCHING and task.outline:
        total_sections = len(task.outline.sections)
        current_section = response["progress_info"].get("current_section", 0)
        
        # Thêm thông tin về section hiện tại
        if 0 < current_section <= total_sections:
            section = task.outline.sections[current_section - 1]
            response["progress_info"]["current_section_title"] = section.title
            response["progress_info"]["current_section_description"] = section.description
        
        # Tính phần trăm hoàn thành
        completed_percentage = (current_section / total_sections) * 100 if total_sections > 0 else 0
        response["progress_info"]["completed_percentage"] = round(completed_percentage, 2)
    
    return response

@router.get("/research/{research_id}/outline", response_model=ResearchOutline)
async def get_research_outline(research_id: str) -> ResearchOutline:
    """
    Lấy dàn ý của một research task.
    
    Args:
        research_id: ID của research task
        
    Returns:
        ResearchOutline: Dàn ý của research task
    """
    try:
        # Kiểm tra task tồn tại
        if research_id not in research_tasks:
            # Thử tải từ file
            task = await research_storage_service.load_task(research_id)
            if task:
                research_tasks[research_id] = task
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Research task {research_id} not found"
                )
        
        # Kiểm tra outline tồn tại
        if not research_tasks[research_id].outline:
            # Thử tải outline từ file
            outline = await research_storage_service.load_outline(research_id)
            if outline:
                research_tasks[research_id].outline = outline
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Outline for research task {research_id} not found"
                )
        
        return research_tasks[research_id].outline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy outline của research task {research_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/research", response_model=List[Dict[str, Any]])
async def list_research() -> List[Dict[str, Any]]:
    """
    Liệt kê tất cả các research tasks với thông tin tóm tắt
    
    Returns:
        List[Dict[str, Any]]: Danh sách các research tasks với thông tin tóm tắt
    """
    try:
        logger.info("Liệt kê tất cả research tasks")
        
        # Tải tất cả tasks từ file nếu chưa có trong bộ nhớ
        task_ids = await research_storage_service.list_tasks()
        
        for task_id in task_ids:
            if task_id not in research_tasks:
                # Chỉ tải thông tin cơ bản của task
                task = await research_storage_service.load_task(task_id)
                if task:
                    research_tasks[task_id] = task
        
        # Tạo danh sách tasks với thông tin tóm tắt
        summary_tasks = []
        for task in research_tasks.values():
            # Tạo thông tin tóm tắt cho mỗi task
            task_summary = {
                "id": task.id,
                "status": task.status,
                "query": task.request.query if task.request else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "progress_summary": {}
            }
            
            # Thêm thông tin tiến độ tóm tắt
            if task.progress_info:
                task_summary["progress_summary"] = {
                    "phase": task.progress_info.get("phase"),
                    "message": task.progress_info.get("message"),
                    "timestamp": task.progress_info.get("timestamp")
                }
            
            # Thêm thông tin về thời gian đã trôi qua
            if task.created_at:
                elapsed_time = datetime.utcnow() - task.created_at
                task_summary["elapsed_time"] = str(elapsed_time).split('.')[0]  # HH:MM:SS format
            
            # Thêm thông tin về outline và sections nếu có
            if task.outline:
                task_summary["outline_sections_count"] = len(task.outline.sections)
            
            if task.sections:
                task_summary["researched_sections_count"] = len(task.sections)
            
            # Thêm URL GitHub nếu có
            if task.github_url:
                task_summary["github_url"] = task.github_url
            
            # Thêm thông tin lỗi nếu có
            if task.error:
                task_summary["error"] = task.error.message
            
            summary_tasks.append(task_summary)
        
        # Sắp xếp theo thời gian tạo, mới nhất lên đầu
        summary_tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"Đã liệt kê {len(summary_tasks)} research tasks")
        
        return summary_tasks
        
    except Exception as e:
        logger.error(f"Lỗi khi liệt kê research tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/research/edit_only", response_model=ResearchResponse)
async def continue_with_editing(
    request: EditRequest,
    background_tasks: BackgroundTasks
) -> ResearchResponse:
    """
    Tiếp tục xử lý giai đoạn chỉnh sửa cho task được chỉ định
    
    Args:
        request (EditRequest): Request chứa research_id cần chỉnh sửa
        background_tasks: Background tasks để xử lý chỉnh sửa
    
    Returns:
        ResearchResponse: Thông tin về research task đã cập nhật
    """
    try:
        research_id = request.research_id
        
        # Tải task đầy đủ
        task = await research_storage_service.load_full_task(research_id)
        if not task:
            logger.error(f"Không thể tải đầy đủ thông tin task {research_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Không thể tải đầy đủ thông tin task {research_id}"
            )
        
        logger.info(f"Tìm thấy task với ID: {research_id}")
        
        # Kiểm tra xem task có đủ dữ liệu để tiếp tục không
        if not task.request:
            logger.error(f"Task {research_id} không có thông tin request")
            raise HTTPException(
                status_code=400,
                detail=f"Task {research_id} không có thông tin request"
            )
        
        # Tải outline và sections từ file
        outline = task.outline
        if not outline:
            logger.error(f"Task {research_id} không có outline")
            raise HTTPException(
                status_code=400,
                detail=f"Task {research_id} không có outline"
            )
        
        sections = task.sections
        if not sections:
            logger.error(f"Task {research_id} không có sections")
            raise HTTPException(
                status_code=400,
                detail=f"Task {research_id} không có sections"
            )
        
        # Cập nhật trạng thái task và thông tin tiến độ
        task.status = ResearchStatus.EDITING
        task.updated_at = datetime.utcnow()
        task.progress_info = {
            "phase": "editing",
            "message": "Đang bắt đầu giai đoạn chỉnh sửa từ dữ liệu nghiên cứu có sẵn",
            "timestamp": datetime.utcnow().isoformat(),
            "sections_count": len(sections),
            "outline_sections_count": len(outline.sections) if outline else 0
        }
        
        # Lưu task vào bộ nhớ và file
        research_tasks[research_id] = task
        await research_storage_service.save_task(task)
        
        logger.info(f"Đã cập nhật task {research_id} để tiếp tục xử lý giai đoạn chỉnh sửa")
        logger.info(f"Thông tin yêu cầu: Query: '{task.request.query}', Topic: '{task.request.topic}', Scope: '{task.request.scope}', Target Audience: '{task.request.target_audience}'")
        logger.info(f"Số phần đã nghiên cứu: {len(sections)}")
        
        # Chạy quá trình chỉnh sửa trong background
        background_tasks.add_task(process_research_with_sections, research_id, task.request, outline, sections)
        
        return task
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Lỗi khi tiếp tục xử lý giai đoạn chỉnh sửa: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tiếp tục xử lý giai đoạn chỉnh sửa: {str(e)}"
        )

async def process_research_with_sections(
    task_id: str, 
    request: ResearchRequest,
    outline: ResearchOutline,
    sections: List[ResearchSection]
):
    """
    Xử lý yêu cầu nghiên cứu với sections có sẵn trong background
    
    Args:
        task_id: ID của research task
        request: Yêu cầu nghiên cứu
        outline: Dàn ý nghiên cứu
        sections: Danh sách các phần đã nghiên cứu
    """
    try:
        logger.info(f"=== BẮT ĐẦU XỬ LÝ RESEARCH TASK {task_id} VỚI SECTIONS CÓ SẴN ===")
        logger.info(f"Thông tin yêu cầu: Query: '{request.query}', Topic: '{request.topic}', Scope: '{request.scope}', Target Audience: '{request.target_audience}'")
        
        # Khởi tạo các services
        edit_service = EditService()
        
        # Gán task_id vào request để các service có thể sử dụng
        request.task_id = task_id
        
        # Phase 3: Chỉnh sửa
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHỈNH SỬA ===")
        research_tasks[task_id].status = ResearchStatus.EDITING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "editing",
            "message": "Đang tổng hợp và chỉnh sửa nội dung từ các phần đã nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "sections_count": len(sections),
            "outline_sections_count": len(outline.sections) if outline else 0,
            "step": "starting"
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        
        # Cập nhật tiến độ trước khi bắt đầu chỉnh sửa
        research_tasks[task_id].progress_info.update({
            "step": "processing",
            "message": "Đang xử lý và tổng hợp nội dung từ các phần nghiên cứu",
            "timestamp": datetime.utcnow().isoformat()
        })
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Đảm bảo outline có task_id
        outline.task_id = task_id
        result = await edit_service.execute(request, outline, sections)
        end_time = time.time()
        
        # Cập nhật tiến độ sau khi hoàn thành chỉnh sửa
        research_tasks[task_id].progress_info.update({
            "step": "completed_editing",
            "message": "Đã hoàn thành chỉnh sửa nội dung",
            "timestamp": datetime.utcnow().isoformat(),
            "time_taken": f"{end_time - start_time:.2f} giây",
            "content_length": len(result.content),
            "sources_count": len(result.sources)
        })
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"[Task {task_id}] Phase chỉnh sửa hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Kết quả: Tiêu đề: '{result.title}', Độ dài nội dung: {len(result.content)} ký tự, Số nguồn: {len(result.sources)}")
        
        # Lưu kết quả vào file
        await research_storage_service.save_result(task_id, result)
        
        # Cập nhật tiến độ trước khi lưu lên GitHub
        research_tasks[task_id].progress_info.update({
            "step": "saving_to_github",
            "message": "Đang lưu kết quả nghiên cứu lên GitHub",
            "timestamp": datetime.utcnow().isoformat()
        })
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Lưu kết quả lên GitHub
        logger.info(f"[Task {task_id}] === BẮT ĐẦU LƯU KẾT QUẢ LÊN GITHUB ===")
        
        # Tạo nội dung Markdown
        markdown_content = f"# {result.title}\n\n{result.content}\n\n## Nguồn tham khảo\n\n"
        for idx, source in enumerate(result.sources):
            markdown_content += f"{idx+1}. [{source}]({source})\n"
        
        logger.info(f"[Task {task_id}] Đã tạo nội dung Markdown với {len(markdown_content)} ký tự")
        
        # Lưu lên GitHub
        try:
            github_service = get_service_factory().create_storage_service("github")
            file_path = f"researches/{task_id}/result.md"
            logger.info(f"[Task {task_id}] Đường dẫn file: {file_path}")
            
            start_time = time.time()
            github_url = await github_service.save(markdown_content, file_path)
            end_time = time.time()
            
            logger.info(f"[Task {task_id}] Đã lưu kết quả lên GitHub trong {end_time - start_time:.2f} giây")
            logger.info(f"[Task {task_id}] URL GitHub: {github_url}")
            
            # Cập nhật URL GitHub vào task
            research_tasks[task_id].github_url = github_url
        except Exception as e:
            logger.error(f"[Task {task_id}] Lỗi khi lưu kết quả lên GitHub: {str(e)}")
        
        # Cập nhật trạng thái task
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].result = result
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "completed",
            "message": "Đã hoàn thành toàn bộ quá trình nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "content_length": len(result.content),
            "sources_count": len(result.sources),
            "total_time": f"{(datetime.utcnow() - research_tasks[task_id].created_at).total_seconds():.2f} giây"
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"[Task {task_id}] === HOÀN THÀNH RESEARCH TASK {task_id} - THÀNH CÔNG ===")
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Lỗi khi xử lý research task {task_id}: {str(e)}")
        
        # Cập nhật trạng thái task thành failed
        if task_id in research_tasks:
            research_tasks[task_id].status = ResearchStatus.FAILED
            research_tasks[task_id].error = ResearchError(
                message="Lỗi trong quá trình xử lý research task",
                details={"error": str(e)}
            )
            research_tasks[task_id].updated_at = datetime.utcnow()
            research_tasks[task_id].progress_info = {
                "phase": "failed",
                "message": f"Lỗi trong quá trình xử lý: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            await research_storage_service.save_task(research_tasks[task_id])

@router.get("/research/{research_id}/progress", response_model=Dict[str, Any])
async def get_research_progress(research_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết về tiến độ của một research task.
    
    Args:
        research_id: ID của research task
        
    Returns:
        Dict[str, Any]: Thông tin chi tiết về tiến độ của research task
        
    Raises:
        HTTPException: Nếu không tìm thấy research task
    """
    if research_id not in research_tasks:
        # Thử tải từ file
        task = await research_storage_service.load_task(research_id)
        if task:
            research_tasks[research_id] = task
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy research task với ID: {research_id}"
            )
    
    task = research_tasks[research_id]
    
    # Tạo response với thông tin chi tiết về tiến độ
    response = {
        "id": task.id,
        "status": task.status,
        "progress_info": task.progress_info or {},
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "query": task.request.query if task.request else None
    }
    
    # Thêm thông tin về thời gian đã trôi qua
    if task.created_at:
        elapsed_time = datetime.utcnow() - task.created_at
        response["elapsed_time"] = {
            "seconds": elapsed_time.total_seconds(),
            "minutes": elapsed_time.total_seconds() / 60,
            "hours": elapsed_time.total_seconds() / 3600,
            "formatted": str(elapsed_time).split('.')[0]  # HH:MM:SS format
        }
    
    # Thêm thông tin về outline nếu có
    if task.outline:
        response["outline_sections_count"] = len(task.outline.sections)
    
    # Thêm thông tin về sections đã nghiên cứu nếu có
    if task.sections:
        response["researched_sections_count"] = len(task.sections)
        
        # Tính phần trăm hoàn thành dựa trên số sections đã nghiên cứu
        if task.outline and len(task.outline.sections) > 0:
            completion_percentage = (len(task.sections) / len(task.outline.sections)) * 100
            response["completion_percentage"] = round(completion_percentage, 2)
    
    # Thêm thông tin về kết quả nếu đã hoàn thành
    if task.result:
        response["result_info"] = {
            "title": task.result.title,
            "content_length": len(task.result.content) if task.result.content else 0,
            "sources_count": len(task.result.sources) if task.result.sources else 0
        }
    
    # Thêm thông tin về lỗi nếu có
    if task.error:
        response["error_info"] = {
            "message": task.error.message,
            "details": task.error.details
        }
    
    # Thêm URL GitHub nếu có
    if task.github_url:
        response["github_url"] = task.github_url
    
    return response 

@router.post("/research/complete", response_model=ResearchResponse)
async def create_complete_research(request: ResearchRequest, background_tasks: BackgroundTasks) -> ResearchResponse:
    """
    Tạo yêu cầu nghiên cứu mới và thực hiện toàn bộ quy trình từ đầu đến cuối,
    tự động phát hiện khi research đã xong để chuyển sang edit.
    
    Endpoint này thực hiện toàn bộ quy trình nghiên cứu từ đầu đến cuối một cách tự động. Điểm khác biệt chính so với endpoint `/api/v1/research` là:

    1. Tự động phát hiện khi nghiên cứu đã hoàn thành để chuyển sang giai đoạn chỉnh sửa
    2. Không cần gọi thêm endpoint `/api/v1/research/edit_only`
    3. Tất cả các bước được thực hiện trong một lần gọi API duy nhất
    4. Mỗi phần trong bài nghiên cứu sẽ có độ dài từ 350-400 từ
    5. Trong quá trình chỉnh sửa, nội dung gốc sẽ được giữ nguyên độ dài và chi tiết
    
    Args:
        request: Thông tin yêu cầu nghiên cứu
        background_tasks: Background tasks để xử lý nghiên cứu
        
    Returns:
        ResearchResponse: Thông tin về research task đã tạo
        
    Examples:
        ```json
        # Request
        {
          "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
          "topic": "Trí tuệ nhân tạo trong giáo dục",
          "scope": "Tổng quan và ứng dụng thực tế",
          "target_audience": "Giáo viên và nhà quản lý giáo dục"
        }
        
        # Response
        {
          "id": "ca214ee5-6204-4f3d-98c4-4f558e27399b",
          "status": "pending",
          "request": {
            "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
            "topic": "Trí tuệ nhân tạo trong giáo dục",
            "scope": "Tổng quan và ứng dụng thực tế",
            "target_audience": "Giáo viên và nhà quản lý giáo dục"
          },
          "outline": null,
          "result": null,
          "error": null,
          "github_url": null,
          "progress_info": {
            "phase": "pending",
            "message": "Đã nhận yêu cầu nghiên cứu, đang chuẩn bị xử lý",
            "timestamp": "2023-03-11T10:15:30.123456"
          },
          "created_at": "2023-03-11T10:15:30.123456",
          "updated_at": "2023-03-11T10:15:30.123456"
        }
        ```
        
        > **Lưu ý**: Khi chỉ cung cấp `query`, hệ thống sẽ tự động phân tích để xác định `topic`, `scope` và `target_audience`.
    """
    try:
        # Tạo ID mới cho research task
        task_id = str(uuid4())
        logger.info(f"Tạo research task mới với ID: {task_id}")
        
        # Tạo research task mới
        task = ResearchResponse(
            id=task_id,
            status=ResearchStatus.PENDING,
            request=request,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            progress_info={
                "phase": "pending",
                "message": "Đã nhận yêu cầu nghiên cứu, đang chuẩn bị xử lý",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Lưu task vào bộ nhớ và file
        research_tasks[task_id] = task
        await research_storage_service.save_task(task)
        
        # Chạy quá trình nghiên cứu hoàn chỉnh trong background
        background_tasks.add_task(process_complete_research, task_id, request)
        
        logger.info(f"Đã tạo research task với ID: {task_id}")
        logger.info(f"Thông tin yêu cầu: Query: '{request.query}', Topic: '{request.topic}', Scope: '{request.scope}', Target Audience: '{request.target_audience}'")
        
        return task
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo yêu cầu nghiên cứu: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def process_complete_research(task_id: str, request: ResearchRequest):
    """
    Xử lý yêu cầu nghiên cứu hoàn chỉnh trong background, tự động phát hiện khi research đã xong để chuyển sang edit
    
    Args:
        task_id: ID của research task
        request: Yêu cầu nghiên cứu
    """
    try:
        logger.info(f"=== BẮT ĐẦU XỬ LÝ RESEARCH TASK HOÀN CHỈNH {task_id} ===")
        logger.info(f"Thông tin yêu cầu: Query: '{request.query}', Topic: '{request.topic}', Scope: '{request.scope}', Target Audience: '{request.target_audience}'")
        
        # Khởi tạo các services
        prepare_service = PrepareService()
        research_service = ResearchService()
        edit_service = EditService()
        
        # Thiết lập callback để cập nhật tiến độ
        async def update_progress_callback(progress_info: Dict[str, Any]):
            if task_id in research_tasks:
                research_tasks[task_id].progress_info = progress_info
                research_tasks[task_id].updated_at = datetime.utcnow()
                await research_storage_service.save_task(research_tasks[task_id])
        
        # Gán callback cho research_service
        research_service.update_progress_callback = update_progress_callback
        
        # Gán task_id vào request để các service có thể sử dụng
        request.task_id = task_id
        
        # Phase 1: Chuẩn bị
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHUẨN BỊ ===")
        research_tasks[task_id].status = ResearchStatus.ANALYZING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "analyzing",
            "message": "Đang phân tích yêu cầu nghiên cứu",
            "timestamp": datetime.utcnow().isoformat()
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        analysis = await prepare_service.analyze_query(request.query, task_id)
        end_time = time.time()
        
        # Chuẩn hóa kết quả phân tích (kiểm tra cả viết hoa và viết thường)
        topic = analysis.get("Topic") or analysis.get("topic", request.query)
        scope = analysis.get("Scope") or analysis.get("scope", "Phân tích toàn diện")
        target_audience = analysis.get("Target Audience") or analysis.get("target_audience", "Người đọc quan tâm đến chủ đề")
        
        logger.info(f"[Task {task_id}] Phân tích yêu cầu hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Kết quả phân tích: Topic: '{topic}', Scope: '{scope}', Target Audience: '{target_audience}'")
        
        # Cập nhật request với thông tin phân tích đã chuẩn hóa
        request.topic = topic
        request.scope = scope
        request.target_audience = target_audience
        
        # Cập nhật task với request đã cập nhật
        research_tasks[task_id].request = request
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "analyzed",
            "message": "Đã phân tích xong yêu cầu nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": {
                "topic": topic,
                "scope": scope,
                "target_audience": target_audience
            }
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Tạo dàn ý
        logger.info(f"[Task {task_id}] === BẮT ĐẦU TẠO DÀN Ý ===")
        research_tasks[task_id].status = ResearchStatus.OUTLINING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "outlining",
            "message": "Đang tạo dàn ý cho bài nghiên cứu",
            "timestamp": datetime.utcnow().isoformat()
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        outline = await prepare_service.create_outline(request, task_id)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Tạo dàn ý hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Dàn ý có {len(outline.sections)} phần")
        
        # Lưu outline vào task
        research_tasks[task_id].outline = outline
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "outlined",
            "message": "Đã tạo xong dàn ý cho bài nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "outline_sections_count": len(outline.sections)
        }
        await research_storage_service.save_outline(task_id, outline)
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Phase 2: Nghiên cứu
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE NGHIÊN CỨU ===")
        research_tasks[task_id].status = ResearchStatus.RESEARCHING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "researching",
            "message": "Đang bắt đầu nghiên cứu các phần",
            "timestamp": datetime.utcnow().isoformat(),
            "current_section": 0,
            "total_sections": len(outline.sections),
            "completed_sections": 0
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        # Đảm bảo outline có task_id
        outline.task_id = task_id
        researched_sections = await research_service.execute(request, outline)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase nghiên cứu hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Đã nghiên cứu {len(researched_sections)}/{len(outline.sections)} phần")
        
        # Lưu researched_sections vào task
        research_tasks[task_id].sections = researched_sections
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "researched",
            "message": "Đã hoàn thành nghiên cứu tất cả các phần",
            "timestamp": datetime.utcnow().isoformat(),
            "total_sections": len(outline.sections),
            "completed_sections": len(researched_sections),
            "time_taken": f"{end_time - start_time:.2f} giây"
        }
        await research_storage_service.save_sections(task_id, researched_sections)
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Phase 3: Chỉnh sửa - Tự động chuyển sang phase chỉnh sửa
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHỈNH SỬA (TỰ ĐỘNG) ===")
        research_tasks[task_id].status = ResearchStatus.EDITING
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "editing",
            "message": "Đang tự động chuyển sang giai đoạn chỉnh sửa",
            "timestamp": datetime.utcnow().isoformat(),
            "sections_count": len(researched_sections),
            "outline_sections_count": len(outline.sections)
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        result = await edit_service.execute(request, outline, researched_sections)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase chỉnh sửa hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Kết quả: Tiêu đề: '{result.title}', Độ dài nội dung: {len(result.content)} ký tự, Số nguồn: {len(result.sources)}")
        
        # Lưu kết quả vào file
        await research_storage_service.save_result(task_id, result)
        
        # Lưu kết quả lên GitHub
        logger.info(f"[Task {task_id}] === BẮT ĐẦU LƯU KẾT QUẢ LÊN GITHUB ===")
        
        # Tạo nội dung Markdown
        markdown_content = f"# {result.title}\n\n{result.content}\n\n## Nguồn tham khảo\n\n"
        for idx, source in enumerate(result.sources):
            markdown_content += f"{idx+1}. [{source}]({source})\n"
        
        logger.info(f"[Task {task_id}] Đã tạo nội dung Markdown với {len(markdown_content)} ký tự")
        
        # Lưu lên GitHub
        try:
            github_service = get_service_factory().create_storage_service("github")
            file_path = f"researches/{task_id}/result.md"
            logger.info(f"[Task {task_id}] Đường dẫn file: {file_path}")
            
            start_time = time.time()
            github_url = await github_service.save(markdown_content, file_path)
            end_time = time.time()
            
            logger.info(f"[Task {task_id}] Đã lưu kết quả lên GitHub trong {end_time - start_time:.2f} giây")
            logger.info(f"[Task {task_id}] URL GitHub: {github_url}")
            
            # Cập nhật URL GitHub vào task
            research_tasks[task_id].github_url = github_url
        except Exception as e:
            logger.error(f"[Task {task_id}] Lỗi khi lưu kết quả lên GitHub: {str(e)}")
        
        # Cập nhật trạng thái task
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].result = result
        research_tasks[task_id].updated_at = datetime.utcnow()
        research_tasks[task_id].progress_info = {
            "phase": "completed",
            "message": "Đã hoàn thành toàn bộ quá trình nghiên cứu",
            "timestamp": datetime.utcnow().isoformat(),
            "content_length": len(result.content),
            "sources_count": len(result.sources),
            "total_time": f"{(datetime.utcnow() - research_tasks[task_id].created_at).total_seconds():.2f} giây"
        }
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"[Task {task_id}] === HOÀN THÀNH RESEARCH TASK HOÀN CHỈNH ===")
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Lỗi khi xử lý research task hoàn chỉnh: {str(e)}")
        
        # Cập nhật trạng thái task thành failed
        if task_id in research_tasks:
            research_tasks[task_id].status = ResearchStatus.FAILED
            research_tasks[task_id].error = ResearchError(
                message="Lỗi trong quá trình xử lý research task hoàn chỉnh",
                details={"error": str(e)}
            )
            research_tasks[task_id].updated_at = datetime.utcnow()
            research_tasks[task_id].progress_info = {
                "phase": "failed",
                "message": f"Lỗi trong quá trình xử lý: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            await research_storage_service.save_task(research_tasks[task_id])

@router.get("/research/{research_id}/cost", response_model=ResearchCostMonitoring)
async def get_research_cost(research_id: str):
    """Lấy thông tin chi phí của một research task"""
    try:
        # Kiểm tra task tồn tại
        if research_id not in research_tasks:
            raise HTTPException(status_code=404, detail=f"Research task {research_id} not found")
        
        # Tạo cost monitoring service
        service_factory = get_service_factory()
        cost_service = service_factory.get_cost_monitoring_service()
        
        # Lấy thông tin chi phí chi tiết
        try:
            monitoring = await cost_service.get_monitoring(research_id)
            if not monitoring:
                monitoring = cost_service.initialize_monitoring(research_id)
            
            # Cập nhật summary nếu cần
            if not monitoring.summary:
                monitoring._update_summary()
                
            return monitoring
            
        except Exception as cost_error:
            logger.error(f"Lỗi khi lấy thông tin chi phí: {str(cost_error)}")
            raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông tin chi phí: {str(cost_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving cost information: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cost information: {str(e)}") 