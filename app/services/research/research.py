import json
import time
from typing import Any, Dict, List

from app.core.config import get_research_prompts
from app.core.exceptions import ResearchError
from app.core.factory import get_service_factory
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
        service_factory = get_service_factory()
        self.llm_service = service_factory.create_llm_service_for_phase("research")
        self.search_service = None
        self.update_progress_callback = None
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
        outline: ResearchOutline
    ) -> List[ResearchSection]:
        """
        Thực thi phase nghiên cứu
        """
        # Khởi tạo các service bất đồng bộ
        await self.initialize()
        
        try:
            service_factory = get_service_factory()
            self.search_service = await service_factory.create_search_service()
            
            logger.info(f"=== BẮT ĐẦU PHASE NGHIÊN CỨU ===")
            logger.info(f"Bắt đầu nghiên cứu cho topic: {request.topic}")
            logger.info(f"Số phần cần nghiên cứu: {len(outline.sections)}")
            
            # Tạo context cho quá trình nghiên cứu
            context = {
                "query": request.query,
                "topic": request.topic,
                "scope": request.scope,
                "target_audience": request.target_audience,
                "outline": outline.dict()
            }
            
            # Bắt đầu ghi nhận thời gian cho phase nghiên cứu
            task_id = outline.task_id if hasattr(outline, 'task_id') else None
            if task_id:
                await self.cost_service.start_phase_timing(task_id, "researching")
            
            # Nghiên cứu từng phần
            researched_sections = []
            total_sections = len(outline.sections)
            
            for i, section in enumerate(outline.sections):
                logger.info(f"Bắt đầu nghiên cứu phần {i+1}/{total_sections}: {section.title}")
                
                # Cập nhật thông tin tiến độ
                progress_info = {
                    "phase": "researching",
                    "current_section": i + 1,
                    "total_sections": total_sections,
                    "current_section_title": section.title,
                    "completed_sections": i
                }
                
                # Gửi thông tin tiến độ đến callback nếu có
                if hasattr(self, 'update_progress_callback') and callable(self.update_progress_callback):
                    await self.update_progress_callback(progress_info)
                
                # Bắt đầu ghi nhận thời gian cho section
                if task_id:
                    section_id = f"section_{i+1}"
                    await self.cost_service.start_section_timing(task_id, section_id, section.title)
                
                # Nghiên cứu phần này
                researched_section = await self.research_section(section, context, task_id)
                researched_sections.append(researched_section)
                
                # Kết thúc ghi nhận thời gian cho section
                if task_id:
                    await self.cost_service.end_section_timing(task_id, section_id, "completed")
                
                logger.info(f"Đã hoàn thành nghiên cứu phần {i+1}/{total_sections}: {section.title}")
                logger.info(f"Độ dài nội dung: {len(researched_section.content) if researched_section.content else 0} ký tự")
                logger.info(f"Số nguồn tham khảo: {len(researched_section.sources) if researched_section.sources else 0}")
            
            # Kết thúc ghi nhận thời gian cho phase nghiên cứu
            if task_id:
                await self.cost_service.end_phase_timing(task_id, "researching", "completed")
                # Lưu dữ liệu monitoring
                await self.cost_service.save_monitoring_data(task_id)
            
            logger.info(f"=== KẾT THÚC PHASE NGHIÊN CỨU - THÀNH CÔNG ===")
            logger.info(f"Đã hoàn thành nghiên cứu {len(researched_sections)}/{total_sections} phần")
            
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
        context: Dict[str, Any],
        task_id: str = None
    ) -> ResearchSection:
        """
        Nghiên cứu một phần cụ thể
        
        Args:
            section: Phần cần nghiên cứu
            context: Context cho việc nghiên cứu
            task_id: ID của task để ghi nhận chi phí
            
        Returns:
            ResearchSection: Phần đã được nghiên cứu
        """
        try:
            # Tìm kiếm thông tin
            logger.info(f"Bắt đầu tìm kiếm thông tin cho phần: {section.title}")
            search_results = await self._search_section_info(section, context, task_id)
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
            # Truyền task_id để ghi nhận chi phí
            content = await self.llm_service.generate(
                prompt=prompt,
                task_id=task_id,
                purpose=f"research_section_{section.title}"
            )
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
        context: Dict[str, Any],
        task_id: str = None
    ) -> List[Dict[str, str]]:
        """
        Tìm kiếm thông tin cho một phần
        
        Args:
            section: Phần cần tìm kiếm
            context: Context cho việc tìm kiếm
            task_id: ID của task để ghi nhận chi phí
            
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
            # Truyền task_id để ghi nhận chi phí
            results = await self.search_service.search(
                query=search_query,
                task_id=task_id,
                purpose=f"search_section_{section.title}"
            )
            end_time = time.time()
            
            logger.info(f"Tìm kiếm hoàn thành trong {end_time - start_time:.2f} giây")
            logger.info(f"Tìm thấy {len(results)} kết quả cho phần {section.title}")
            
            return results
            
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm thông tin cho phần {section.title}: {str(e)}")
            raise
