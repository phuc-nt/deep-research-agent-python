from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ResearchStatus(str, Enum):
    """Status of a research task"""
    PENDING = "pending"          # Đang chờ xử lý
    ANALYZING = "analyzing"      # Đang phân tích yêu cầu
    OUTLINING = "outlining"      # Đang tạo dàn ý
    RESEARCHING = "researching"  # Đang nghiên cứu
    EDITING = "editing"          # Đang chỉnh sửa
    COMPLETED = "completed"      # Đã hoàn thành
    FAILED = "failed"           # Thất bại

class ResearchRequest(BaseModel):
    """Input for creating a research task"""
    query: str = Field(..., description="Yêu cầu nghiên cứu")
    topic: Optional[str] = Field(None, description="Chủ đề nghiên cứu (tùy chọn)")
    scope: Optional[str] = Field(None, description="Phạm vi nghiên cứu (tùy chọn)")
    target_audience: Optional[str] = Field(None, description="Đối tượng độc giả (tùy chọn)")
    task_id: Optional[str] = Field(None, description="ID của task (được sử dụng nội bộ)")

class EditRequest(BaseModel):
    """Input for editing a research task"""
    task_id: str = Field(..., description="ID của research task cần chỉnh sửa")

class ResearchSection(BaseModel):
    """A section in the research paper"""
    title: str = Field(..., description="Tiêu đề phần")
    description: Optional[str] = Field(None, description="Mô tả phần")
    content: Optional[str] = Field(None, description="Nội dung chi tiết")
    sources: List[str] = Field(default_factory=list)

class ResearchOutline(BaseModel):
    """Outline for a research paper"""
    sections: List[ResearchSection] = Field(..., description="Danh sách các phần")
    task_id: Optional[str] = Field(None, description="ID của task (được sử dụng nội bộ)")

class ProgressInfo(BaseModel):
    """Information about the progress of the research task"""
    phase: str  # outlining, researching, editing, completed, failed
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_section: Optional[int] = None
    total_sections: Optional[int] = None
    completed_sections: Optional[int] = None
    time_taken: Optional[str] = None
    content_length: Optional[int] = None
    sources_count: Optional[int] = None
    outline_sections_count: Optional[int] = None
    total_time: Optional[str] = None

class ResearchResult(BaseModel):
    """Result of a research task"""
    title: str = Field(..., description="Tiêu đề bài nghiên cứu")
    content: str = Field(..., description="Nội dung bài nghiên cứu")
    sections: List[ResearchSection] = Field(..., description="Các phần của bài nghiên cứu")
    sources: List[str] = Field(..., description="Danh sách nguồn tham khảo")

class ResearchError(BaseModel):
    """Error information for a research task"""
    message: str = Field(..., description="Thông báo lỗi")
    details: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi")
    phase: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ResearchCostInfo(BaseModel):
    """Information about research cost"""
    total_cost_usd: float = 0.0
    llm_cost_usd: float = 0.0
    search_cost_usd: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    model_breakdown: Dict[str, Dict] = Field(default_factory=dict)
    execution_time_seconds: Dict[str, float] = Field(default_factory=dict)
    cost_report_url: Optional[str] = None

class ResearchResponse(BaseModel):
    """Response for a research task"""
    id: str = Field(..., description="ID của research task")
    status: ResearchStatus = Field(..., description="Trạng thái hiện tại")
    request: ResearchRequest = Field(..., description="Yêu cầu nghiên cứu gốc")
    outline: Optional[ResearchOutline] = Field(None, description="Dàn ý nghiên cứu")
    sections: Optional[List[ResearchSection]] = Field(None, description="Các phần đã nghiên cứu")
    result: Optional[ResearchResult] = Field(None, description="Kết quả nghiên cứu")
    error: Optional[ResearchError] = Field(None, description="Thông tin lỗi nếu có")
    github_url: Optional[str] = Field(None, description="URL của repository trên GitHub")
    progress_info: Dict[str, Any] = Field(default_factory=dict)
    cost_info: Optional[ResearchCostInfo] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm tạo")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm cập nhật cuối") 