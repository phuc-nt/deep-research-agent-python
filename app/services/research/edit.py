import json
from typing import Any, Dict, List

from app.core.config import get_edit_prompts, get_settings, EditPrompts
from app.core.exceptions import EditError
from app.core.factory import get_service_factory
from app.services.research.base import (
    BaseEditPhase,
    ResearchSection,
    ResearchResult,
    ResearchRequest,
    ResearchOutline
)
import logging

logger = logging.getLogger(__name__)

class EditService(BaseEditPhase):
    """Service thực hiện phase chỉnh sửa trong quy trình nghiên cứu"""
    
    def __init__(self):
        """Khởi tạo service với các prompts và LLM service"""
        self.settings = get_settings()
        self.prompts = EditPrompts()
        service_factory = get_service_factory()
        self.llm_service = service_factory.create_llm_service_for_phase("edit")
        # Khởi tạo cost monitoring service
        self.cost_service = service_factory.get_cost_monitoring_service()
    
    async def execute(
        self, 
        request: ResearchRequest,
        outline: ResearchOutline,
        sections: List[ResearchSection]
    ) -> ResearchResult:
        """
        Thực thi phase chỉnh sửa
        
        Args:
            request: Yêu cầu nghiên cứu
            outline: Dàn ý nghiên cứu
            sections: Danh sách các phần đã nghiên cứu
            
        Returns:
            ResearchResult: Kết quả nghiên cứu hoàn chỉnh
            
        Raises:
            EditError: Nếu có lỗi trong quá trình chỉnh sửa
        """
        try:
            logger.info(f"=== BẮT ĐẦU PHASE CHỈNH SỬA ===")
            logger.info(f"Bắt đầu chỉnh sửa nghiên cứu cho topic: {request.topic}")
            logger.info(f"Số phần cần chỉnh sửa: {len(sections)}")
            
            # Lấy task_id từ outline nếu có
            task_id = outline.task_id if hasattr(outline, 'task_id') else None
            logger.info(f"EditService.execute: task_id = {task_id}")
            
            # Kiểm tra sections
            if not sections or len(sections) == 0:
                logger.warning("Không có sections nào để chỉnh sửa")
                raise EditError("Không có sections nào để chỉnh sửa")
            
            # Kiểm tra nội dung của sections
            for i, section in enumerate(sections):
                if not section.content:
                    logger.warning(f"Section {i+1} ({section.title}) không có nội dung")
            
            # Bắt đầu ghi nhận thời gian cho phase chỉnh sửa
            if task_id:
                self.cost_service.start_phase_timing(task_id, "editing")
            
            # Tạo context từ request
            context = {
                "topic": request.topic,
                "scope": request.scope,
                "target_audience": request.target_audience
            }
            
            # Chỉnh sửa và kết hợp nội dung
            logger.info("Bắt đầu chỉnh sửa và kết hợp nội dung...")
            try:
                content = await self.edit_content(sections, context, task_id)
                logger.info(f"Chỉnh sửa nội dung thành công, độ dài: {len(content)} ký tự")
            except Exception as e:
                logger.error(f"Lỗi khi chỉnh sửa nội dung trong execute: {str(e)}")
                # Tạo nội dung mặc định từ các sections
                content = "# " + request.topic + "\n\n"
                for section in sections:
                    content += "## " + section.title + "\n\n"
                    if section.content:
                        content += section.content + "\n\n"
                logger.info(f"Sử dụng nội dung mặc định do lỗi, độ dài: {len(content)} ký tự")
            
            # Tạo tiêu đề
            logger.info("Bắt đầu tạo tiêu đề...")
            try:
                title = await self.create_title(content, context, task_id)
                logger.info(f"Tạo tiêu đề thành công: {title}")
            except Exception as e:
                logger.error(f"Lỗi khi tạo tiêu đề trong execute: {str(e)}")
                title = request.topic
                logger.info(f"Sử dụng tiêu đề mặc định do lỗi: {title}")
            
            # Thu thập các nguồn
            logger.info("Bắt đầu thu thập nguồn tham khảo...")
            sources = self._collect_sources(sections)
            logger.info(f"Thu thập nguồn thành công: {len(sources)} nguồn")
            
            # Tạo kết quả nghiên cứu hoàn chỉnh
            # Tạo các đối tượng ResearchSection mới để tránh lỗi validation
            new_sections = []
            for section in sections:
                new_section = {
                    "title": section.title,
                    "description": section.description,
                    "content": section.content
                }
                new_sections.append(new_section)
                
            result = ResearchResult(
                title=title,
                content=content,
                sections=new_sections,
                sources=sources
            )
            
            # Kết thúc ghi nhận thời gian cho phase chỉnh sửa
            if task_id:
                self.cost_service.end_phase_timing(task_id, "editing", "completed")
                # Bắt đầu ghi nhận thời gian cho phase hoàn thành
                self.cost_service.start_phase_timing(task_id, "completed")
                self.cost_service.end_phase_timing(task_id, "completed", "completed")
                # Lưu dữ liệu monitoring
                try:
                    await self.cost_service.save_monitoring_data(task_id)
                except Exception as e:
                    logger.error(f"Lỗi khi lưu dữ liệu monitoring: {str(e)}")
            
            logger.info(f"=== KẾT THÚC PHASE CHỈNH SỬA - THÀNH CÔNG ===")
            return result
        except Exception as e:
            logger.error(f"=== KẾT THÚC PHASE CHỈNH SỬA - THẤT BẠI ===")
            logger.error(f"Lỗi trong quá trình chỉnh sửa: {str(e)}")
            raise EditError(
                "Lỗi trong quá trình chỉnh sửa",
                details={"error": str(e)}
            )
    
    async def edit_content(
        self, 
        sections: List[ResearchSection], 
        context: Dict[str, Any],
        task_id: str = None
    ) -> str:
        """
        Chỉnh sửa và kết hợp nội dung từ các phần nghiên cứu
        
        Args:
            sections: Danh sách các phần nghiên cứu
            context: Context cho việc chỉnh sửa
            task_id: ID của task để ghi nhận chi phí
            
        Returns:
            str: Nội dung đã chỉnh sửa
        """
        try:
            logger.info("Bắt đầu chỉnh sửa và kết hợp nội dung...")
            logger.info(f"EditService.edit_content: task_id = {task_id}")
            
            # Kiểm tra sections
            if not sections or len(sections) == 0:
                logger.warning("Không có sections nào để chỉnh sửa")
                return f"# {context['topic']}\n\nKhông có nội dung để chỉnh sửa."
            
            # Tạo nội dung từ các sections để gửi đến LLM
            combined_content = ""
            for i, section in enumerate(sections):
                # Kiểm tra và log thông tin về section
                logger.info(f"Section {i+1}: {section.title}")
                logger.info(f"Section {i+1} có nội dung: {len(section.content) if section.content else 0} ký tự")
                
                # Thêm nội dung section vào combined_content
                combined_content += f"## {section.title}\n\n"
                if section.content:
                    combined_content += f"{section.content}\n\n"
                else:
                    logger.warning(f"Section {i+1} ({section.title}) không có nội dung")
                    combined_content += "Không có nội dung cho phần này.\n\n"
            
            # Tạo prompt
            prompt = self.prompts.EDIT_CONTENT.format(
                topic=context["topic"],
                scope=context["scope"],
                target_audience=context["target_audience"],
                content=combined_content
            )
            
            # Gọi LLM để chỉnh sửa nội dung
            logger.info(f"Gửi prompt chỉnh sửa nội dung đến LLM (độ dài: {len(prompt)} ký tự)")
            try:
                response = await self.llm_service.generate(
                    prompt=prompt,
                    task_id=task_id,
                    purpose="edit_content"
                )
                logger.info(f"Nhận phản hồi từ LLM (độ dài: {len(response)} ký tự)")
                
                # Xử lý kết quả
                content = response.strip()
                
                # Kiểm tra xem kết quả có phải là JSON không
                try:
                    content_data = json.loads(content)
                    if isinstance(content_data, dict):
                        if "content" in content_data:
                            content = content_data["content"]
                            logger.info("Đã trích xuất nội dung từ JSON với trường 'content'")
                        elif "text" in content_data:
                            content = content_data["text"]
                            logger.info("Đã trích xuất nội dung từ JSON với trường 'text'")
                        elif "result" in content_data:
                            content = content_data["result"]
                            logger.info("Đã trích xuất nội dung từ JSON với trường 'result'")
                except json.JSONDecodeError:
                    # Nếu không phải JSON, sử dụng toàn bộ phản hồi
                    logger.info("Phản hồi không phải là JSON, sử dụng toàn bộ phản hồi")
                
                return content
            except Exception as llm_error:
                logger.error(f"Lỗi khi gọi LLM để chỉnh sửa nội dung: {str(llm_error)}")
                raise llm_error
                
        except Exception as e:
            logger.error(f"Lỗi khi chỉnh sửa nội dung: {str(e)}")
            # Tạo nội dung mặc định từ các sections
            default_content = f"# {context['topic']}\n\n"
            for section in sections:
                default_content += f"## {section.title}\n\n"
                if section.content:
                    default_content += f"{section.content}\n\n"
            
            logger.info(f"Sử dụng nội dung mặc định do lỗi, độ dài: {len(default_content)} ký tự")
            return default_content
    
    async def create_title(
        self, 
        content: str, 
        context: Dict[str, Any],
        task_id: str = None
    ) -> str:
        """
        Tạo tiêu đề cho bài nghiên cứu
        
        Args:
            content: Nội dung đã chỉnh sửa
            context: Context cho việc tạo tiêu đề
            task_id: ID của task để ghi nhận chi phí
            
        Returns:
            str: Tiêu đề cho bài nghiên cứu
        """
        try:
            logger.info("Bắt đầu tạo tiêu đề...")
            logger.info(f"EditService.create_title: task_id = {task_id}")
            
            # Lấy đoạn đầu của nội dung để tạo tiêu đề
            content_preview = content[:2000]  # Lấy 2000 ký tự đầu tiên
            
            # Tạo prompt
            prompt = self.prompts.CREATE_TITLE.format(
                topic=context["topic"],
                scope=context["scope"],
                target_audience=context["target_audience"],
                content_preview=content_preview
            )
            
            # Gọi LLM để tạo tiêu đề
            logger.info(f"Gửi prompt tạo tiêu đề đến LLM: {prompt[:100]}...")
            try:
                response = await self.llm_service.generate(
                    prompt=prompt,
                    task_id=task_id,
                    purpose="create_title"
                )
                logger.info(f"Nhận phản hồi từ LLM: {response}")
                
                # Xử lý kết quả
                title = response.strip()
                
                # Log giá trị của title để debug
                logger.info(f"Title trước khi xử lý JSON: '{title}'")
                
                # Kiểm tra xem kết quả có phải là JSON không
                try:
                    title_data = json.loads(title)
                    if isinstance(title_data, dict):
                        if "title" in title_data:
                            title = title_data["title"]
                            logger.info("Đã trích xuất tiêu đề từ JSON với trường 'title'")
                        elif "text" in title_data:
                            title = title_data["text"]
                            logger.info("Đã trích xuất tiêu đề từ JSON với trường 'text'")
                        elif "result" in title_data:
                            title = title_data["result"]
                            logger.info("Đã trích xuất tiêu đề từ JSON với trường 'result'")
                except json.JSONDecodeError:
                    # Nếu không phải JSON, sử dụng toàn bộ phản hồi
                    logger.info("Phản hồi không phải là JSON, sử dụng toàn bộ phản hồi")
                
                # Loại bỏ dấu ngoặc kép nếu có
                title = title.strip('"')
                
                return title
            except Exception as llm_error:
                logger.error(f"Lỗi khi gọi LLM để tạo tiêu đề: {str(llm_error)}")
                raise llm_error
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo tiêu đề: {str(e)}")
            # Trả về tiêu đề mặc định nếu có lỗi
            logger.info(f"Sử dụng tiêu đề mặc định do lỗi: {context['topic']}")
            return context["topic"]
    
    def _collect_sources(self, sections: List[ResearchSection]) -> List[str]:
        """
        Thu thập các nguồn tham khảo từ các phần
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            
        Returns:
            List[str]: Danh sách các nguồn tham khảo
        """
        all_sources = []
        
        # Thu thập các nguồn từ các phần
        for section in sections:
            if section.sources:
                all_sources.extend(section.sources)
        
        # Loại bỏ các nguồn trùng lặp
        unique_sources = list(dict.fromkeys(all_sources))
        
        return unique_sources
        
    async def research_section(
        self, 
        section: ResearchSection, 
        context: Dict[str, Any],
        task_id: str = None
    ) -> ResearchSection:
        """
        Triển khai phương thức abstract từ BaseResearchPhase
        Trong EditService, phương thức này không được sử dụng trực tiếp
        nhưng cần triển khai để tránh lỗi abstract method
        
        Args:
            section: Phần cần nghiên cứu
            context: Thông tin context
            task_id: ID của task để ghi nhận chi phí
            
        Returns:
            ResearchSection: Phần đã được nghiên cứu
        """
        # Trong EditService, phương thức này không thực sự được sử dụng
        # nhưng cần triển khai để tránh lỗi abstract method
        return section
