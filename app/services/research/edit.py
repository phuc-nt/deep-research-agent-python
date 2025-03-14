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
        self.cost_service = None
        
    async def initialize(self):
        """Khởi tạo các service bất đồng bộ"""
        if self.cost_service is None:
            service_factory = get_service_factory()
            self.cost_service = await service_factory.get_cost_monitoring_service()
    
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
            # Khởi tạo các service bất đồng bộ
            await self.initialize()
            
            logger.info(f"=== BẮT ĐẦU PHASE CHỈNH SỬA ===")
            logger.info(f"Bắt đầu chỉnh sửa nghiên cứu cho topic: {request.topic}")
            logger.info(f"Số phần cần chỉnh sửa: {len(sections)}")
            
            # Lấy task_id từ request hoặc outline
            task_id = None
            if hasattr(request, 'task_id') and request.task_id:
                task_id = request.task_id
                logger.info(f"Sử dụng task_id từ request: {task_id}")
            elif hasattr(outline, 'task_id') and outline.task_id:
                task_id = outline.task_id
                logger.info(f"Sử dụng task_id từ outline: {task_id}")
            else:
                logger.warning("Không tìm thấy task_id trong request hoặc outline")
                
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
                try:
                    await self.cost_service.start_phase_timing(task_id, "editing")
                except Exception as e:
                    logger.error(f"Lỗi khi bắt đầu timing cho phase editing: {str(e)}")
            
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
                try:
                    await self.cost_service.end_phase_timing(task_id, "editing", "completed")
                    # Bắt đầu ghi nhận thời gian cho phase hoàn thành
                    await self.cost_service.start_phase_timing(task_id, "completed")
                    await self.cost_service.end_phase_timing(task_id, "completed", "completed")
                    # Lưu dữ liệu monitoring
                    try:
                        await self.cost_service.save_monitoring_data(task_id)
                    except Exception as e:
                        logger.error(f"Lỗi khi lưu dữ liệu monitoring: {str(e)}")
                except Exception as e:
                    logger.error(f"Lỗi khi kết thúc timing cho phase editing: {str(e)}")
            
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
        Chỉnh sửa và kết hợp nội dung từ các phần đã nghiên cứu
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            context: Context cho việc chỉnh sửa
            task_id: ID của task để ghi nhận chi phí
            
        Returns:
            str: Nội dung đã chỉnh sửa
        """
        try:
            logger.info("Bắt đầu chỉnh sửa và kết hợp nội dung...")
            logger.info(f"EditService.edit_content: task_id = {task_id}")
            
            # Log thông tin các phần
            for i, section in enumerate(sections, 1):
                logger.info(f"Section {i}: {section.title}")
                logger.info(f"Section {i} có nội dung: {len(section.content)} ký tự")
            
            # Kết hợp nội dung từ các phần
            combined_content = "\n\n".join([
                f"## {section.title}\n\n{section.content}" 
                for section in sections
            ])
            
            # Tạo prompt
            prompt = self.prompts.EDIT_CONTENT.format(
                topic=context["topic"],
                scope=context["scope"],
                target_audience=context["target_audience"],
                content=combined_content
            )
            
            # Gọi LLM để chỉnh sửa nội dung
            logger.info(f"Gửi prompt chỉnh sửa nội dung đến LLM (độ dài: {len(prompt)} ký tự)")
            response = ""
            try:
                response = await self.llm_service.generate(
                    prompt=prompt,
                    task_id=task_id,
                    purpose="edit_content"
                )
                # Log phản hồi từ LLM để debug
                logger.info(f"Nhận phản hồi từ LLM (độ dài: {len(response)} ký tự)")
                logger.info(f"Phản hồi LLM (100 ký tự đầu): {response[:100]}")
                
                # Xử lý kết quả
                content = response.strip()
                
                # Kiểm tra xem kết quả có phải là JSON không
                try:
                    content_data = json.loads(content)
                    if isinstance(content_data, dict):
                        logger.info(f"Phản hồi là JSON với các trường: {list(content_data.keys())}")
                        # Kiểm tra các trường có thể chứa nội dung
                        for field in ["content", "text", "result", "markdown"]:
                            if field in content_data and content_data[field]:
                                content = content_data[field]
                                logger.info(f"Đã trích xuất nội dung từ JSON với trường '{field}'")
                                break
                except json.JSONDecodeError:
                    # Nếu không phải JSON, sử dụng toàn bộ phản hồi
                    logger.info("Phản hồi không phải là JSON, sử dụng toàn bộ phản hồi")
                
                # Kiểm tra nội dung rỗng
                if not content or len(content.strip()) == 0:
                    logger.warning("Nội dung trống, sử dụng nội dung mặc định")
                    return combined_content
                
                logger.info(f"Chỉnh sửa nội dung thành công, độ dài: {len(content)} ký tự")
                return content
            except Exception as llm_error:
                logger.error(f"Lỗi khi gọi LLM để chỉnh sửa nội dung: {str(llm_error)}")
                # Ghi lại phản hồi nếu có
                if response:
                    logger.error(f"Phản hồi LLM trước khi xảy ra lỗi (100 ký tự đầu): {response[:100]}")
                raise llm_error
            
        except Exception as e:
            logger.error(f"Lỗi khi chỉnh sửa nội dung: {str(e)}")
            # Trả về nội dung mặc định nếu có lỗi
            default_content = "\n\n".join([
                f"# {context['topic']}\n\n" +
                "\n\n".join([
                    f"## {section.title}\n\n{section.content}" 
                    for section in sections
                ])
            ])
            
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
            
            # Kiểm tra content
            if not content or len(content.strip()) == 0:
                logger.warning("Content trống, không thể tạo tiêu đề")
                return context.get("topic", "Không có tiêu đề")
            
            # Kiểm tra context
            if not context:
                logger.warning("Context trống, không thể tạo tiêu đề")
                return "Không có tiêu đề"
            
            # Kiểm tra các trường cần thiết trong context
            required_fields = ["topic", "scope", "target_audience"]
            for field in required_fields:
                if field not in context:
                    logger.warning(f"Thiếu trường {field} trong context, sử dụng giá trị mặc định")
                    context[field] = "Không xác định"
            
            # Lấy đoạn đầu của nội dung để tạo tiêu đề
            content_preview = content[:2000]  # Lấy 2000 ký tự đầu tiên
            
            # Tạo prompt
            try:
                prompt = self.prompts.CREATE_TITLE.format(
                    topic=context["topic"],
                    scope=context["scope"],
                    target_audience=context["target_audience"],
                    content=content_preview
                )
            except KeyError as format_error:
                logger.error(f"Lỗi khi tạo prompt: {str(format_error)}")
                return context.get("topic", "Không có tiêu đề")
            
            # Gọi LLM để tạo tiêu đề
            logger.info(f"Gửi prompt tạo tiêu đề đến LLM: {prompt[:100]}...")
            response = ""
            try:
                response = await self.llm_service.generate(
                    prompt=prompt,
                    task_id=task_id,
                    purpose="create_title"
                )
                # Log phản hồi từ LLM để debug
                logger.info(f"Nhận phản hồi từ LLM cho create_title: {response[:100]}...")
                
                # Xử lý kết quả
                title = response.strip()
                
                # Log giá trị của title để debug
                logger.info(f"Title trước khi xử lý JSON: '{title}'")
                
                # Kiểm tra xem kết quả có phải là JSON không
                try:
                    # Thử parse JSON
                    title_data = json.loads(title)
                    
                    # Kiểm tra nếu là dict
                    if isinstance(title_data, dict):
                        logger.info(f"Phản hồi là JSON với các trường: {list(title_data.keys())}")
                        
                        # Kiểm tra các trường có thể chứa tiêu đề
                        found_title = False
                        for field in ["title", "text", "result", "content"]:
                            if field in title_data and title_data[field]:
                                title = title_data[field]
                                logger.info(f"Đã trích xuất tiêu đề từ JSON với trường '{field}'")
                                found_title = True
                                break
                        
                        # Nếu không tìm thấy trường nào phù hợp, sử dụng giá trị đầu tiên
                        if not found_title and title_data:
                            first_key = list(title_data.keys())[0]
                            if title_data[first_key] and isinstance(title_data[first_key], str):
                                title = title_data[first_key]
                                logger.info(f"Sử dụng giá trị từ trường đầu tiên '{first_key}' làm tiêu đề")
                    
                except json.JSONDecodeError:
                    # Nếu không phải JSON, sử dụng toàn bộ phản hồi
                    logger.info("Phản hồi không phải là JSON, sử dụng toàn bộ phản hồi")
                except KeyError as key_error:
                    # Xử lý lỗi khi truy cập key không tồn tại trong JSON
                    logger.error(f"Lỗi KeyError khi xử lý JSON: {str(key_error)}")
                    # Vẫn sử dụng phản hồi gốc
                    logger.info("Sử dụng phản hồi gốc do lỗi KeyError trong JSON")
                except Exception as json_error:
                    # Bắt các lỗi khác khi xử lý JSON
                    logger.error(f"Lỗi khi xử lý JSON: {str(json_error)}")
                    # Vẫn sử dụng phản hồi gốc
                    logger.info("Sử dụng phản hồi gốc do lỗi khi xử lý JSON")
                
                # Loại bỏ dấu ngoặc kép nếu có
                if isinstance(title, str):
                    title = title.strip('"')
                else:
                    logger.warning(f"Title không phải là string mà là {type(title)}, chuyển đổi sang string")
                    title = str(title).strip('"')
                
                # Kiểm tra tiêu đề rỗng
                if not title or len(title.strip()) == 0:
                    logger.warning("Tiêu đề trống, sử dụng tiêu đề mặc định")
                    return context["topic"]
                
                return title
            except Exception as llm_error:
                logger.error(f"Lỗi khi gọi LLM để tạo tiêu đề: {str(llm_error)}")
                # Ghi lại phản hồi nếu có
                if response:
                    logger.error(f"Phản hồi LLM trước khi xảy ra lỗi: {response[:100]}...")
                return context.get("topic", "Không có tiêu đề")
            
        except KeyError as key_error:
            # Xử lý lỗi khi truy cập key không tồn tại
            logger.error(f"Lỗi KeyError khi tạo tiêu đề: {str(key_error)}")
            logger.info(f"Sử dụng tiêu đề mặc định do lỗi KeyError: {context.get('topic', 'Không có tiêu đề')}")
            return context.get("topic", "Không có tiêu đề")
        except Exception as e:
            logger.error(f"Lỗi khi tạo tiêu đề: {str(e)}")
            # Trả về tiêu đề mặc định nếu có lỗi
            logger.info(f"Sử dụng tiêu đề mặc định do lỗi: {context.get('topic', 'Không có tiêu đề')}")
            return context.get("topic", "Không có tiêu đề")
    
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
