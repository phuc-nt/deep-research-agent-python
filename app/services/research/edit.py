import json
from typing import Any, Dict, List

from app.core.config import get_edit_prompts
from app.core.exceptions import EditError
from app.core.factory import service_factory
from app.services.research.base import (
    BaseEditPhase,
    ResearchSection,
    ResearchResult
)

class EditService(BaseEditPhase):
    """Service thực hiện phase chỉnh sửa trong quy trình nghiên cứu"""
    
    def __init__(self):
        """Khởi tạo service với các prompts và LLM service"""
        self.prompts = get_edit_prompts()
        self.llm_service = service_factory.create_llm_service()
    
    async def execute(
        self, 
        sections: List[ResearchSection], 
        context: Dict[str, Any]
    ) -> ResearchResult:
        """
        Thực thi phase chỉnh sửa
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            context: Thông tin context (topic, scope, target_audience)
            
        Returns:
            ResearchResult: Kết quả nghiên cứu hoàn chỉnh
            
        Raises:
            EditError: Nếu có lỗi trong quá trình chỉnh sửa
        """
        try:
            # Chỉnh sửa và kết hợp nội dung
            content = await self.edit_content(sections, context)
            
            # Tạo tiêu đề
            title = await self.create_title(content, context)
            
            # Thu thập các nguồn
            sources = self._collect_sources(sections)
            
            # Tạo kết quả nghiên cứu hoàn chỉnh
            result = ResearchResult(
                title=title,
                content=content,
                sections=sections,
                sources=sources
            )
            
            return result
        except Exception as e:
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
        Chỉnh sửa và kết hợp các phần thành bài nghiên cứu hoàn chỉnh
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            context: Thông tin context (topic, scope, target_audience)
            
        Returns:
            str: Nội dung bài nghiên cứu hoàn chỉnh
            
        Raises:
            EditError: Nếu có lỗi trong quá trình chỉnh sửa nội dung
        """
        try:
            # Kết hợp nội dung từ các phần
            combined_content = ""
            for section in sections:
                combined_content += f"## {section.title}\n\n"
                combined_content += f"{section.content}\n\n"
            
            # Format prompt với nội dung đã kết hợp và context
            prompt = self.prompts.EDIT_CONTENT.format(
                content=combined_content,
                topic=context.get("topic", ""),
                scope=context.get("scope", ""),
                target_audience=context.get("target_audience", "")
            )
            
            # Gọi LLM để chỉnh sửa
            edited_content = await self.llm_service.generate(prompt)
            
            return edited_content
        except Exception as e:
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
            
        Raises:
            EditError: Nếu có lỗi trong quá trình tạo tiêu đề
        """
        try:
            # Lấy 1000 ký tự đầu tiên của nội dung để tạo tiêu đề
            content_preview = content[:1000]
            
            # Format prompt để tạo tiêu đề
            prompt = f"""
            Tạo một tiêu đề hấp dẫn và súc tích cho bài nghiên cứu sau:
            
            Chủ đề: {context.get("topic", "")}
            Phạm vi: {context.get("scope", "")}
            Đối tượng đọc: {context.get("target_audience", "")}
            
            Nội dung bài nghiên cứu (phần đầu):
            {content_preview}
            
            Yêu cầu:
            1. Tiêu đề phải ngắn gọn, không quá 100 ký tự
            2. Phản ánh chính xác nội dung bài nghiên cứu
            3. Hấp dẫn và thu hút người đọc
            4. Viết bằng tiếng Việt
            
            Chỉ trả về tiêu đề, không thêm bất kỳ nội dung nào khác.
            """
            
            # Gọi LLM để tạo tiêu đề
            title = await self.llm_service.generate(prompt)
            
            # Loại bỏ các ký tự không cần thiết
            title = title.strip().strip('"').strip("'")
            
            return title
        except Exception as e:
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
        sources = []
        
        # Tìm các URL trong nội dung
        import re
        # Cập nhật pattern để loại bỏ dấu nháy đơn trong kết quả
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
        
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
        
        return sources
