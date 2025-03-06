import json
from typing import Any, Dict

from app.core.config import get_prepare_prompts
from app.core.exceptions import PrepareError
from app.core.factory import service_factory
from app.services.research.base import (
    BasePreparePhase,
    ResearchRequest,
    ResearchOutline,
    ResearchSection
)

class PrepareService(BasePreparePhase):
    """Service thực hiện phase chuẩn bị trong quy trình nghiên cứu"""
    
    def __init__(self):
        """Khởi tạo service với các prompts và LLM service"""
        self.prompts = get_prepare_prompts()
        self.llm_service = service_factory.create_llm_service()
        self.search_service = service_factory.create_search_service()
    
    async def execute(self, request: ResearchRequest) -> ResearchOutline:
        """
        Thực thi phase chuẩn bị
        
        Args:
            request: Yêu cầu nghiên cứu
            
        Returns:
            ResearchOutline: Dàn ý cho bài nghiên cứu
            
        Raises:
            PrepareError: Nếu có lỗi trong quá trình chuẩn bị
        """
        try:
            # Phân tích yêu cầu
            analysis = await self.analyze_query(request)
            
            # Tạo dàn ý
            outline = await self.create_outline(analysis)
            
            return outline
        except Exception as e:
            raise PrepareError(
                "Lỗi trong quá trình chuẩn bị",
                details={"error": str(e)}
            )
    
    async def analyze_query(self, request: ResearchRequest) -> Dict[str, Any]:
        """
        Phân tích yêu cầu nghiên cứu để xác định các thông tin quan trọng
        
        Args:
            request: Yêu cầu nghiên cứu
            
        Returns:
            Dict[str, Any]: Kết quả phân tích bao gồm topic, scope, target_audience
            
        Raises:
            PrepareError: Nếu có lỗi trong quá trình phân tích
        """
        try:
            # Format prompt với yêu cầu nghiên cứu
            prompt = self.prompts.ANALYZE_QUERY.format(
                query=request.query
            )
            
            # Gọi LLM để phân tích
            response = await self.llm_service.generate(prompt)
            
            # Parse kết quả JSON
            analysis = json.loads(response)
            
            # Cập nhật request với thông tin đã phân tích
            if not request.topic:
                request.topic = analysis.get("Topic")
            if not request.scope:
                request.scope = analysis.get("Scope")
            if not request.target_audience:
                request.target_audience = analysis.get("Target Audience")
            
            return analysis
        except Exception as e:
            raise PrepareError(
                "Lỗi khi phân tích yêu cầu nghiên cứu",
                details={"error": str(e)}
            )
    
    async def create_outline(self, analysis: Dict[str, Any]) -> ResearchOutline:
        """
        Tạo dàn ý cho bài nghiên cứu dựa trên kết quả phân tích
        
        Args:
            analysis: Kết quả phân tích từ analyze_query
            
        Returns:
            ResearchOutline: Dàn ý cho bài nghiên cứu
            
        Raises:
            PrepareError: Nếu có lỗi trong quá trình tạo dàn ý
        """
        try:
            # Format prompt với thông tin đã phân tích
            prompt = self.prompts.CREATE_OUTLINE.format(
                query=f"Topic: {analysis.get('Topic')}\nScope: {analysis.get('Scope')}\nTarget Audience: {analysis.get('Target Audience')}"
            )
            
            # Gọi LLM để tạo dàn ý
            response = await self.llm_service.generate(prompt)
            
            # Parse kết quả JSON
            outline_data = json.loads(response)
            
            # Tạo các section từ dữ liệu
            sections = [
                ResearchSection(
                    title=section["title"],
                    description=section["description"]
                )
                for section in outline_data["researchSections"]
            ]
            
            return ResearchOutline(sections=sections)
        except Exception as e:
            raise PrepareError(
                "Lỗi khi tạo dàn ý nghiên cứu",
                details={"error": str(e)}
            ) 