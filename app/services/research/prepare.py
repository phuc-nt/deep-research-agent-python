import json
import re
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
            analysis = await self.analyze_query(request.query)
            logger.info(f"Phân tích yêu cầu thành công: {json.dumps(analysis, ensure_ascii=False)}")
            
            # Cập nhật request với thông tin phân tích
            updated_request = ResearchRequest(
                query=request.query,
                topic=analysis.get("topic"),
                scope=analysis.get("scope"),
                target_audience=analysis.get("target_audience")
            )
            
            # Tạo dàn ý
            logger.info("Bắt đầu tạo dàn ý nghiên cứu...")
            outline = await self.create_outline(updated_request)
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
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Phân tích yêu cầu nghiên cứu
        
        Args:
            query: Nội dung câu hỏi
            
        Returns:
            Dict[str, Any]: Kết quả phân tích
        """
        try:
            logger.info("Phân tích yêu cầu với LLM")
            
            # Nếu đã có topic, scope, target_audience thì sử dụng
            if query and query.startswith("Chủ đề:") and query.endswith("Đối tượng đọc:") and "Phạm vi:" in query:
                logger.info("Sử dụng thông tin đã có trong yêu cầu")
                analysis = {
                    "topic": query.split("Chủ đề:")[1].split("\n")[0].strip(),
                    "scope": query.split("Phạm vi:")[1].split("\n")[0].strip(),
                    "target_audience": query.split("Đối tượng đọc:")[1].strip()
                }
                return analysis
            
            # Nếu không, phân tích bằng LLM
            # Thêm hướng dẫn cụ thể để đảm bảo phân tích liên quan đến chủ đề
            enhanced_query = f"{query}\n\nLưu ý quan trọng: Hãy phân tích chủ đề cụ thể này, KHÔNG đưa ra phân tích chung chung về quy trình nghiên cứu."
            
            prompt = self.prompts.ANALYZE_QUERY.format(query=enhanced_query)
            
            logger.info(f"Gửi prompt phân tích đến LLM: {prompt[:100]}...")
            response = await self.llm_service.generate(prompt)
            logger.info(f"Nhận phản hồi từ LLM: {response[:100]}...")
            
            # Parse kết quả JSON
            try:
                analysis = json.loads(response)
                logger.info(f"Phân tích JSON thành công: {json.dumps(analysis, ensure_ascii=False)}")
                
                # Kiểm tra xem kết quả phân tích có liên quan đến chủ đề không
                if not self._validate_analysis_relevance(analysis, query):
                    logger.warning(f"Kết quả phân tích không liên quan đến chủ đề, thử phân tích lại")
                    
                    # Tạo lại prompt với hướng dẫn rõ ràng hơn
                    direct_query = f"Phân tích chủ đề: '{query}'. Hãy đảm bảo rằng phân tích tập trung vào chủ đề cụ thể này, KHÔNG phân tích chung chung về quy trình nghiên cứu."
                    
                    prompt = self.prompts.ANALYZE_QUERY.format(query=direct_query)
                    
                    logger.info(f"Gửi lại prompt phân tích đến LLM: {prompt[:100]}...")
                    response = await self.llm_service.generate(prompt)
                    logger.info(f"Nhận phản hồi từ LLM (lần 2): {response[:100]}...")
                    
                    try:
                        analysis = json.loads(response)
                        logger.info(f"Phân tích JSON thành công (lần 2): {json.dumps(analysis, ensure_ascii=False)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Lỗi khi parse JSON (lần 2): {str(e)}")
                        analysis = self._manual_parse_analysis(response)
                        logger.info(f"Phân tích thủ công (lần 2): {json.dumps(analysis, ensure_ascii=False)}")
                
                # Đảm bảo các khóa được chuẩn hóa
                standardized_analysis = {
                    "topic": analysis.get("Topic") or analysis.get("topic", query),
                    "scope": analysis.get("Scope") or analysis.get("scope", "Phân tích toàn diện"),
                    "target_audience": analysis.get("Target Audience") or analysis.get("target_audience", "Người đọc quan tâm đến chủ đề")
                }
                
                return standardized_analysis
                
            except json.JSONDecodeError as e:
                logger.error(f"Lỗi khi parse JSON: {str(e)}")
                logger.error(f"Phản hồi gốc: {response}")
                # Thử phân tích thủ công
                analysis = self._manual_parse_analysis(response)
                logger.info(f"Phân tích thủ công: {json.dumps(analysis, ensure_ascii=False)}")
                
                # Đảm bảo các khóa được chuẩn hóa
                standardized_analysis = {
                    "topic": analysis.get("Topic") or analysis.get("topic", query),
                    "scope": analysis.get("Scope") or analysis.get("scope", "Phân tích toàn diện"),
                    "target_audience": analysis.get("Target Audience") or analysis.get("target_audience", "Người đọc quan tâm đến chủ đề")
                }
                
                return standardized_analysis
                
        except Exception as e:
            logger.error(f"Lỗi khi phân tích yêu cầu: {str(e)}")
            # Trả về phân tích mặc định nếu có lỗi
            return {
                "topic": query,
                "scope": "Phân tích toàn diện",
                "target_audience": "Người đọc quan tâm đến chủ đề"
            }

    def _validate_analysis_relevance(self, analysis: Dict[str, Any], query: str) -> bool:
        """
        Kiểm tra xem kết quả phân tích có liên quan đến chủ đề không
        
        Args:
            analysis: Kết quả phân tích
            query: Câu hỏi gốc
            
        Returns:
            bool: True nếu kết quả phân tích liên quan đến chủ đề, False nếu không
        """
        # Lấy các từ khóa chính từ query
        query_keywords = set(query.lower().split())
        
        # Loại bỏ các từ phổ biến
        common_words = {"là", "và", "của", "trong", "về", "các", "những", "với", "cho", "tại", "bởi", "vì", "nên", "cần", "phải", "có", "không", "ở", "tại"}
        query_keywords = query_keywords - common_words
        
        # Lấy topic, scope và target_audience từ kết quả phân tích
        topic = analysis.get("Topic") or analysis.get("topic", "")
        scope = analysis.get("Scope") or analysis.get("scope", "")
        target_audience = analysis.get("Target Audience") or analysis.get("target_audience", "")
        
        # Kiểm tra xem topic có rỗng hoặc None không
        if not topic or topic.lower() == "none":
            logger.warning(f"Topic rỗng hoặc None trong kết quả phân tích")
            return False
        
        # Kiểm tra xem topic có chứa từ khóa quan trọng từ query không
        important_keywords_found = False
        for keyword in query_keywords:
            if len(keyword) > 3 and keyword in topic.lower():
                important_keywords_found = True
                break
        
        if not important_keywords_found:
            logger.warning(f"Topic '{topic}' không chứa từ khóa quan trọng nào từ query '{query}'")
            return False
        
        # Kiểm tra xem topic có phải là chung chung về nghiên cứu khoa học không
        generic_topics = ["nghiên cứu khoa học", "quy trình nghiên cứu", "phương pháp nghiên cứu", 
                         "cách thức nghiên cứu", "nghiên cứu", "khoa học"]
        
        if any(generic_topic in topic.lower() for generic_topic in generic_topics):
            # Nếu topic chung chung, kiểm tra xem có chứa từ khóa cụ thể từ query không
            if not any(keyword in topic.lower() for keyword in query_keywords if len(keyword) > 3):
                logger.warning(f"Topic '{topic}' có vẻ chung chung và không liên quan đến chủ đề '{query}'")
                return False
        
        # Kiểm tra xem scope có liên quan đến chủ đề không
        if scope and scope.lower() != "none":
            if not any(keyword in scope.lower() for keyword in query_keywords if len(keyword) > 3):
                logger.warning(f"Scope '{scope}' không liên quan đến chủ đề '{query}'")
                # Không return False ở đây vì scope có thể không chứa từ khóa từ query
        
        return True

    def _manual_parse_analysis(self, response: str) -> Dict[str, Any]:
        """
        Phân tích thủ công kết quả từ LLM khi không thể parse JSON
        
        Args:
            response: Phản hồi từ LLM
            
        Returns:
            Dict[str, Any]: Kết quả phân tích
        """
        analysis = {}
        
        # Tìm Topic/Chủ đề
        topic_patterns = ["Topic:", "Chủ đề:", "Topic: ", "Chủ đề: "]
        for pattern in topic_patterns:
            if pattern in response:
                topic_line = response.split(pattern)[1].split("\n")[0].strip()
                analysis["topic"] = topic_line
                break
        
        # Tìm Scope/Phạm vi
        scope_patterns = ["Scope:", "Phạm vi:", "Scope: ", "Phạm vi: "]
        for pattern in scope_patterns:
            if pattern in response:
                scope_line = response.split(pattern)[1].split("\n")[0].strip()
                analysis["scope"] = scope_line
                break
        
        # Tìm Target Audience/Đối tượng độc giả
        audience_patterns = ["Target Audience:", "Đối tượng độc giả:", "Target Audience: ", "Đối tượng độc giả: "]
        for pattern in audience_patterns:
            if pattern in response:
                audience_line = response.split(pattern)[1].split("\n")[0].strip()
                analysis["target_audience"] = audience_line
                break
        
        return analysis

    async def create_outline(self, request: ResearchRequest) -> ResearchOutline:
        """
        Tạo dàn ý cho bài nghiên cứu
        
        Args:
            request: Yêu cầu nghiên cứu
            
        Returns:
            ResearchOutline: Dàn ý cho bài nghiên cứu
        """
        try:
            logger.info("Tạo dàn ý với LLM")
            
            # Chuẩn hóa các khóa trong từ điển analysis
            topic = request.topic or ""
            scope = request.scope or ""
            target_audience = request.target_audience or ""
            
            logger.info(f"Chuẩn hóa các khóa trong từ điển analysis: topic={topic}, scope={scope}, target_audience={target_audience}")
            
            # Kiểm tra xem các giá trị có ý nghĩa hay không
            has_meaningful_topic = topic and topic.strip() and topic.lower() != "none"
            has_meaningful_scope = scope and scope.strip() and scope.lower() != "none"
            has_meaningful_audience = target_audience and target_audience.strip() and target_audience.lower() != "none"
            
            # Tạo query từ thông tin đã phân tích
            if has_meaningful_topic and has_meaningful_scope and has_meaningful_audience:
                # Nếu có đầy đủ thông tin phân tích có ý nghĩa, sử dụng chúng
                query = f"Chủ đề: {topic}\nPhạm vi: {scope}\nĐối tượng đọc: {target_audience}"
                logger.info(f"Tạo query cho prompt tạo dàn ý từ thông tin phân tích: {query}")
            else:
                # Nếu không có đầy đủ thông tin phân tích có ý nghĩa, sử dụng query gốc
                query = request.query
                logger.info(f"Sử dụng query gốc cho prompt tạo dàn ý: {query}")
            
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
            
            # Kiểm tra xem dàn ý có liên quan đến chủ đề không
            if not self._validate_outline_relevance(outline_data, request.query):
                logger.warning(f"Dàn ý không liên quan đến chủ đề, thử tạo lại với query gốc")
                
                # Tạo lại dàn ý với query gốc và hướng dẫn rõ ràng hơn
                direct_query = request.query
                
                prompt = self.prompts.CREATE_OUTLINE.format(
                    query=direct_query
                )
                
                logger.info(f"Gửi lại prompt tạo dàn ý đến LLM: {prompt[:100]}...")
                response = await self.llm_service.generate(prompt)
                logger.info(f"Nhận phản hồi từ LLM: {response[:100]}...")
                
                try:
                    outline_data = json.loads(response)
                    logger.info(f"Phân tích JSON thành công (lần 2): {json.dumps(outline_data, ensure_ascii=False)}")
                except json.JSONDecodeError as e:
                    logger.error(f"Lỗi khi parse JSON (lần 2): {str(e)}")
                    outline_data = self._manual_parse_outline(response)
                    logger.info(f"Phân tích thủ công (lần 2): {json.dumps(outline_data, ensure_ascii=False)}")
            
            # Tạo outline object
            outline = ResearchOutline(
                title=outline_data.get("title", "Nghiên cứu về " + request.query),
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

    def _validate_outline_relevance(self, outline_data: Dict[str, Any], query: str) -> bool:
        """
        Kiểm tra xem dàn ý có liên quan đến chủ đề không
        
        Args:
            outline_data: Dữ liệu dàn ý
            query: Câu hỏi gốc
            
        Returns:
            bool: True nếu dàn ý liên quan đến chủ đề, False nếu không
        """
        # Lấy các từ khóa chính từ query
        query_keywords = set(query.lower().split())
        
        # Loại bỏ các từ phổ biến
        common_words = {"là", "và", "của", "trong", "về", "các", "những", "với", "cho", "tại", "bởi", "vì", "nên", "cần", "phải", "có", "không", "ở", "tại"}
        query_keywords = query_keywords - common_words
        
        # Kiểm tra xem có ít nhất một từ khóa xuất hiện trong các tiêu đề phần
        sections = outline_data.get("researchSections", [])
        if not sections:
            logger.warning("Dàn ý không có phần nào")
            return False
        
        # Danh sách các tiêu đề chung chung về nghiên cứu khoa học
        generic_research_titles = [
            "giới thiệu", "phần nghiên cứu", "phương pháp nghiên cứu", "kết quả nghiên cứu", 
            "phân tích và đánh giá", "ứng dụng thực tế", "kết luận", "tổng quan nghiên cứu",
            "tổng quan", "phương pháp", "kết quả", "thảo luận", "kết luận và đề xuất",
            "giới thiệu chung", "phân tích và thảo luận", "các phương pháp nghiên cứu",
            "kết quả và đánh giá", "phần 1", "phần 2", "phần 3", "phần 4", "phần 5"
        ]
        
        # Đếm số phần có tiêu đề chung chung
        generic_title_count = 0
        for section in sections:
            title = section.get("title", "").lower()
            # Loại bỏ các tiền tố như "Phần 1: ", "I. ", v.v.
            cleaned_title = re.sub(r'^(phần \d+:|[ivx]+\.|[\d]+\.)\s*', '', title).strip()
            if cleaned_title in generic_research_titles:
                generic_title_count += 1
        
        # Nếu tất cả các phần đều có tiêu đề chung chung
        if generic_title_count == len(sections):
            logger.warning(f"Tất cả các phần đều có tiêu đề chung chung, không liên quan đến chủ đề '{query}'")
            return False
        
        # Kiểm tra xem có ít nhất một phần có tiêu đề hoặc mô tả liên quan trực tiếp đến chủ đề
        topic_related_section_found = False
        for section in sections:
            title = section.get("title", "").lower()
            description = section.get("description", "").lower()
            
            # Tìm các từ khóa quan trọng từ query (từ có độ dài > 3)
            for keyword in query_keywords:
                if len(keyword) > 3 and (keyword in title or keyword in description):
                    topic_related_section_found = True
                    break
            
            if topic_related_section_found:
                break
        
        if not topic_related_section_found:
            logger.warning(f"Không tìm thấy phần nào liên quan trực tiếp đến chủ đề '{query}'")
            return False
        
        return True

    def _manual_parse_outline(self, response: str) -> Dict[str, Any]:
        """
        Phân tích thủ công kết quả tạo dàn ý từ LLM khi không thể parse JSON
        
        Args:
            response: Phản hồi từ LLM
            
        Returns:
            Dict[str, Any]: Dữ liệu dàn ý
        """
        outline_data = {"researchSections": []}
        
        # Tìm các phần trong dàn ý
        lines = response.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Bỏ qua các dòng trống
            if not line:
                continue
            
            # Tìm tiêu đề phần
            if line.startswith("##") or line.startswith("- ") or line.startswith("* ") or line.startswith("1. ") or line.startswith("2. "):
                # Nếu đã có phần hiện tại, thêm vào danh sách
                if current_section:
                    outline_data["researchSections"].append(current_section)
                
                # Tạo phần mới
                title = line.lstrip("#-*0123456789. ").strip()
                current_section = {"title": title, "description": ""}
            
            # Nếu không phải tiêu đề và đã có phần hiện tại, thêm vào mô tả
            elif current_section:
                if current_section["description"]:
                    current_section["description"] += " " + line
                else:
                    current_section["description"] = line
        
        # Thêm phần cuối cùng nếu có
        if current_section:
            outline_data["researchSections"].append(current_section)
        
        # Nếu không tìm thấy phần nào, tạo các phần mặc định
        if not outline_data["researchSections"]:
            outline_data["researchSections"] = [
                {"title": "Giới thiệu", "description": "Giới thiệu về chủ đề nghiên cứu"},
                {"title": "Phân tích", "description": "Phân tích các khía cạnh của chủ đề"},
                {"title": "Kết luận", "description": "Kết luận và đề xuất"}
            ]
        
        return outline_data 