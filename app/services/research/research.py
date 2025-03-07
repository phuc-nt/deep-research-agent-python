import json
from typing import Any, Dict, List

from app.core.config import get_research_prompts
from app.core.exceptions import ResearchError
from app.core.factory import service_factory
from app.services.research.base import (
    BaseResearchPhase,
    ResearchSection,
    ResearchRequest,
    ResearchOutline
)

class ResearchService(BaseResearchPhase):
    """Service thực hiện phase nghiên cứu chi tiết trong quy trình"""
    
    def __init__(self):
        """Khởi tạo service với các prompts và services cần thiết"""
        self.prompts = get_research_prompts()
        self.llm_service = service_factory.create_llm_service()
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
            # Context cho việc nghiên cứu
            context = {
                "topic": request.topic,
                "scope": request.scope,
                "target_audience": request.target_audience
            }
            
            # Nghiên cứu từng phần
            researched_sections = []
            for section in outline.sections:
                researched_section = await self.research_section(
                    section=section,
                    context=context
                )
                researched_sections.append(researched_section)
            
            return researched_sections
        except Exception as e:
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
        Thực hiện nghiên cứu cho một phần cụ thể
        
        Args:
            section: Phần cần nghiên cứu
            context: Thông tin context (topic, scope, target_audience)
            
        Returns:
            ResearchSection: Phần đã được nghiên cứu với nội dung đầy đủ
            
        Raises:
            ResearchError: Nếu có lỗi trong quá trình nghiên cứu phần
        """
        try:
            # Tìm kiếm thông tin chi tiết
            search_results = await self._search_section_info(section, context)
            
            # Phân tích và tổng hợp thông tin
            section_content = await self._analyze_and_synthesize(
                section=section,
                context=context,
                search_results=search_results
            )
            
            # Cập nhật nội dung cho section
            section.content = section_content
            return section
        except Exception as e:
            raise ResearchError(
                f"Lỗi khi nghiên cứu phần '{section.title}'",
                details={"error": str(e)}
            )
    
    async def _search_section_info(
        self,
        section: ResearchSection,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm thông tin chi tiết cho một phần
        
        Args:
            section: Phần cần tìm kiếm thông tin
            context: Thông tin context
            
        Returns:
            List[Dict[str, Any]]: Danh sách kết quả tìm kiếm
        """
        # Format prompt tìm kiếm
        search_query = self.prompts.SEARCH_QUERY.format(
            topic=context["topic"],
            scope=context["scope"],
            section_title=section.title,
            section_description=section.description
        )
        
        # Thực hiện tìm kiếm
        results = await self.search_service.search(search_query)
        return results
    
    async def _analyze_and_synthesize(
        self,
        section: ResearchSection,
        context: Dict[str, Any],
        search_results: List[Dict[str, Any]]
    ) -> str:
        """
        Phân tích và tổng hợp thông tin thành nội dung hoàn chỉnh
        
        Args:
            section: Phần cần tổng hợp
            context: Thông tin context
            search_results: Kết quả tìm kiếm
            
        Returns:
            str: Nội dung đã được tổng hợp
        """
        # Format prompt phân tích
        prompt = self.prompts.ANALYZE_AND_SYNTHESIZE.format(
            topic=context["topic"],
            scope=context["scope"],
            target_audience=context["target_audience"],
            section_title=section.title,
            section_description=section.description,
            search_results=json.dumps(search_results, ensure_ascii=False)
        )
        
        # Gọi LLM để phân tích và tổng hợp
        content = await self.llm_service.generate(prompt)
        return content
