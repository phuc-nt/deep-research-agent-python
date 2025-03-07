import json
import time
from typing import Any, Dict, List

from app.core.config import get_research_prompts
from app.core.exceptions import ResearchError
from app.core.factory import service_factory
from app.core.logging import logger
from app.services.research.base import (
    BaseResearchPhase,
    ResearchSection,
    ResearchRequest,
    ResearchOutline
)

class ResearchService(BaseResearchPhase):
    """Service thực hiện phase nghiên cứu chi tiết trong quy trình"""
    
    def __init__(self):
        """Khởi tạo service với các prompts và LLM service"""
        self.prompts = get_research_prompts()
        self.llm_service = service_factory.create_llm_service_for_phase("research")
        self.search_service = service_factory.create_search_service()
    
    async def execute(
        self, 
        request: ResearchRequest,
        outline: ResearchOutline
    ) -> List[ResearchSection]:
        """
        Thực thi phase nghiên cứu
        
        Args:
            request: Yêu cầu nghiên cứu
            outline: Dàn ý từ PrepareService
            
        Returns:
            List[ResearchSection]: Danh sách các phần đã được nghiên cứu
            
        Raises:
            ResearchError: Nếu có lỗi trong quá trình nghiên cứu
        """
        try:
            logger.info(f"=== BẮT ĐẦU PHASE NGHIÊN CỨU ===")
            logger.info(f"Bắt đầu nghiên cứu cho topic: {request.topic}")
            logger.info(f"Số phần cần nghiên cứu: {len(outline.sections)}")
            
            # Context cho việc nghiên cứu
            context = {
                "topic": request.topic,
                "scope": request.scope,
                "target_audience": request.target_audience
            }
            
            # Nghiên cứu từng phần
            researched_sections = []
            for i, section in enumerate(outline.sections):
                logger.info(f"=== BẮT ĐẦU NGHIÊN CỨU PHẦN {i+1}/{len(outline.sections)}: {section.title} ===")
                try:
                    researched_section = await self.research_section(
                        section=section,
                        context=context
                    )
                    researched_sections.append(researched_section)
                    logger.info(f"=== KẾT THÚC NGHIÊN CỨU PHẦN {i+1} - THÀNH CÔNG ===")
                except Exception as e:
                    logger.error(f"=== KẾT THÚC NGHIÊN CỨU PHẦN {i+1} - THẤT BẠI ===")
                    logger.error(f"Lỗi khi nghiên cứu phần {section.title}: {str(e)}")
                    # Vẫn tiếp tục với phần tiếp theo
            
            logger.info(f"Đã hoàn thành nghiên cứu {len(researched_sections)}/{len(outline.sections)} phần")
            logger.info(f"=== KẾT THÚC PHASE NGHIÊN CỨU - THÀNH CÔNG ===")
            return researched_sections
            
        except Exception as e:
            logger.error(f"=== KẾT THÚC PHASE NGHIÊN CỨU - THẤT BẠI ===")
            logger.error(f"Lỗi trong quá trình nghiên cứu: {str(e)}")
            raise ResearchError(
                "Lỗi trong quá trình nghiên cứu",
                details={"error": str(e)}
            )
            
    async def research_section(
        self,
        section: ResearchSection,
        context: Dict[str, Any]
    ) -> ResearchSection:
        """
        Nghiên cứu một phần cụ thể
        
        Args:
            section: Phần cần nghiên cứu
            context: Context cho việc nghiên cứu
            
        Returns:
            ResearchSection: Phần đã được nghiên cứu
        """
        try:
            # Tìm kiếm thông tin
            logger.info(f"Bắt đầu tìm kiếm thông tin cho phần: {section.title}")
            search_results = await self._search_section_info(section, context)
            logger.info(f"Tìm kiếm thành công: {len(search_results)} kết quả")
            
            # Log một số kết quả tìm kiếm đầu tiên
            for i, result in enumerate(search_results[:3]):
                logger.info(f"  Kết quả {i+1}: {result.get('title', 'N/A')} - {result.get('url', 'N/A')}")
            
            # Tổng hợp thông tin
            logger.info(f"Bắt đầu tổng hợp thông tin cho phần: {section.title}")
            prompt = self.prompts.ANALYZE_AND_SYNTHESIZE.format(
                topic=context["topic"],
                scope=context["scope"],
                target_audience=context["target_audience"],
                section_title=section.title,
                section_description=section.description,
                search_results=json.dumps(search_results, ensure_ascii=False)
            )
            
            logger.info(f"Gửi prompt tổng hợp đến LLM: {prompt[:100]}...")
            content = await self.llm_service.generate(prompt)
            logger.info(f"Nhận phản hồi từ LLM: {content[:100]}...")
            
            # Cập nhật nội dung cho phần
            section.content = content
            section.sources = [result["url"] for result in search_results]
            
            logger.info(f"Hoàn thành nghiên cứu phần: {section.title}")
            logger.info(f"Độ dài nội dung: {len(content)} ký tự")
            logger.info(f"Số nguồn tham khảo: {len(section.sources)}")
            
            return section
            
        except Exception as e:
            logger.error(f"Lỗi khi nghiên cứu phần {section.title}: {str(e)}")
            raise
            
    async def _search_section_info(
        self,
        section: ResearchSection,
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Tìm kiếm thông tin cho một phần
        
        Args:
            section: Phần cần tìm kiếm
            context: Context cho việc tìm kiếm
            
        Returns:
            List[Dict[str, str]]: Danh sách kết quả tìm kiếm
        """
        try:
            # Tạo query tìm kiếm
            search_query = f"{context['topic']} {section.title}"
            if section.description:
                search_query += f" {section.description}"
                
            logger.info(f"Thực hiện tìm kiếm với query: {search_query}")
            logger.info(f"Sử dụng search service: {self.search_service.__class__.__name__}")
            
            # Thực hiện tìm kiếm
            start_time = time.time()
            results = await self.search_service.search(search_query)
            end_time = time.time()
            
            logger.info(f"Tìm kiếm hoàn thành trong {end_time - start_time:.2f} giây")
            logger.info(f"Tìm thấy {len(results)} kết quả cho phần {section.title}")
            
            return results
            
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm thông tin cho phần {section.title}: {str(e)}")
            raise
