import json
import re
from typing import Any, Dict

from app.core.config import get_prepare_prompts
from app.core.exceptions import PrepareError
from app.core.factory import get_service_factory
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
        service_factory = get_service_factory()
        self.llm_service = service_factory.create_llm_service_for_phase("prepare")
        self.search_service = None
        # Khởi tạo cost monitoring service
        self.cost_service = service_factory.get_cost_monitoring_service()
    
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
            # Khởi tạo search service tại đây để có thể await
            service_factory = get_service_factory()
            self.search_service = await service_factory.create_search_service()
            
            logger.info(f"=== BẮT ĐẦU PHASE CHUẨN BỊ ===")
            logger.info(f"Bắt đầu chuẩn bị nghiên cứu cho topic: {request.topic}")
            
            # Lấy task_id từ request nếu có
            task_id = request.task_id if hasattr(request, 'task_id') else None
            
            # Bắt đầu ghi nhận thời gian cho phase phân tích
            if task_id:
                self.cost_service.start_phase_timing(task_id, "analyzing")
            
            # Phân tích yêu cầu
            logger.info("Bắt đầu phân tích yêu cầu nghiên cứu...")
            analysis = await self.analyze_query(request.query, task_id)
            logger.info(f"Phân tích yêu cầu thành công: {json.dumps(analysis, ensure_ascii=False)}")
            
            # Kết thúc ghi nhận thời gian cho phase phân tích
            if task_id:
                self.cost_service.end_phase_timing(task_id, "analyzing", "completed")
            
            # Cập nhật request với thông tin phân tích
            updated_request = ResearchRequest(
                query=request.query,
                topic=analysis.get("topic"),
                scope=analysis.get("scope"),
                target_audience=analysis.get("target_audience")
            )
            
            # Bắt đầu ghi nhận thời gian cho phase tạo dàn ý
            if task_id:
                self.cost_service.start_phase_timing(task_id, "outlining")
            
            # Tạo dàn ý
            logger.info("Bắt đầu tạo dàn ý nghiên cứu...")
            outline = await self.create_outline(updated_request, task_id)
            logger.info(f"Tạo dàn ý thành công với {len(outline.sections)} phần")
            for i, section in enumerate(outline.sections):
                logger.info(f"  Phần {i+1}: {section.title} - {section.description}")
            
            # Kết thúc ghi nhận thời gian cho phase tạo dàn ý
            if task_id:
                self.cost_service.end_phase_timing(task_id, "outlining", "completed")
                # Lưu dữ liệu monitoring
                await self.cost_service.save_monitoring_data(task_id)
                
                # Gán task_id cho outline để sử dụng trong các phase tiếp theo
                outline.task_id = task_id
            
            logger.info("=== KẾT THÚC PHASE CHUẨN BỊ - THÀNH CÔNG ===")
            return outline
            
        except Exception as e:
            logger.error(f"=== KẾT THÚC PHASE CHUẨN BỊ - THẤT BẠI ===")
            logger.error(f"Lỗi trong quá trình chuẩn bị: {str(e)}")
            raise PrepareError(
                "Lỗi trong quá trình chuẩn bị",
                details={"error": str(e)}
            )
    
    async def analyze_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """
        Phân tích yêu cầu nghiên cứu
        
        Args:
            query: Nội dung câu hỏi
            task_id: ID của task để ghi nhận chi phí
            
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
            
            # Tạo prompt
            prompt = self.prompts.ANALYZE_QUERY.format(query=query)
            
            # Gọi LLM để phân tích
            logger.info(f"Gửi prompt phân tích đến LLM: {prompt[:100]}...")
            response = await self.llm_service.generate(
                prompt=prompt,
                task_id=task_id,
                purpose="analyze_query"
            )
            logger.info(f"Nhận phản hồi từ LLM: {response[:100]}...")
            
            # Phân tích kết quả
            try:
                # Thử parse JSON
                analysis = json.loads(response)
                logger.info("Đã parse JSON thành công")
                
                # Chuẩn hóa keys
                if "Topic" in analysis and "topic" not in analysis:
                    analysis["topic"] = analysis["Topic"]
                if "Scope" in analysis and "scope" not in analysis:
                    analysis["scope"] = analysis["Scope"]
                if "Target Audience" in analysis and "target_audience" not in analysis:
                    analysis["target_audience"] = analysis["Target Audience"]
                
                # Kiểm tra tính hợp lệ
                if not self._validate_analysis_relevance(analysis, query):
                    logger.warning("Kết quả phân tích không liên quan đến yêu cầu, thử phân tích thủ công")
                    analysis = self._manual_parse_analysis(response)
            except json.JSONDecodeError:
                logger.warning("Không thể parse JSON, thử phân tích thủ công")
                analysis = self._manual_parse_analysis(response)
            
            # Đảm bảo có đủ các trường cần thiết
            if "topic" not in analysis or not analysis["topic"]:
                analysis["topic"] = query
            if "scope" not in analysis or not analysis["scope"]:
                analysis["scope"] = "Phân tích toàn diện về chủ đề"
            if "target_audience" not in analysis or not analysis["target_audience"]:
                analysis["target_audience"] = "Người đọc quan tâm đến chủ đề"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Lỗi khi phân tích yêu cầu: {str(e)}")
            # Trả về phân tích mặc định nếu có lỗi
            return {
                "topic": query,
                "scope": "Phân tích toàn diện về chủ đề",
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

    async def create_outline(self, request: ResearchRequest, task_id: str = None) -> ResearchOutline:
        """
        Tạo dàn ý cho bài nghiên cứu
        
        Args:
            request: Yêu cầu nghiên cứu
            task_id: ID của task để ghi nhận chi phí
            
        Returns:
            ResearchOutline: Dàn ý cho bài nghiên cứu
        """
        try:
            logger.info("Tạo dàn ý với LLM")
            
            # Tìm kiếm thông tin liên quan
            search_query = f"{request.topic} {request.scope}"
            logger.info(f"Tìm kiếm thông tin liên quan với query: {search_query}")
            
            # Gọi search API
            search_results = await self.search_service.search(
                query=search_query,
                task_id=task_id,
                purpose="search_for_outline"
            )
            logger.info(f"Tìm thấy {len(search_results)} kết quả liên quan")
            
            # Tạo prompt
            prompt = self.prompts.CREATE_OUTLINE.format(
                topic=request.topic,
                scope=request.scope,
                target_audience=request.target_audience,
                search_results=json.dumps(search_results[:5], ensure_ascii=False)
            )
            
            # Gọi LLM để tạo dàn ý
            logger.info(f"Gửi prompt tạo dàn ý đến LLM: {prompt[:100]}...")
            response = await self.llm_service.generate(
                prompt=prompt,
                task_id=task_id,
                purpose="create_outline"
            )
            logger.info(f"Nhận phản hồi từ LLM: {response[:100]}...")
            
            # Phân tích kết quả
            try:
                # Thử parse JSON
                outline_data = json.loads(response)
                logger.info("Đã parse JSON thành công")
                
                # Kiểm tra tính hợp lệ
                if not self._validate_outline_relevance(outline_data, request.query):
                    logger.warning("Dàn ý không liên quan đến yêu cầu, thử phân tích thủ công")
                    outline_data = self._manual_parse_outline(response)
            except json.JSONDecodeError:
                logger.warning("Không thể parse JSON, thử phân tích thủ công")
                outline_data = self._manual_parse_outline(response)
            
            # Tạo đối tượng ResearchOutline
            sections = []
            for section_data in outline_data.get("sections", []):
                section = ResearchSection(
                    title=section_data.get("title", ""),
                    description=section_data.get("description", "")
                )
                sections.append(section)
            
            # Đảm bảo có ít nhất một phần
            if not sections:
                logger.warning("Không có phần nào trong dàn ý, tạo phần mặc định")
                sections = [
                    ResearchSection(
                        title="Giới thiệu",
                        description="Giới thiệu về chủ đề nghiên cứu"
                    ),
                    ResearchSection(
                        title="Phân tích",
                        description="Phân tích các khía cạnh của chủ đề"
                    ),
                    ResearchSection(
                        title="Kết luận",
                        description="Kết luận và đề xuất"
                    )
                ]
            
            outline = ResearchOutline(sections=sections)
            return outline
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo dàn ý: {str(e)}")
            # Tạo dàn ý mặc định nếu có lỗi
            sections = [
                ResearchSection(
                    title="Giới thiệu",
                    description="Giới thiệu về chủ đề nghiên cứu"
                ),
                ResearchSection(
                    title="Phân tích",
                    description="Phân tích các khía cạnh của chủ đề"
                ),
                ResearchSection(
                    title="Kết luận",
                    description="Kết luận và đề xuất"
                )
            ]
            return ResearchOutline(sections=sections)

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
        sections = outline_data.get("sections", [])
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
        outline_data = {"sections": []}
        
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
                    outline_data["sections"].append(current_section)
                
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
            outline_data["sections"].append(current_section)
        
        # Nếu không tìm thấy phần nào, tạo các phần mặc định
        if not outline_data["sections"]:
            outline_data["sections"] = [
                {"title": "Giới thiệu", "description": "Giới thiệu về chủ đề nghiên cứu"},
                {"title": "Phân tích", "description": "Phân tích các khía cạnh của chủ đề"},
                {"title": "Kết luận", "description": "Kết luận và đề xuất"}
            ]
        
        return outline_data 