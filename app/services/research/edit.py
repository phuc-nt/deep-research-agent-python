import json
from typing import Any, Dict, List

from app.core.config import get_edit_prompts, get_settings, EditPrompts
from app.core.exceptions import EditError
from app.core.factory import service_factory
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
        self.llm_service = service_factory.create_llm_service_for_phase("edit")
    
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
            
            # Tạo context từ request
            context = {
                "topic": request.topic,
                "scope": request.scope,
                "target_audience": request.target_audience
            }
            
            # Chỉnh sửa và kết hợp nội dung
            logger.info("Bắt đầu chỉnh sửa và kết hợp nội dung...")
            content = await self.edit_content(sections, context)
            logger.info(f"Chỉnh sửa nội dung thành công, độ dài: {len(content)} ký tự")
            
            # Tạo tiêu đề
            logger.info("Bắt đầu tạo tiêu đề...")
            title = await self.create_title(content, context)
            logger.info(f"Tạo tiêu đề thành công: {title}")
            
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
            
            logger.info(f"=== KẾT THÚC PHASE CHỈNH SỬA - THÀNH CÔNG ===")
            return result
        except Exception as e:
            logger.error(f"=== KẾT THÚC PHASE CHỈNH SỬA - THẤT BẠI ===")
            logger.error(f"Lỗi trong quá trình chỉnh sửa: {str(e)}")
            raise EditError(
                "Lỗi trong quá trình chỉnh sửa",
                details={"error": str(e)}
            )
    
    async def research_section(
        self, 
        section: ResearchSection, 
        context: Dict[str, Any]
    ) -> ResearchSection:
        """
        Triển khai phương thức abstract từ BaseResearchPhase
        Trong EditService, phương thức này không được sử dụng trực tiếp
        nhưng cần triển khai để tránh lỗi abstract method
        
        Args:
            section: Phần cần nghiên cứu
            context: Thông tin context
            
        Returns:
            ResearchSection: Phần đã được nghiên cứu
            
        Raises:
            EditError: Nếu có lỗi
        """
        # Trong EditService, phương thức này không thực sự được sử dụng
        # nhưng cần triển khai để tránh lỗi abstract method
        return section
    
    async def edit_content(
        self, 
        sections: List[ResearchSection], 
        context: Dict[str, Any]
    ) -> str:
        """
        Chỉnh sửa và kết hợp nội dung các phần thành bài nghiên cứu hoàn chỉnh
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            context: Thông tin context (topic, scope, target_audience)
            
        Returns:
            str: Nội dung bài nghiên cứu hoàn chỉnh
        """
        try:
            logger.info("Bắt đầu chỉnh sửa nội dung...")
            
            # Chuẩn bị dữ liệu đầu vào
            sections_data = []
            for section in sections:
                if hasattr(section, 'content') and section.content:
                    sections_data.append({
                        "title": section.title,
                        "content": section.content
                    })
            
            logger.info(f"Số phần có nội dung: {len(sections_data)}/{len(sections)}")
            
            # Tạo nội dung từ các sections
            content = ""
            for section_data in sections_data:
                content += f"## {section_data['title']}\n\n"
                content += f"{section_data['content']}\n\n"
            
            # Format prompt
            prompt = self.prompts.EDIT_CONTENT.format(
                topic=context["topic"],
                scope=context["scope"],
                target_audience=context["target_audience"],
                content=content
            )
            
            logger.info(f"Gửi prompt chỉnh sửa đến LLM: {prompt[:100]}...")
            content = await self.llm_service.generate(prompt)
            logger.info(f"Nhận phản hồi từ LLM: {content[:100]}...")
            
            return content
            
        except Exception as e:
            logger.error(f"Lỗi khi chỉnh sửa nội dung: {str(e)}")
            raise EditError(
                "Lỗi khi chỉnh sửa nội dung",
                details={"error": str(e)}
            )
    
    async def create_title(
        self, 
        content: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Tạo tiêu đề cho bài nghiên cứu
        
        Args:
            content: Nội dung bài nghiên cứu
            context: Thông tin context (topic, scope, target_audience)
            
        Returns:
            str: Tiêu đề bài nghiên cứu
        """
        try:
            logger.info("Bắt đầu tạo tiêu đề...")
            
            # Format prompt
            prompt = self.prompts.CREATE_TITLE.format(
                topic=context["topic"],
                scope=context["scope"],
                target_audience=context["target_audience"],
                content=content[:1000]  # Chỉ sử dụng 1000 ký tự đầu tiên
            )
            
            logger.info(f"Gửi prompt tạo tiêu đề đến LLM: {prompt[:100]}...")
            title = await self.llm_service.generate(prompt)
            logger.info(f"Nhận phản hồi từ LLM: {title}")
            
            # Làm sạch tiêu đề
            title = title.strip().strip('"').strip()
            
            return title
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo tiêu đề: {str(e)}")
            raise EditError(
                "Lỗi khi tạo tiêu đề",
                details={"error": str(e)}
            )
    
    def _collect_sources(self, sections: List[ResearchSection]) -> List[str]:
        """
        Thu thập các nguồn từ nội dung các phần
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            
        Returns:
            List[str]: Danh sách các nguồn
        """
        logger.info("Bắt đầu thu thập nguồn tham khảo...")
        sources = []
        
        # Thu thập từ trường sources của mỗi section
        for section in sections:
            if hasattr(section, 'sources') and section.sources:
                for source in section.sources:
                    if source not in sources:
                        sources.append(source)
        
        logger.info(f"Đã thu thập {len(sources)} nguồn từ trường sources")
        
        # Tìm các URL trong nội dung
        import re
        # Cập nhật pattern để loại bỏ dấu nháy đơn trong kết quả
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
        
        url_count = 0
        for section in sections:
            if section.content:
                # Tìm tất cả URL trong nội dung
                found_urls = re.findall(url_pattern, section.content)
                
                # Thêm vào danh sách nguồn nếu chưa có
                for url in found_urls:
                    # Loại bỏ dấu nháy đơn ở cuối URL nếu có
                    clean_url = url.rstrip("'")
                    if clean_url not in sources:
                        sources.append(clean_url)
                        url_count += 1
        
        logger.info(f"Đã thu thập thêm {url_count} nguồn từ nội dung")
        logger.info(f"Tổng số nguồn: {len(sources)}")
        
        return sources
