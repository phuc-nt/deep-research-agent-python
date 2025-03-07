from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ResearchStatus(str, Enum):
    """Trạng thái của quá trình nghiên cứu"""
    PENDING = "pending"          # Đang chờ xử lý
    ANALYZING = "analyzing"      # Đang phân tích yêu cầu
    OUTLINING = "outlining"      # Đang tạo dàn ý
    RESEARCHING = "researching"  # Đang nghiên cứu
    EDITING = "editing"          # Đang chỉnh sửa
    COMPLETED = "completed"      # Đã hoàn thành
    FAILED = "failed"           # Thất bại

class ResearchRequest(BaseModel):
    """Yêu cầu nghiên cứu"""
    query: str = Field(..., description="Yêu cầu nghiên cứu")
    topic: Optional[str] = Field(None, description="Chủ đề nghiên cứu (tùy chọn)")
    scope: Optional[str] = Field(None, description="Phạm vi nghiên cứu (tùy chọn)")
    target_audience: Optional[str] = Field(None, description="Đối tượng độc giả (tùy chọn)")

class ResearchSection(BaseModel):
    """Một phần của bài nghiên cứu"""
    title: str = Field(..., description="Tiêu đề phần")
    description: str = Field(..., description="Mô tả phần")
    content: Optional[str] = Field(None, description="Nội dung chi tiết")

class ResearchOutline(BaseModel):
    """Dàn ý nghiên cứu"""
    sections: List[ResearchSection] = Field(..., description="Danh sách các phần")

class ResearchResult(BaseModel):
    """Kết quả nghiên cứu hoàn chỉnh"""
    title: str = Field(..., description="Tiêu đề bài nghiên cứu")
    content: str = Field(..., description="Nội dung bài nghiên cứu")
    sections: List[ResearchSection] = Field(..., description="Các phần của bài nghiên cứu")
    sources: List[str] = Field(..., description="Danh sách nguồn tham khảo")

class ResearchError(BaseModel):
    """Thông tin lỗi"""
    message: str = Field(..., description="Thông báo lỗi")
    details: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi")

class ResearchResponse(BaseModel):
    """Phản hồi cho yêu cầu nghiên cứu"""
    id: str = Field(..., description="ID của research task")
    status: ResearchStatus = Field(..., description="Trạng thái hiện tại")
    request: ResearchRequest = Field(..., description="Yêu cầu nghiên cứu gốc")
    outline: Optional[ResearchOutline] = Field(None, description="Dàn ý nghiên cứu")
    result: Optional[ResearchResult] = Field(None, description="Kết quả nghiên cứu")
    error: Optional[ResearchError] = Field(None, description="Thông tin lỗi nếu có")
    github_url: Optional[str] = Field(None, description="URL của repository trên GitHub")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm tạo")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm cập nhật cuối") 