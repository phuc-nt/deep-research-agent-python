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
    ResearchError
)
from app.services.research.prepare import PrepareService
from app.services.research.research import ResearchService
from app.services.research.edit import EditService
from app.services.research.storage import ResearchStorageService
from app.services.core.storage.github import GitHubService
from app.core.exceptions import BaseError
from app.core.config import get_settings
from app.core.factory import service_factory
from app.core.logging import logger

router = APIRouter()

# Lưu trữ tạm thời các research tasks (trong thực tế nên dùng database)
research_tasks: Dict[str, ResearchResponse] = {}

# Khởi tạo ResearchStorageService
research_storage_service = ResearchStorageService()

# Tải lại các tasks đã lưu khi khởi động server
@router.on_event("startup")
async def load_saved_tasks():
    """Tải lại các tasks đã lưu khi khởi động server"""
    try:
        logger.info("Đang tải lại các research tasks đã lưu...")
        task_ids = await research_storage_service.list_tasks()
        
        for task_id in task_ids:
            task = await research_storage_service.load_task(task_id)
            if task:
                research_tasks[task_id] = task
                logger.info(f"Đã tải lại task {task_id}, trạng thái: {task.status}")
        
        logger.info(f"Đã tải lại {len(task_ids)} research tasks")
    except Exception as e:
        logger.error(f"Lỗi khi tải lại research tasks: {str(e)}")

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
        edit_service = EditService()
        storage_service = service_factory.create_storage_service()
        
        # Phase 1: Chuẩn bị
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHUẨN BỊ ===")
        research_tasks[task_id].status = ResearchStatus.OUTLINING
        research_tasks[task_id].updated_at = datetime.utcnow()
        
        # Lưu trạng thái task
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        outline = await prepare_service.execute(request)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase chuẩn bị hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Dàn ý có {len(outline.sections)} phần")
        for i, section in enumerate(outline.sections):
            logger.info(f"[Task {task_id}] Phần {i+1}: {section.title} - {section.description}")
        
        # Lưu outline vào task
        research_tasks[task_id].outline = outline
        await research_storage_service.save_outline(task_id, outline)
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Phase 2: Nghiên cứu
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE NGHIÊN CỨU ===")
        research_tasks[task_id].status = ResearchStatus.RESEARCHING
        research_tasks[task_id].updated_at = datetime.utcnow()
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        researched_sections = await research_service.execute(request, outline)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase nghiên cứu hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Đã nghiên cứu {len(researched_sections)}/{len(outline.sections)} phần")
        
        # Lưu researched_sections vào task
        research_tasks[task_id].sections = researched_sections
        await research_storage_service.save_sections(task_id, researched_sections)
        await research_storage_service.save_task(research_tasks[task_id])
        
        # Phase 3: Chỉnh sửa
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHỈNH SỬA ===")
        research_tasks[task_id].status = ResearchStatus.EDITING
        research_tasks[task_id].updated_at = datetime.utcnow()
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        result = await edit_service.execute(request, outline, researched_sections)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase chỉnh sửa hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Kết quả: Tiêu đề: '{result.title}', Độ dài nội dung: {len(result.content)} ký tự, Số nguồn: {len(result.sources)}")
        
        # Lưu kết quả vào file
        await research_storage_service.save_result(task_id, result)
        
        # Lưu kết quả lên GitHub
        try:
            logger.info(f"[Task {task_id}] === BẮT ĐẦU LƯU KẾT QUẢ LÊN GITHUB ===")
            
            # Tạo nội dung file Markdown
            markdown_content = f"""# {result.title}

{result.content}

## Nguồn tham khảo

"""
            for idx, source in enumerate(result.sources):
                markdown_content += f"{idx+1}. [{source}]({source})\n"
            
            logger.info(f"[Task {task_id}] Đã tạo nội dung Markdown với {len(markdown_content)} ký tự")
            
            # Tạo đường dẫn file
            file_path = f"researches/{task_id}/result.md"
            logger.info(f"[Task {task_id}] Đường dẫn file: {file_path}")
            
            # Lưu lên GitHub
            start_time = time.time()
            github_url = await storage_service.save(markdown_content, file_path)
            end_time = time.time()
            
            # Cập nhật thông tin GitHub URL
            research_tasks[task_id].github_url = github_url
            logger.info(f"[Task {task_id}] Đã lưu kết quả lên GitHub trong {end_time - start_time:.2f} giây")
            logger.info(f"[Task {task_id}] URL GitHub: {github_url}")
            
        except Exception as e:
            # Ghi log lỗi nhưng không dừng quá trình
            logger.error(f"[Task {task_id}] === LỖI KHI LƯU LÊN GITHUB ===")
            logger.error(f"[Task {task_id}] Chi tiết lỗi: {str(e)}")
        
        # Cập nhật kết quả và trạng thái
        research_tasks[task_id].result = result
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].updated_at = datetime.utcnow()
        await research_storage_service.save_task(research_tasks[task_id])
        logger.info(f"[Task {task_id}] === HOÀN THÀNH RESEARCH TASK ===")
        
    except Exception as e:
        logger.error(f"[Task {task_id}] === LỖI TRONG QUÁ TRÌNH XỬ LÝ RESEARCH TASK ===")
        logger.error(f"[Task {task_id}] Lỗi từ service: {str(e)}")
        
        # Cập nhật trạng thái lỗi
        research_tasks[task_id].status = ResearchStatus.FAILED
        research_tasks[task_id].error = {
            "message": "Lỗi trong quá trình nghiên cứu",
            "details": {"error": str(e)}
        }
        research_tasks[task_id].updated_at = datetime.utcnow()
        await research_storage_service.save_task(research_tasks[task_id])

