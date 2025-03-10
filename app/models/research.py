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
    query: str = Field(
        ..., 
        description="Yêu cầu nghiên cứu. Cần mô tả rõ nội dung cần nghiên cứu. Ví dụ: 'Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục'"
    )
    topic: Optional[str] = Field(
        None, 
        description="Chủ đề nghiên cứu (tùy chọn). Nếu không cung cấp, hệ thống sẽ tự động xác định dựa trên query. Ví dụ: 'Trí tuệ nhân tạo trong giáo dục'"
    )
    scope: Optional[str] = Field(
        None, 
        description="Phạm vi nghiên cứu (tùy chọn). Giới hạn phạm vi để tập trung vào các khía cạnh cụ thể. Ví dụ: 'Tổng quan và ứng dụng thực tế'"
    )
    target_audience: Optional[str] = Field(
        None, 
        description="Đối tượng độc giả (tùy chọn). Xác định đối tượng để điều chỉnh ngôn ngữ và nội dung phù hợp. Ví dụ: 'Giáo viên và nhà quản lý giáo dục'"
    )
    task_id: Optional[str] = Field(
        None, 
        description="ID của task (được sử dụng nội bộ). Thường được tạo tự động, không cần cung cấp."
    )

class EditRequest(BaseModel):
    """Input for editing a research task"""
    research_id: str = Field(
        ..., 
        description="ID của research task cần chỉnh sửa. Được cung cấp sau khi tạo research task."
    )

class ResearchSection(BaseModel):
    """A section in the research paper"""
    title: str = Field(..., description="Tiêu đề phần")
    description: Optional[str] = Field(None, description="Mô tả phần")
    content: Optional[str] = Field(None, description="Nội dung chi tiết")
    sources: Optional[List[str]] = Field(default_factory=list, description="Các nguồn tham khảo cho phần này")

class ResearchOutline(BaseModel):
    """Outline for a research paper"""
    sections: List[ResearchSection] = Field(..., description="Danh sách các phần")
    task_id: Optional[str] = Field(None, description="ID của task (được sử dụng nội bộ)")

class ProgressInfo(BaseModel):
    """Information about the progress of the research task"""
    phase: str = Field(..., description="Giai đoạn hiện tại: outlining, researching, editing, completed, failed")
    message: str = Field(..., description="Thông báo về tiến độ hiện tại")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Thời điểm cập nhật")
    current_section: Optional[int] = Field(None, description="Phần đang được xử lý (bắt đầu từ 1)")
    total_sections: Optional[int] = Field(None, description="Tổng số phần cần xử lý")
    completed_sections: Optional[int] = Field(None, description="Số phần đã hoàn thành")
    time_taken: Optional[str] = Field(None, description="Thời gian đã sử dụng (định dạng: '302.5 giây')")
    content_length: Optional[int] = Field(None, description="Độ dài nội dung (số ký tự)")
    sources_count: Optional[int] = Field(None, description="Số lượng nguồn tham khảo")
    outline_sections_count: Optional[int] = Field(None, description="Số lượng phần trong dàn ý")
    total_time: Optional[str] = Field(None, description="Tổng thời gian thực hiện (định dạng: '305.3 giây')")

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
    phase: Optional[str] = Field(None, description="Giai đoạn xảy ra lỗi: analyzing, outlining, researching, editing")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Thời điểm xảy ra lỗi")

class ResearchCostInfo(BaseModel):
    """Information about research cost"""
    total_cost_usd: float = Field(0.0, description="Tổng chi phí (USD)")
    llm_cost_usd: float = Field(0.0, description="Chi phí sử dụng LLM (USD)")
    search_cost_usd: float = Field(0.0, description="Chi phí sử dụng Search API (USD)")
    total_tokens: int = Field(0, description="Tổng số tokens đã sử dụng")
    total_requests: int = Field(0, description="Tổng số requests")
    model_breakdown: Dict[str, Dict] = Field(default_factory=dict, description="Chi tiết chi phí theo từng model")
    execution_time_seconds: Dict[str, float] = Field(default_factory=dict, description="Thời gian thực thi cho từng giai đoạn (giây)")
    cost_report_url: Optional[str] = Field(None, description="URL báo cáo chi phí chi tiết (nếu có)")

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
    progress_info: Dict[str, Any] = Field(default_factory=dict, description="Thông tin chi tiết về tiến độ nghiên cứu")
    cost_info: Optional[ResearchCostInfo] = Field(None, description="Thông tin chi tiết về chi phí thực hiện")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm tạo")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm cập nhật cuối") 