from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

class ResearchRequest(BaseModel):
    """Model cho yêu cầu nghiên cứu"""
    query: str
    topic: Optional[str] = None
    scope: Optional[str] = None
    target_audience: Optional[str] = None

class ResearchSection(BaseModel):
    """Model cho một phần của nghiên cứu"""
    title: str
    description: str
    content: Optional[str] = None
    sources: Optional[List[str]] = None

class ResearchOutline(BaseModel):
    """Model cho dàn ý nghiên cứu"""
    sections: List[ResearchSection]

class ResearchResult(BaseModel):
    """Model cho kết quả nghiên cứu hoàn chỉnh"""
    title: str
    content: str
    sections: List[ResearchSection]
    sources: List[str]

class BaseResearchPhase(ABC):
    """Base class cho các phase trong quy trình nghiên cứu"""
    
    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Dict[str, Any]) -> Any:
        """
        Thực thi phase trong quy trình nghiên cứu
        
        Args:
            *args: Các tham số vị trí
            **kwargs: Các tham số từ khóa
            
        Returns:
            Any: Kết quả của phase
        """
        pass

class BasePreparePhase(BaseResearchPhase):
    """Phase chuẩn bị: Phân tích yêu cầu và tạo dàn ý"""
    
    @abstractmethod
    async def analyze_query(self, request: ResearchRequest) -> Dict[str, Any]:
        """
        Phân tích yêu cầu nghiên cứu để xác định các thông tin quan trọng
        
        Args:
            request: Yêu cầu nghiên cứu
            
        Returns:
            Dict[str, Any]: Kết quả phân tích bao gồm topic, scope, target_audience
        """
        pass
    
    @abstractmethod
    async def create_outline(self, analysis: Dict[str, Any]) -> ResearchOutline:
        """
        Tạo dàn ý cho bài nghiên cứu dựa trên kết quả phân tích
        
        Args:
            analysis: Kết quả phân tích từ analyze_query
            
        Returns:
            ResearchOutline: Dàn ý cho bài nghiên cứu
        """
        pass

class BaseResearchPhase(BaseResearchPhase):
    """Phase nghiên cứu: Thực hiện nghiên cứu cho từng phần"""
    
    @abstractmethod
    async def research_section(self, section: ResearchSection, context: Dict[str, Any]) -> ResearchSection:
        """
        Thực hiện nghiên cứu cho một phần cụ thể
        
        Args:
            section: Phần cần nghiên cứu
            context: Thông tin context (topic, scope, target_audience, etc.)
            
        Returns:
            ResearchSection: Phần đã được nghiên cứu với nội dung đầy đủ
        """
        pass

class BaseEditPhase(BaseResearchPhase):
    """Phase chỉnh sửa: Hoàn thiện bài nghiên cứu"""
    
    @abstractmethod
    async def edit_content(self, sections: List[ResearchSection], context: Dict[str, Any]) -> str:
        """
        Chỉnh sửa và kết hợp các phần thành bài nghiên cứu hoàn chỉnh
        
        Args:
            sections: Danh sách các phần đã nghiên cứu
            context: Thông tin context (topic, scope, target_audience, etc.)
            
        Returns:
            str: Nội dung bài nghiên cứu hoàn chỉnh
        """
        pass
    
    @abstractmethod
    async def create_title(self, content: str, context: Dict[str, Any]) -> str:
        """
        Tạo tiêu đề cho bài nghiên cứu
        
        Args:
            content: Nội dung bài nghiên cứu
            context: Thông tin context (topic, scope, target_audience, etc.)
            
        Returns:
            str: Tiêu đề bài nghiên cứu
        """
        pass 