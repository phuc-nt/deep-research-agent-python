import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from app.core.factory import service_factory
from app.core.logging import logger
from app.models.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchOutline,
    ResearchSection,
    ResearchResult,
    ResearchStatus
)

class ResearchStorageService:
    """Service quản lý lưu trữ và truy xuất dữ liệu nghiên cứu"""
    
    def __init__(self, storage_provider: str = "file"):
        """
        Khởi tạo service với provider lưu trữ
        
        Args:
            storage_provider: Provider lưu trữ ("file" hoặc "github")
        """
        self.storage_service = service_factory.create_storage_service(storage_provider)
        self.tasks_dir = "research_tasks"
        logger.info(f"Khởi tạo ResearchStorageService với provider: {storage_provider}")
    
    async def save_task(self, task: ResearchResponse) -> str:
        """
        Lưu thông tin task vào file
        
        Args:
            task: Task cần lưu
            
        Returns:
            str: Đường dẫn đến file đã lưu
        """
        try:
            # Chuyển đổi task thành dict
            task_dict = task.dict()
            
            # Chuyển đổi datetime thành string
            task_dict["created_at"] = task_dict["created_at"].isoformat() if task_dict.get("created_at") else None
            task_dict["updated_at"] = task_dict["updated_at"].isoformat() if task_dict.get("updated_at") else None
            
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task.id}/task.json"
            
            # Lưu vào file
            path = await self.storage_service.save(task_dict, file_path)
            logger.info(f"Đã lưu task {task.id} vào file: {path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu task {task.id}: {str(e)}")
            raise
    
    async def load_task(self, task_id: str) -> Optional[ResearchResponse]:
        """
        Đọc thông tin task từ file
        
        Args:
            task_id: ID của task cần đọc
            
        Returns:
            Optional[ResearchResponse]: Task đã đọc hoặc None nếu không tìm thấy
        """
        try:
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/task.json"
            
            # Đọc từ file
            try:
                task_dict = await self.storage_service.load(file_path)
            except FileNotFoundError:
                logger.warning(f"Không tìm thấy file task {task_id}")
                return None
            
            # Chuyển đổi string thành datetime
            if task_dict.get("created_at"):
                task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
            if task_dict.get("updated_at"):
                task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
            
            # Tạo đối tượng ResearchResponse
            task = ResearchResponse(**task_dict)
            logger.info(f"Đã đọc task {task_id} từ file")
            
            return task
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc task {task_id}: {str(e)}")
            raise
    
    async def list_tasks(self) -> List[str]:
        """
        Liệt kê danh sách các task đã lưu
        
        Returns:
            List[str]: Danh sách ID của các task
        """
        try:
            # Lấy đường dẫn đầy đủ đến thư mục tasks_dir
            base_dir = self.storage_service.base_dir
            full_tasks_dir = os.path.join(base_dir, self.tasks_dir)
            
            # Kiểm tra thư mục tồn tại
            if not os.path.exists(full_tasks_dir):
                logger.warning(f"Thư mục không tồn tại: {full_tasks_dir}")
                return []
            
            # Liệt kê các thư mục trong tasks_dir
            task_ids = []
            for item in os.listdir(full_tasks_dir):
                item_path = os.path.join(full_tasks_dir, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "task.json")):
                    task_ids.append(item)
            
            logger.info(f"Đã liệt kê {len(task_ids)} tasks")
            return task_ids
            
        except Exception as e:
            logger.error(f"Lỗi khi liệt kê tasks: {str(e)}")
            raise
    
    async def save_outline(self, task_id: str, outline: ResearchOutline) -> str:
        """
        Lưu outline vào file
        
        Args:
            task_id: ID của task
            outline: Outline cần lưu
            
        Returns:
            str: Đường dẫn đến file đã lưu
        """
        try:
            # Chuyển đổi outline thành dict
            outline_dict = outline.dict()
            
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/outline.json"
            
            # Lưu vào file
            path = await self.storage_service.save(outline_dict, file_path)
            logger.info(f"Đã lưu outline của task {task_id} vào file: {path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu outline của task {task_id}: {str(e)}")
            raise
    
    async def load_outline(self, task_id: str) -> Optional[ResearchOutline]:
        """
        Đọc outline từ file
        
        Args:
            task_id: ID của task
            
        Returns:
            Optional[ResearchOutline]: Outline đã đọc hoặc None nếu không tìm thấy
        """
        try:
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/outline.json"
            
            # Đọc từ file
            try:
                outline_dict = await self.storage_service.load(file_path)
            except FileNotFoundError:
                logger.warning(f"Không tìm thấy file outline của task {task_id}")
                return None
            
            # Tạo đối tượng ResearchOutline
            outline = ResearchOutline(**outline_dict)
            logger.info(f"Đã đọc outline của task {task_id} từ file")
            
            return outline
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc outline của task {task_id}: {str(e)}")
            raise
    
    async def save_sections(self, task_id: str, sections: List[ResearchSection]) -> str:
        """
        Lưu danh sách sections vào file
        
        Args:
            task_id: ID của task
            sections: Danh sách sections cần lưu
            
        Returns:
            str: Đường dẫn đến file đã lưu
        """
        try:
            # Chuyển đổi sections thành list dict
            sections_dict = [section.dict() for section in sections]
            
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/sections.json"
            
            # Lưu vào file
            path = await self.storage_service.save(sections_dict, file_path)
            logger.info(f"Đã lưu {len(sections)} sections của task {task_id} vào file: {path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu sections của task {task_id}: {str(e)}")
            raise
    
    async def load_sections(self, task_id: str) -> Optional[List[ResearchSection]]:
        """
        Đọc danh sách sections từ file
        
        Args:
            task_id: ID của task
            
        Returns:
            Optional[List[ResearchSection]]: Danh sách sections đã đọc hoặc None nếu không tìm thấy
        """
        try:
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/sections.json"
            
            # Đọc từ file
            try:
                sections_dict = await self.storage_service.load(file_path)
            except FileNotFoundError:
                logger.warning(f"Không tìm thấy file sections của task {task_id}")
                return None
            
            # Tạo danh sách đối tượng ResearchSection
            sections = [ResearchSection(**section_dict) for section_dict in sections_dict]
            logger.info(f"Đã đọc {len(sections)} sections của task {task_id} từ file")
            
            return sections
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc sections của task {task_id}: {str(e)}")
            raise
    
    async def save_result(self, task_id: str, result: ResearchResult) -> str:
        """
        Lưu kết quả nghiên cứu vào file
        
        Args:
            task_id: ID của task
            result: Kết quả cần lưu
            
        Returns:
            str: Đường dẫn đến file đã lưu
        """
        try:
            # Chuyển đổi result thành dict
            result_dict = result.dict()
            
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/result.json"
            
            # Lưu vào file
            path = await self.storage_service.save(result_dict, file_path)
            logger.info(f"Đã lưu kết quả của task {task_id} vào file: {path}")
            
            # Lưu cả nội dung dưới dạng markdown
            markdown_content = f"""# {result.title}

{result.content}

## Nguồn tham khảo

"""
            for idx, source in enumerate(result.sources):
                markdown_content += f"{idx+1}. [{source}]({source})\n"
                
            markdown_path = f"{self.tasks_dir}/{task_id}/result.md"
            await self.storage_service.save(markdown_content, markdown_path)
            logger.info(f"Đã lưu kết quả dạng markdown của task {task_id} vào file: {markdown_path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu kết quả của task {task_id}: {str(e)}")
            raise
    
    async def load_result(self, task_id: str) -> Optional[ResearchResult]:
        """
        Đọc kết quả nghiên cứu từ file
        
        Args:
            task_id: ID của task
            
        Returns:
            Optional[ResearchResult]: Kết quả đã đọc hoặc None nếu không tìm thấy
        """
        try:
            # Tạo đường dẫn file
            file_path = f"{self.tasks_dir}/{task_id}/result.json"
            
            # Đọc từ file
            try:
                result_dict = await self.storage_service.load(file_path)
            except FileNotFoundError:
                logger.warning(f"Không tìm thấy file kết quả của task {task_id}")
                return None
            
            # Tạo đối tượng ResearchResult
            result = ResearchResult(**result_dict)
            logger.info(f"Đã đọc kết quả của task {task_id} từ file")
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc kết quả của task {task_id}: {str(e)}")
            raise 