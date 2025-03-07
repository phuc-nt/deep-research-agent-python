import json
from typing import Any, Dict

from app.core.config import get_prepare_prompts
from app.core.exceptions import PrepareError
from app.core.factory import service_factory
from app.core.logging import logger
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
        self.llm_service = service_factory.create_llm_service_for_phase("prepare")
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
            logger.info(f"=== BẮT ĐẦU PHASE CHUẨN BỊ ===")
            logger.info(f"Bắt đầu chuẩn bị nghiên cứu cho topic: {request.topic}")
            
            # Phân tích yêu cầu
            logger.info("Bắt đầu phân tích yêu cầu nghiên cứu...")
            analysis = await self.analyze_query(request)
            logger.info(f"Phân tích yêu cầu thành công: {json.dumps(analysis, ensure_ascii=False)}")
            
            # Tạo dàn ý
            logger.info("Bắt đầu tạo dàn ý nghiên cứu...")
            outline = await self.create_outline(analysis)
            logger.info(f"Tạo dàn ý thành công với {len(outline.sections)} phần")
            for i, section in enumerate(outline.sections):
                logger.info(f"  Phần {i+1}: {section.title} - {section.description}")
            
            logger.info("=== KẾT THÚC PHASE CHUẨN BỊ - THÀNH CÔNG ===")
            return outline
            
        except Exception as e:
            logger.error(f"=== KẾT THÚC PHASE CHUẨN BỊ - THẤT BẠI ===")
            logger.error(f"Lỗi trong quá trình chuẩn bị: {str(e)}")
            raise PrepareError(
                "Lỗi trong quá trình chuẩn bị",
                details={"error": str(e)}
            )
    
    async def analyze_query(self, request: ResearchRequest) -> Dict[str, Any]:
        """
        Phân tích yêu cầu nghiên cứu
        
        Args:
            request: Yêu cầu nghiên cứu
            
        Returns:
            Dict[str, Any]: Kết quả phân tích
        """
        try:
            logger.info("Phân tích yêu cầu với LLM")
            
            # Nếu đã có topic, scope, target_audience thì sử dụng
            if request.topic and request.scope and request.target_audience:
                logger.info("Sử dụng thông tin đã có trong yêu cầu")
                analysis = {
                    "topic": request.topic,
                    "scope": request.scope,
                    "target_audience": request.target_audience
                }
                return analysis
            
            # Nếu không, phân tích bằng LLM
            prompt = self.prompts.ANALYZE_QUERY.format(query=request.query)
            
            logger.info(f"Gửi prompt phân tích đến LLM: {prompt[:100]}...")
            response = await self.llm_service.generate(prompt)
            logger.info(f"Nhận phản hồi từ LLM: {response[:100]}...")
            
            # Parse kết quả JSON
            try:
                analysis = json.loads(response)
                logger.info(f"Phân tích JSON thành công: {json.dumps(analysis, ensure_ascii=False)}")
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Lỗi khi parse JSON: {str(e)}")
                logger.error(f"Phản hồi gốc: {response}")
                # Thử phân tích thủ công
                analysis = self._manual_parse_analysis(response)
                logger.info(f"Phân tích thủ công: {json.dumps(analysis, ensure_ascii=False)}")
                return analysis
                
        except Exception as e:
            logger.error(f"Lỗi khi phân tích yêu cầu: {str(e)}")
            raise
    
    async def create_outline(self, analysis: Dict[str, Any]) -> ResearchOutline:
        """
        Tạo dàn ý cho bài nghiên cứu
        
        Args:
            analysis: Kết quả phân tích từ analyze_query
            
        Returns:
            ResearchOutline: Dàn ý cho bài nghiên cứu
        """
        try:
            logger.info("Tạo dàn ý với LLM")
            
            # Chuẩn hóa các khóa trong từ điển analysis
            topic = analysis.get("Topic") or analysis.get("topic", "")
            scope = analysis.get("Scope") or analysis.get("scope", "")
            target_audience = analysis.get("Target Audience") or analysis.get("target_audience", "")
            
            logger.info(f"Chuẩn hóa các khóa trong từ điển analysis: topic={topic}, scope={scope}, target_audience={target_audience}")
            
            # Tạo query từ thông tin đã phân tích
            query = f"Chủ đề: {topic}\nPhạm vi: {scope}\nĐối tượng đọc: {target_audience}"
            logger.info(f"Tạo query cho prompt tạo dàn ý: {query}")
            
            # Format prompt
            prompt = self.prompts.CREATE_OUTLINE.format(
                query=query
            )
            
            logger.info(f"Gửi prompt tạo dàn ý đến LLM: {prompt[:100]}...")
            response = await self.llm_service.generate(prompt)
            logger.info(f"Nhận phản hồi từ LLM: {response[:100]}...")
            
            # Parse kết quả JSON
            try:
                outline_data = json.loads(response)
                logger.info(f"Phân tích JSON thành công: {json.dumps(outline_data, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                logger.error(f"Lỗi khi parse JSON: {str(e)}")
                logger.error(f"Phản hồi gốc: {response}")
                # Thử phân tích thủ công
                outline_data = self._manual_parse_outline(response)
                logger.info(f"Phân tích thủ công: {json.dumps(outline_data, ensure_ascii=False)}")
            
            # Tạo outline object
            outline = ResearchOutline(
                title=outline_data.get("title", "Nghiên cứu"),
                sections=[
                    ResearchSection(
                        title=section["title"],
                        description=section.get("description", "")
                    )
                    for section in outline_data.get("researchSections", [])
                ]
            )
            
            logger.info(f"Đã tạo dàn ý với {len(outline.sections)} phần")
            return outline
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo dàn ý: {str(e)}")
            raise 