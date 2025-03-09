from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class LLMCost(BaseModel):
    """Chi phí cho một cuộc gọi LLM API"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    prompt: Optional[str] = None
    duration_ms: Optional[int] = None
    endpoint: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    purpose: Optional[str] = None

class SearchCost(BaseModel):
    """Chi phí cho một cuộc gọi Search API"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    provider: str
    query: Optional[str] = None
    cost_usd: float
    duration_ms: Optional[int] = None
    num_results: Optional[int] = None
    request_id: Optional[str] = Field(default_factory=lambda: str(datetime.now().timestamp()))
    purpose: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

class PhaseTimingInfo(BaseModel):
    """Thông tin timing của một phase"""
    phase_name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str = "pending"  # pending, completed, failed

class SectionTimingInfo(BaseModel):
    """Thông tin timing của một section"""
    section_id: str
    section_title: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str = "pending"  # pending, completed, failed

class CostSummary(BaseModel):
    """Tổng hợp chi phí cho một research task"""
    total_cost_usd: float = 0.0
    llm_cost_usd: float = 0.0
    search_cost_usd: float = 0.0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_llm_requests: int = 0
    total_search_requests: int = 0
    model_breakdown: Dict[str, Dict] = Field(default_factory=dict)
    provider_breakdown: Dict[str, Dict] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

class ResearchCostMonitoring(BaseModel):
    """Theo dõi chi phí cho một research task"""
    task_id: str
    llm_requests: List[LLMCost] = Field(default_factory=list)
    search_requests: List[SearchCost] = Field(default_factory=list)
    phase_timings: List[PhaseTimingInfo] = Field(default_factory=list)
    section_timings: List[SectionTimingInfo] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    summary: Optional[CostSummary] = None

    def add_llm_cost(self, cost: LLMCost) -> None:
        """Thêm một LLM cost mới"""
        self.llm_requests.append(cost)
        self.updated_at = datetime.now().isoformat()
        self._update_summary()

    def add_search_cost(self, cost: SearchCost) -> None:
        """Thêm một Search cost mới"""
        self.search_requests.append(cost)
        self.updated_at = datetime.now().isoformat()
        self._update_summary()

    def start_phase(self, phase_name: str) -> str:
        """Bắt đầu timing cho một phase"""
        start_time = datetime.now().isoformat()
        
        # Kiểm tra xem phase đã tồn tại chưa
        for phase in self.phase_timings:
            if phase.phase_name == phase_name:
                # Nếu đã tồn tại, cập nhật
                phase.start_time = start_time
                phase.end_time = None
                phase.duration_seconds = None
                phase.status = "pending"
                return phase_name
        
        # Nếu chưa tồn tại, thêm mới
        self.phase_timings.append(PhaseTimingInfo(
            phase_name=phase_name,
            start_time=start_time,
            status="pending"
        ))
        
        self.updated_at = start_time
        return phase_name

    def end_phase(self, phase_name: str, status: str = "completed") -> None:
        """Kết thúc timing cho một phase"""
        end_time = datetime.now().isoformat()
        end_time_dt = datetime.now()
        
        # Tìm phase cần cập nhật
        for phase in self.phase_timings:
            if phase.phase_name == phase_name:
                # Nếu không có start_time, đặt là end_time
                if not phase.start_time:
                    phase.start_time = end_time
                
                # Tính thời gian
                start_time_dt = datetime.fromisoformat(phase.start_time)
                duration_seconds = (end_time_dt - start_time_dt).total_seconds()
                
                # Cập nhật thông tin
                phase.end_time = end_time
                phase.duration_seconds = duration_seconds
                phase.status = status
                break
        
        self.updated_at = end_time

    def start_section(self, section_id: str, section_title: str) -> str:
        """Bắt đầu timing cho một section"""
        start_time = datetime.now().isoformat()
        
        # Kiểm tra xem section đã tồn tại chưa
        for section in self.section_timings:
            if section.section_id == section_id:
                # Nếu đã tồn tại, cập nhật
                section.start_time = start_time
                section.end_time = None
                section.duration_seconds = None
                section.status = "pending"
                return section_id
        
        # Nếu chưa tồn tại, thêm mới
        self.section_timings.append(SectionTimingInfo(
            section_id=section_id,
            section_title=section_title,
            start_time=start_time,
            status="pending"
        ))
        
        self.updated_at = start_time
        return section_id

    def end_section(self, section_id: str, status: str = "completed") -> None:
        """Kết thúc timing cho một section"""
        end_time = datetime.now().isoformat()
        end_time_dt = datetime.now()
        
        # Tìm section cần cập nhật
        for section in self.section_timings:
            if section.section_id == section_id:
                # Nếu không có start_time, đặt là end_time
                if not section.start_time:
                    section.start_time = end_time
                
                # Tính thời gian
                start_time_dt = datetime.fromisoformat(section.start_time)
                duration_seconds = (end_time_dt - start_time_dt).total_seconds()
                
                # Cập nhật thông tin
                section.end_time = end_time
                section.duration_seconds = duration_seconds
                section.status = status
                break
        
        self.updated_at = end_time

    def _update_summary(self) -> CostSummary:
        """Cập nhật tổng hợp chi phí"""
        total_llm_cost = sum(request.cost_usd for request in self.llm_requests)
        total_search_cost = sum(request.cost_usd for request in self.search_requests)
        total_cost = total_llm_cost + total_search_cost
        
        # Tính tổng token từ LLM requests
        total_input_tokens = sum(request.input_tokens for request in self.llm_requests)
        total_output_tokens = sum(request.output_tokens for request in self.llm_requests)
        
        # Thêm token từ search requests nếu có
        for request in self.search_requests:
            if hasattr(request, 'input_tokens') and hasattr(request, 'output_tokens') and request.input_tokens and request.output_tokens:
                total_input_tokens += request.input_tokens
                total_output_tokens += request.output_tokens
        
        total_tokens = total_input_tokens + total_output_tokens
        
        # Tính toán breakdown theo model
        model_breakdown = {}
        for request in self.llm_requests:
            model = request.model
            if model not in model_breakdown:
                model_breakdown[model] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0
                }
            
            model_breakdown[model]["requests"] += 1
            model_breakdown[model]["input_tokens"] += request.input_tokens
            model_breakdown[model]["output_tokens"] += request.output_tokens
            model_breakdown[model]["cost_usd"] += request.cost_usd
        
        # Tính toán breakdown theo provider
        provider_breakdown = {}
        for request in self.search_requests:
            provider = request.provider
            if provider not in provider_breakdown:
                provider_breakdown[provider] = {
                    "requests": 0,
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            
            provider_breakdown[provider]["requests"] += 1
            provider_breakdown[provider]["cost_usd"] += request.cost_usd
            
            # Thêm thông tin token nếu có
            if hasattr(request, 'input_tokens') and hasattr(request, 'output_tokens') and request.input_tokens and request.output_tokens:
                provider_breakdown[provider]["input_tokens"] += request.input_tokens
                provider_breakdown[provider]["output_tokens"] += request.output_tokens
        
        # Tạo summary
        summary = CostSummary(
            total_cost_usd=total_cost,
            llm_cost_usd=total_llm_cost,
            search_cost_usd=total_search_cost,
            total_tokens=total_tokens,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_llm_requests=len(self.llm_requests),
            total_search_requests=len(self.search_requests),
            model_breakdown=model_breakdown,
            provider_breakdown=provider_breakdown,
            last_updated=datetime.now().isoformat()
        )
        
        self.summary = summary
        return summary 