@router.post("/research", response_model=ResearchResponse)
async def create_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
) -> ResearchResponse:
    """
    Tạo một yêu cầu nghiên cứu mới
    """
    try:
        logger.info(f"Nhận yêu cầu nghiên cứu mới: {request.topic or request.query}")
        
        # Tạo ID cho research task
        task_id = str(uuid4())
        
        # Tạo research task
        research_tasks[task_id] = ResearchResponse(
            id=task_id,
            request=request,
            status=ResearchStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Lưu task vào file
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"Đã tạo research task {task_id}")
        
        # Chạy quá trình nghiên cứu trong background
        asyncio.create_task(process_research(task_id, request))
        
        return research_tasks[task_id]
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo research task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo research task: {str(e)}"
        )

@router.get("/research/{task_id}", response_model=ResearchResponse)
async def get_research(task_id: str) -> ResearchResponse:
    """
    Lấy thông tin về một research task
    """
    try:
        logger.info(f"Lấy thông tin research task {task_id}")
        
        # Kiểm tra trong bộ nhớ
        if task_id not in research_tasks:
            # Thử tải từ file
            logger.info(f"Task {task_id} không có trong bộ nhớ, thử tải từ file...")
            task = await research_storage_service.load_task(task_id)
            
            if task:
                # Cập nhật vào bộ nhớ
                research_tasks[task_id] = task
                logger.info(f"Đã tải task {task_id} từ file, trạng thái: {task.status}")
            else:
                logger.error(f"Không tìm thấy research task {task_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Research task {task_id} not found"
                )
            
        return research_tasks[task_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin research task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

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

@router.get("/research", response_model=List[ResearchResponse])
async def list_research() -> List[ResearchResponse]:
    """
    Liệt kê tất cả các research tasks
    
    Returns:
        List[ResearchResponse]: Danh sách các research tasks
    """
    try:
        logger.info("Liệt kê tất cả research tasks")
        
        # Tải tất cả tasks từ file nếu chưa có trong bộ nhớ
        task_ids = await research_storage_service.list_tasks()
        
        for task_id in task_ids:
            if task_id not in research_tasks:
                task = await research_storage_service.load_task(task_id)
                if task:
                    research_tasks[task_id] = task
        
        # Trả về danh sách tasks
        tasks = list(research_tasks.values())
        logger.info(f"Đã liệt kê {len(tasks)} research tasks")
        
        return tasks
        
    except Exception as e:
        logger.error(f"Lỗi khi liệt kê research tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/research/edit_only", response_model=ResearchResponse)
async def continue_with_editing() -> ResearchResponse:
    """
    Tiếp tục xử lý giai đoạn chỉnh sửa cho task mới nhất, sử dụng dữ liệu có sẵn
    
    Returns:
        ResearchResponse: Thông tin về research task đã cập nhật
    """
    try:
        # Tìm task mới nhất
        task_ids = await research_storage_service.list_tasks()
        
        if not task_ids:
            # Nếu không có task nào, báo lỗi
            logger.error("Không tìm thấy task nào để tiếp tục xử lý")
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy task nào để tiếp tục xử lý"
            )
        
        # Sắp xếp task theo thời gian tạo (nếu có thông tin)
        tasks = []
        for tid in task_ids:
            task = await research_storage_service.load_task(tid)
            if task:
                tasks.append(task)
        
        if not tasks:
            # Nếu không load được task nào, báo lỗi
            logger.error("Không load được task nào để tiếp tục xử lý")
            raise HTTPException(
                status_code=404,
                detail="Không load được task nào để tiếp tục xử lý"
            )
        
        # Sắp xếp theo thời gian tạo, lấy task mới nhất
        tasks.sort(key=lambda x: x.created_at if x.created_at else datetime.min, reverse=True)
        task_id = tasks[0].id
        task = tasks[0]
        
        logger.info(f"Tìm thấy task mới nhất với ID: {task_id}")
        
        # Kiểm tra xem task có đủ dữ liệu để tiếp tục không
        if not task.request:
            logger.error(f"Task {task_id} không có thông tin request")
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} không có thông tin request"
            )
        
        # Tải outline và sections từ file
        outline = await research_storage_service.load_outline(task_id)
        if not outline:
            logger.error(f"Task {task_id} không có outline")
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} không có outline"
            )
        
        sections = await research_storage_service.load_sections(task_id)
        if not sections:
            logger.error(f"Task {task_id} không có sections")
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} không có sections"
            )
        
        # Cập nhật trạng thái task
        task.status = ResearchStatus.EDITING
        task.updated_at = datetime.utcnow()
        
        # Lưu task vào bộ nhớ và file
        research_tasks[task_id] = task
        await research_storage_service.save_task(task)
        
        logger.info(f"Đã cập nhật task {task_id} để tiếp tục xử lý giai đoạn chỉnh sửa")
        logger.info(f"Thông tin yêu cầu: Query: '{task.request.query}', Topic: '{task.request.topic}', Scope: '{task.request.scope}', Target Audience: '{task.request.target_audience}'")
        logger.info(f"Số phần đã nghiên cứu: {len(sections)}")
        
        # Chạy quá trình chỉnh sửa trong background
        asyncio.create_task(process_research_with_sections(task_id, task.request, outline, sections))
        
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
        storage_service = service_factory.create_storage_service()
        
        # Phase 3: Chỉnh sửa
        logger.info(f"[Task {task_id}] === BẮT ĐẦU PHASE CHỈNH SỬA ===")
        research_tasks[task_id].status = ResearchStatus.EDITING
        research_tasks[task_id].updated_at = datetime.utcnow()
        await research_storage_service.save_task(research_tasks[task_id])
        
        start_time = time.time()
        result = await edit_service.execute(request, outline, sections)
        end_time = time.time()
        
        logger.info(f"[Task {task_id}] Phase chỉnh sửa hoàn thành trong {end_time - start_time:.2f} giây")
        logger.info(f"[Task {task_id}] Kết quả: Tiêu đề: '{result.title}', Độ dài nội dung: {len(result.content)} ký tự, Số nguồn: {len(result.sources)}")
        
        # Lưu kết quả vào file
        await research_storage_service.save_result(task_id, result)
        
        # Lưu kết quả lên GitHub
        try:
            logger.info(f"[Task {task_id}] === BẮT ĐẦU LƯU KẾT QUẢ LÊN GITHUB ===")
            
            # Tạo nội dung file Markdown
            markdown_content = f"""# {result.title}

{result.content}

## Nguồn tham khảo

"""
            for idx, source in enumerate(result.sources):
                markdown_content += f"{idx+1}. [{source}]({source})\n"
            
            logger.info(f"[Task {task_id}] Đã tạo nội dung Markdown với {len(markdown_content)} ký tự")
            
            # Lưu lên GitHub
            github_service = GitHubService()
            github_url = await github_service.save_research(
                title=result.title,
                content=markdown_content,
                topic=request.topic or request.query
            )
            
            # Cập nhật URL GitHub vào task
            research_tasks[task_id].github_url = github_url
            await research_storage_service.save_task(research_tasks[task_id])
            
            logger.info(f"[Task {task_id}] Đã lưu kết quả lên GitHub: {github_url}")
            
        except Exception as e:
            logger.error(f"[Task {task_id}] Lỗi khi lưu kết quả lên GitHub: {str(e)}")
            # Không dừng quá trình nếu lỗi GitHub
        
        # Cập nhật trạng thái task
        research_tasks[task_id].status = ResearchStatus.COMPLETED
        research_tasks[task_id].result = result
        research_tasks[task_id].updated_at = datetime.utcnow()
        await research_storage_service.save_task(research_tasks[task_id])
        
        logger.info(f"=== KẾT THÚC XỬ LÝ RESEARCH TASK {task_id} - THÀNH CÔNG ===")
        
    except Exception as e:
        logger.error(f"=== KẾT THÚC XỬ LÝ RESEARCH TASK {task_id} - THẤT BẠI ===")
        logger.error(f"Lỗi trong quá trình xử lý research task {task_id}: {str(e)}")
        
        # Cập nhật trạng thái task
        if task_id in research_tasks:
            research_tasks[task_id].status = ResearchStatus.FAILED
            research_tasks[task_id].error = ResearchError(
                message=f"Lỗi trong quá trình xử lý research task",
                details={"error": str(e)}
            )
            research_tasks[task_id].updated_at = datetime.utcnow()
            await research_storage_service.save_task(research_tasks[task_id]) 