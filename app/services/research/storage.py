import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from app.core.factory import get_service_factory
from app.core.logging import get_logger
from app.models.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchOutline,
    ResearchSection,
    ResearchResult,
    ResearchStatus,
    ResearchCostInfo
)

logger = get_logger(__name__)

class ResearchStorageService:
    """Service quản lý lưu trữ và truy xuất dữ liệu nghiên cứu"""
    
    def __init__(self, storage_provider: str = "file"):
        """
        Khởi tạo service với provider lưu trữ
        
        Args:
            storage_provider: Provider lưu trữ ("file" hoặc "github")
        """
        service_factory = get_service_factory()
        self.storage_service = service_factory.get_storage_service(storage_provider)
        self.tasks_dir = "research_tasks"
        self.base_dir = self.storage_service.base_dir
        logger.info(f"Khởi tạo ResearchStorageService với provider: {storage_provider}")
    
    def _get_task_path(self, task_id: str, filename: str) -> str:
        """
        Tạo đường dẫn đầy đủ đến file của task
        
        Args:
            task_id: ID của task
            filename: Tên file
            
        Returns:
            str: Đường dẫn đầy đủ đến file
        """
        return os.path.join(self.tasks_dir, task_id, filename)
    
    def _get_full_path(self, relative_path: str) -> str:
        """
        Tạo đường dẫn đầy đủ đến file
        
        Args:
            relative_path: Đường dẫn tương đối
            
        Returns:
            str: Đường dẫn đầy đủ
        """
        # Với `file` storage, đã có đường dẫn đầy đủ
        if hasattr(self.storage_service, 'base_dir'):
            # Đảm bảo path là đối tượng Path
            path = Path(relative_path)
            if path.is_absolute():
                return str(path)
            return str(Path(self.base_dir) / path)
        return relative_path
    
    def _json_serializer(self, obj):
        """Hàm hỗ trợ serialize các object đặc biệt sang JSON"""
        from datetime import datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            return obj.dict()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    async def save_task(self, task: ResearchResponse) -> None:
        """Lưu thông tin task vào file"""
        try:
            task_path = self._get_task_path(task.id, "task.json")
            full_path = self._get_full_path(task_path)
            
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Chuyển sang dict để serialize
            task_dict = task.dict()
            
            # Lưu vào file
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(task_dict, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            logger.info(f"Đã lưu dữ liệu vào file: {full_path}")
            logger.info(f"Đã lưu thông tin cơ bản của task {task.id} vào file: {full_path}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu thông tin task {task.id}: {str(e)}")
            raise

    async def update_cost_info(self, task_id: str, cost_info: ResearchCostInfo) -> None:
        """
        Cập nhật thông tin chi phí cho một task và lưu lên GitHub
        
        Args:
            task_id: ID của task
            cost_info: Thông tin chi phí cần cập nhật
        """
        try:
            # Lấy thông tin cơ bản hiện có
            task_info = self.get_basic_task_info(task_id)
            if not task_info:
                logger.warning(f"Không tìm thấy task {task_id} để cập nhật cost_info")
                return
            
            # Cập nhật cost_info
            if hasattr(cost_info, 'dict'):
                # Nếu cost_info là đối tượng Pydantic
                task_info["cost_info"] = cost_info.dict()
            else:
                # Nếu cost_info đã là dict
                task_info["cost_info"] = cost_info
            
            # Lưu vào file local
            task_path = self._get_task_path(task_id, "task.json")
            full_path = self._get_full_path(task_path)
            
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(task_info, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            logger.info(f"Đã cập nhật cost_info cho task {task_id} vào file local")
            
            # Lưu cost.json riêng lên GitHub
            try:
                # Tạo nội dung chi tiết cho cost.json
                cost_detail = {
                    "task_id": task_id,
                    "updated_at": datetime.utcnow().isoformat(),
                    "cost_info": cost_info.dict() if hasattr(cost_info, 'dict') else cost_info,
                    "task_info": {
                        "query": task_info.get("request", {}).get("query", ""),
                        "topic": task_info.get("request", {}).get("topic", ""),
                        "status": task_info.get("status", ""),
                        "created_at": task_info.get("created_at", ""),
                    }
                }
                
                # Chuyển sang JSON string
                cost_json = json.dumps(cost_detail, ensure_ascii=False, indent=2, default=self._json_serializer)
                
                # Lưu lên GitHub
                github_service = get_service_factory().get_storage_service("github")
                file_path = f"researches/{task_id}/cost.json"
                github_url = await github_service.save(cost_json, file_path)
                
                # Cập nhật URL vào cost_info
                if hasattr(cost_info, 'cost_report_url'):
                    cost_info.cost_report_url = github_url
                    # Cập nhật lại file local với URL mới
                    task_info["cost_info"]["cost_report_url"] = github_url
                    with open(full_path, "w", encoding="utf-8") as f:
                        json.dump(task_info, f, ensure_ascii=False, indent=2, default=self._json_serializer)
                
                logger.info(f"Đã lưu cost.json lên GitHub: {github_url}")
                
            except Exception as e:
                logger.error(f"Lỗi khi lưu cost.json lên GitHub cho task {task_id}: {str(e)}")
                # Không raise exception để không ảnh hưởng đến luồng chính
            
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật cost_info cho task {task_id}: {str(e)}")
            raise

    async def update_task_with_cost_info(self, task: ResearchResponse, cost_info: ResearchCostInfo) -> ResearchResponse:
        """Cập nhật task với thông tin chi phí và lưu vào file"""
        try:
            # Cập nhật cost_info trong task
            task.cost_info = cost_info
            task.updated_at = datetime.now()
            
            # Lưu task
            await self.save_task(task)
            
            logger.info(f"Đã cập nhật task {task.id} với cost_info")
            return task
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật task {task.id} với cost_info: {str(e)}")
            return task
    
    async def load_task(self, task_id: str) -> Optional[ResearchResponse]:
        """
        Đọc thông tin cơ bản của task từ file
        
        Args:
            task_id: ID của task cần đọc
            
        Returns:
            Optional[ResearchResponse]: Task đã đọc hoặc None nếu không tìm thấy
        """
        try:
            # Tạo đường dẫn file
            file_path = self._get_task_path(task_id, "task.json")
            
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
            logger.info(f"Đã đọc thông tin cơ bản của task {task_id} từ file")
            
            return task
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc task {task_id}: {str(e)}")
            raise
    
    async def load_full_task(self, task_id: str) -> Optional[ResearchResponse]:
        """
        Đọc toàn bộ thông tin của task từ file, bao gồm outline, sections và result
        
        Args:
            task_id: ID của task cần đọc
            
        Returns:
            Optional[ResearchResponse]: Task đầy đủ đã đọc hoặc None nếu không tìm thấy
        """
        try:
            # Đọc thông tin cơ bản của task
            task = await self.load_task(task_id)
            if not task:
                return None
            
            # Đọc outline
            outline = await self.load_outline(task_id)
            if outline:
                task.outline = outline
            
            # Đọc sections
            sections = await self.load_sections(task_id)
            if sections:
                task.sections = sections
            
            # Đọc result
            result = await self.load_result(task_id)
            if result:
                task.result = result
            
            logger.info(f"Đã đọc toàn bộ thông tin của task {task_id} từ file")
            return task
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc toàn bộ thông tin task {task_id}: {str(e)}")
            raise
    
    async def list_tasks(self) -> List[str]:
        """
        Liệt kê danh sách các task đã lưu
        
        Returns:
            List[str]: Danh sách ID của các task
        """
        try:
            # Lấy đường dẫn đầy đủ đến thư mục tasks_dir
            full_tasks_dir = self._get_full_path(self.tasks_dir)
            
            # Kiểm tra thư mục tồn tại
            if not os.path.exists(full_tasks_dir):
                logger.warning(f"Thư mục không tồn tại: {full_tasks_dir}")
                return []
            
            # Liệt kê các thư mục trong tasks_dir
            task_ids = []
            for item in os.listdir(full_tasks_dir):
                task_dir = os.path.join(full_tasks_dir, item)
                task_file = os.path.join(task_dir, "task.json")
                if os.path.isdir(task_dir) and os.path.exists(task_file):
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
            file_path = self._get_task_path(task_id, "outline.json")
            
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
            file_path = self._get_task_path(task_id, "outline.json")
            
            # Kiểm tra file tồn tại
            full_path = self._get_full_path(file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Không tìm thấy file outline của task {task_id}")
                return None
            
            # Đọc từ file
            outline_dict = await self.storage_service.load(file_path)
            
            # Tạo đối tượng ResearchOutline
            outline = ResearchOutline(**outline_dict)
            logger.info(f"Đã đọc outline của task {task_id} từ file")
            
            return outline
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc outline của task {task_id}: {str(e)}")
            return None
    
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
            file_path = self._get_task_path(task_id, "sections.json")
            
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
            file_path = self._get_task_path(task_id, "sections.json")
            
            # Kiểm tra file tồn tại
            full_path = self._get_full_path(file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Không tìm thấy file sections của task {task_id}")
                return None
            
            # Đọc từ file
            sections_dict = await self.storage_service.load(file_path)
            
            # Tạo danh sách đối tượng ResearchSection
            sections = [ResearchSection(**section_dict) for section_dict in sections_dict]
            logger.info(f"Đã đọc {len(sections)} sections của task {task_id} từ file")
            
            return sections
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc sections của task {task_id}: {str(e)}")
            return None
    
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
            file_path = self._get_task_path(task_id, "result.json")
            
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
                
            markdown_path = self._get_task_path(task_id, "result.md")
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
            file_path = self._get_task_path(task_id, "result.json")
            
            # Kiểm tra file tồn tại
            full_path = self._get_full_path(file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Không tìm thấy file kết quả của task {task_id}")
                return None
            
            # Đọc từ file
            result_dict = await self.storage_service.load(file_path)
            
            # Tạo đối tượng ResearchResult
            result = ResearchResult(**result_dict)
            logger.info(f"Đã đọc kết quả của task {task_id} từ file")
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc kết quả của task {task_id}: {str(e)}")
            return None
    
    def get_basic_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin cơ bản của task từ file
        
        Args:
            task_id: ID của task cần đọc
            
        Returns:
            Optional[Dict[str, Any]]: Thông tin cơ bản của task hoặc None nếu không tìm thấy
        """
        try:
            file_path = self._get_task_path(task_id, "task.json")
            full_path = self._get_full_path(file_path)
            
            # Kiểm tra file tồn tại
            if not os.path.exists(full_path):
                logger.warning(f"Không tìm thấy file task {task_id}")
                return None
            
            # Đọc file
            with open(full_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
            
            logger.info(f"Đã đọc thông tin cơ bản của task {task_id} từ file")
            return task_data
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc thông tin cơ bản của task {task_id}: {str(e)}")
            return None 