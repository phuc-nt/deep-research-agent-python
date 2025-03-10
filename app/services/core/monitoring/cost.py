import json
import time
import uuid
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
import asyncio
import os

from app.models.cost import (
    ResearchCostMonitoring,
    LLMCost,
    SearchCost,
    CostSummary,
    PhaseTimingInfo,
    SectionTimingInfo
)
from app.models.research import ResearchCostInfo
from app.core.logging import get_logger
from app.services.core.monitoring.custom_pricing import get_custom_pricing

logger = get_logger(__name__)

# Lấy bảng giá tùy chỉnh
MODEL_PRICING, SEARCH_PRICING = get_custom_pricing()

# Bảng giá model - giá trên 1000 token
MODEL_PRICING = {
    # OpenAI models
    "gpt-4o": {"input": 0.003, "output": 0.01},  # Giá trên 1 triệu token là $3 cho input và $10 cho output, nên trên 1000 token là $0.003 và $0.01
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # Giá trên 1 triệu token là $0.15 cho input và $0.6 cho output, nên trên 1000 token là $0.00015 và $0.0006
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-32k": {"input": 0.06, "output": 0.12},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    
    # Anthropic models
    "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},  # Giá mới nhất cho Claude 3.5 Sonnet
    "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},  # Giá trên 1 triệu token là $3 cho input và $15 cho output, nên trên 1000 token là $0.003 và $0.015
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-2": {"input": 0.008, "output": 0.024},
    "claude-instant": {"input": 0.0008, "output": 0.0024},
    
    # Perplexity models
    "llama-3.1-sonar-small-128k-online": {"input": 0.0002, "output": 0.0002},  # Giá trên 1 triệu token là $0.2 cho input và $0.2 cho output, nên trên 1000 token là $0.0002
}

# Giá cho search providers - giá trên mỗi request
SEARCH_PRICING = {
    "google": 0.01,  # Giả định 1 cent mỗi request
    "perplexity": 0.005,  # Giả định 0.5 cent mỗi request
    "custom": 0.0  # Không tính phí
}


class CostMonitoringService:
    """Service để theo dõi và quản lý chi phí cho research tasks"""
    
    def __init__(self, storage_service=None):
        self.storage_service = storage_service
        self._cost_data: Dict[str, ResearchCostMonitoring] = {}
        self.model_pricing = MODEL_PRICING.copy()
        self.search_pricing = SEARCH_PRICING.copy()
    
    def initialize_monitoring(self, task_id: str) -> ResearchCostMonitoring:
        """Khởi tạo monitoring cho một task mới"""
        if task_id in self._cost_data:
            logger.info(f"Cost monitoring đã tồn tại cho task {task_id}, trả về instance hiện có")
            return self._cost_data[task_id]
        
        logger.info(f"Khởi tạo cost monitoring mới cho task {task_id}")
        cost_monitoring = ResearchCostMonitoring(task_id=task_id)
        self._cost_data[task_id] = cost_monitoring
        
        # Lưu dữ liệu ban đầu
        if self.storage_service:
            self._save_cost_data(task_id)
        
        return cost_monitoring
    
    async def load_monitoring(self, task_id: str) -> Optional[ResearchCostMonitoring]:
        """Tải dữ liệu monitoring cho một task đã tồn tại"""
        if task_id in self._cost_data:
            return self._cost_data[task_id]
        
        if not self.storage_service:
            logger.warning(f"Không thể tải cost monitoring cho task {task_id}: storage_service chưa được cấu hình")
            return None
        
        try:
            # Thử tải từ file
            cost_data_path = f"research_tasks/{task_id}/cost.json"
            cost_data = None
            
            # Kiểm tra xem storage_service có phương thức load_data không
            if hasattr(self.storage_service, 'load_data'):
                cost_data = self.storage_service.load_data(cost_data_path)
            else:
                # Sử dụng phương thức load bất đồng bộ
                cost_data = await self.storage_service.load(cost_data_path)
            
            if not cost_data:
                logger.info(f"Không tìm thấy dữ liệu cost monitoring cho task {task_id}, tạo mới")
                return self.initialize_monitoring(task_id)
            
            cost_monitoring = ResearchCostMonitoring.parse_obj(cost_data)
            self._cost_data[task_id] = cost_monitoring
            return cost_monitoring
            
        except Exception as e:
            logger.error(f"Lỗi khi tải cost monitoring cho task {task_id}: {str(e)}")
            logger.info(f"Khởi tạo cost monitoring mới cho task {task_id}")
            return self.initialize_monitoring(task_id)
    
    async def get_monitoring(self, task_id: str) -> ResearchCostMonitoring:
        """Lấy đối tượng monitoring cho một task, tạo mới nếu chưa tồn tại"""
        if task_id in self._cost_data:
            return self._cost_data[task_id]
            
        # Thử tải từ storage
        monitoring = await self.load_monitoring(task_id)
        if monitoring:
            return monitoring
            
        # Nếu không có, tạo mới
        return self.initialize_monitoring(task_id)
    
    def update_model_pricing(self, pricing_data: Dict[str, Dict[str, float]]):
        """Cập nhật bảng giá model"""
        self.model_pricing.update(pricing_data)
        logger.info(f"Đã cập nhật bảng giá model: {self.model_pricing}")
    
    def update_search_pricing(self, pricing_data: Dict[str, float]):
        """Cập nhật bảng giá search"""
        self.search_pricing.update(pricing_data)
        logger.info(f"Đã cập nhật bảng giá search: {self.search_pricing}")
    
    def _calculate_llm_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Tính toán chi phí cho một LLM request"""
        if model not in self.model_pricing:
            logger.warning(f"Không tìm thấy bảng giá cho model {model}, sử dụng giá mặc định")
            return 0.0
        
        pricing = self.model_pricing[model]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def _calculate_search_cost(self, provider: str) -> float:
        """Tính toán chi phí cho một Search request"""
        if provider not in self.search_pricing:
            logger.warning(f"Không tìm thấy bảng giá cho provider {provider}, sử dụng giá mặc định")
            return 0.0
        
        return self.search_pricing[provider]
    
    async def log_llm_request(
        self, 
        task_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        prompt: Optional[str] = None,
        duration_ms: Optional[int] = None,
        endpoint: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> None:
        """
        Ghi nhận một LLM request
        
        Args:
            task_id: ID của task
            model: Tên model sử dụng
            input_tokens: Số lượng input tokens
            output_tokens: Số lượng output tokens
            prompt: Prompt đã sử dụng
            duration_ms: Thời gian xử lý (ms)
            endpoint: Endpoint API đã sử dụng
            purpose: Mục đích của request
        """
        # Tính toán chi phí
        cost_usd = self._calculate_llm_cost(model, input_tokens, output_tokens)
        
        # Lấy monitoring data
        monitoring = await self.get_monitoring(task_id)
        
        # Tạo LLM cost entry
        llm_cost = LLMCost(
            timestamp=datetime.now().isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            prompt=prompt[:500] if prompt else None,  # Chỉ lưu 500 ký tự đầu tiên
            duration_ms=duration_ms,
            endpoint=endpoint,
            purpose=purpose
        )
        
        # Thêm vào danh sách
        monitoring.llm_requests.append(llm_cost)
        
        # Cập nhật summary
        self._update_summary(monitoring)
        
        # Lưu dữ liệu
        self._save_cost_data(task_id)
        
        # Cập nhật task.json
        try:
            summary = await self.get_summary(task_id)
            asyncio.create_task(self._update_task_json(task_id, summary))
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật task.json: {str(e)}")
        
        logger.info(f"Đã ghi nhận LLM request cho task {task_id}: {input_tokens} input, {output_tokens} output, {cost_usd:.6f} USD")

    async def log_search_request(
        self,
        task_id: str,
        provider: str,
        query: str,
        duration_ms: Optional[int] = None,
        num_results: Optional[int] = None,
        purpose: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> None:
        """
        Ghi nhận một Search request
        
        Args:
            task_id: ID của task
            provider: Tên provider sử dụng
            query: Câu truy vấn tìm kiếm
            duration_ms: Thời gian xử lý (ms)
            num_results: Số lượng kết quả trả về
            purpose: Mục đích của request
            input_tokens: Số lượng token đầu vào (nếu có)
            output_tokens: Số lượng token đầu ra (nếu có)
        """
        # Tính toán chi phí
        cost_usd = 0.0
        
        # Nếu có thông tin token và provider là perplexity, tính chi phí dựa trên token
        if provider == "perplexity" and input_tokens is not None and output_tokens is not None:
            model = "llama-3.1-sonar-small-128k-online"  # Mô hình mặc định của Perplexity
            cost_usd = self._calculate_llm_cost(model, input_tokens, output_tokens)
            logger.info(f"Tính chi phí Perplexity dựa trên token: {input_tokens} input, {output_tokens} output, {cost_usd:.6f} USD")
        else:
            # Nếu không có thông tin token, sử dụng chi phí cố định trên mỗi request
            cost_usd = self._calculate_search_cost(provider)
            logger.info(f"Tính chi phí search dựa trên cố định: {cost_usd:.6f} USD")
        
        # Lấy monitoring data
        monitoring = await self.get_monitoring(task_id)
        
        # Tạo Search cost entry
        search_cost = SearchCost(
            timestamp=datetime.now().isoformat(),
            provider=provider,
            query=query[:500] if query else None,  # Chỉ lưu 500 ký tự đầu tiên
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            num_results=num_results,
            purpose=purpose,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Thêm vào danh sách
        monitoring.search_requests.append(search_cost)
        
        # Cập nhật summary
        self._update_summary(monitoring)
        
        # Lưu dữ liệu
        self._save_cost_data(task_id)
        
        # Cập nhật task.json
        try:
            summary = await self.get_summary(task_id)
            asyncio.create_task(self._update_task_json(task_id, summary))
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật task.json: {str(e)}")
        
        logger.info(f"Đã ghi nhận Search request cho task {task_id}: {provider}, {cost_usd:.6f} USD")

    async def start_phase_timing(self, task_id: str, phase_name: str) -> str:
        """Bắt đầu timing cho một phase"""
        monitoring = await self.get_monitoring(task_id)
        phase_id = monitoring.start_phase(phase_name)
        
        # Lưu dữ liệu
        self._save_cost_data(task_id)
        
        logger.info(f"Bắt đầu timing cho phase {phase_name} của task {task_id}")
        return phase_id
    
    async def end_phase_timing(self, task_id: str, phase_name: str, status: str = "completed") -> None:
        """Kết thúc timing cho một phase"""
        monitoring = await self.get_monitoring(task_id)
        monitoring.end_phase(phase_name, status)
        
        # Lưu dữ liệu
        self._save_cost_data(task_id)
        
        # Cập nhật task.json với thông tin chi phí mới nhất
        asyncio.create_task(self._update_task_json(task_id, monitoring.summary))
        
        logger.info(f"Kết thúc timing cho phase {phase_name} của task {task_id} với trạng thái {status}")
    
    async def start_section_timing(self, task_id: str, section_id: str, section_title: str) -> str:
        """Bắt đầu timing cho một section"""
        monitoring = await self.get_monitoring(task_id)
        section_id = monitoring.start_section(section_id, section_title)
        
        # Lưu dữ liệu
        self._save_cost_data(task_id)
        
        logger.info(f"Bắt đầu timing cho section {section_title} của task {task_id}")
        return section_id
    
    async def end_section_timing(self, task_id: str, section_id: str, status: str = "completed") -> None:
        """Kết thúc timing cho một section"""
        monitoring = await self.get_monitoring(task_id)
        monitoring.end_section(section_id, status)
        
        # Lưu dữ liệu
        self._save_cost_data(task_id)
        
        # Cập nhật task.json với thông tin chi phí mới nhất
        self._update_task_json(task_id, monitoring.summary)
        
        logger.info(f"Kết thúc timing cho section {section_id} của task {task_id} với trạng thái {status}")
    
    async def get_summary(self, task_id: str) -> CostSummary:
        """
        Lấy tổng hợp chi phí cho một task
        
        Args:
            task_id: ID của task
            
        Returns:
            CostSummary: Tổng hợp chi phí
        """
        monitoring = await self.get_monitoring(task_id)
        
        # Cập nhật summary trước khi trả về
        self._update_summary(monitoring)
        
        return monitoring.summary
    
    def _save_cost_data(self, task_id: str) -> None:
        """
        Lưu dữ liệu cost monitoring vào file
        
        Args:
            task_id: ID của task
        """
        if not self.storage_service:
            logger.warning(f"Không thể lưu cost monitoring cho task {task_id}: storage_service chưa được cấu hình")
            return
            
        try:
            # Lấy dữ liệu monitoring
            monitoring = self._cost_data.get(task_id)
            if not monitoring:
                logger.warning(f"Không tìm thấy cost monitoring cho task {task_id}")
                return
                
            # Lưu dữ liệu vào file - sử dụng đường dẫn tương đối
            file_path = f"research_tasks/{task_id}/cost.json"
            # Sử dụng phương thức save_data thay vì storage_service.save trực tiếp
            self.storage_service.save_data(monitoring.dict(), file_path)
            logger.info(f"Đã lưu dữ liệu vào file {file_path}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu cost monitoring: {str(e)}")
    
    def ensure_cost_data_exists(self, task_id: str) -> bool:
        """
        Đảm bảo file cost.json tồn tại cho task
        
        Args:
            task_id: ID của task
            
        Returns:
            bool: True nếu file đã tồn tại hoặc đã được tạo thành công, False nếu có lỗi
        """
        if not self.storage_service:
            logger.warning(f"Không thể đảm bảo cost data cho task {task_id}: storage_service chưa được cấu hình")
            return False
            
        try:
            # Kiểm tra xem đã có dữ liệu monitoring chưa
            monitoring = self._cost_data.get(task_id)
            
            # Nếu chưa có, tạo mới
            if not monitoring:
                monitoring = self.initialize_monitoring(task_id)
                
            # Lưu dữ liệu vào file
            self._save_cost_data(task_id)
            
            return True
        except Exception as e:
            logger.error(f"Lỗi khi đảm bảo cost data tồn tại: {str(e)}")
            return False
    
    async def push_to_github(self, task_id: str, github_storage=None) -> Optional[str]:
        """Đẩy báo cáo chi phí lên GitHub"""
        if not github_storage:
            logger.warning(f"Không thể đẩy cost report lên GitHub cho task {task_id}: github_storage chưa được cung cấp")
            return None
        
        monitoring = await self.get_monitoring(task_id)
        
        try:
            # Tạo báo cáo markdown
            report_content = self._generate_markdown_report(monitoring)
            
            # Đẩy lên GitHub
            file_name = f"cost_report_{task_id}.md"
            github_url = await github_storage.save_cost_report(
                file_name,
                report_content,
                f"Cost Report for Research Task {task_id}"
            )
            
            # Cập nhật URL báo cáo vào task.json
            try:
                task_path = f"research_tasks/{task_id}/task.json"
                task_data = await self.load_data(task_path)
                
                # Đảm bảo có cost_info
                if "cost_info" not in task_data:
                    task_data["cost_info"] = {}
                
                # Cập nhật cost_report_url
                task_data["cost_info"]["cost_report_url"] = github_url
                task_data["updated_at"] = datetime.now().isoformat()
                
                # Lưu lại vào file
                await self.save_data(task_path, task_data)
                
                logger.info(f"Đã cập nhật cost_report_url trong task.json cho task {task_id}")
            except Exception as e:
                logger.error(f"Lỗi khi cập nhật cost_report_url trong task.json cho task {task_id}: {str(e)}")
            
            logger.info(f"Đã đẩy cost report cho task {task_id} lên GitHub: {github_url}")
            return github_url
        except Exception as e:
            logger.error(f"Lỗi khi đẩy cost report lên GitHub cho task {task_id}: {str(e)}")
            return None
    
    def _generate_markdown_report(self, monitoring: ResearchCostMonitoring) -> str:
        """Tạo báo cáo markdown từ dữ liệu monitoring"""
        summary = monitoring.summary
        
        # Định dạng timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Cost Report for Research Task {monitoring.task_id}

## Summary
- **Total Cost**: ${summary.total_cost_usd:.6f} USD
- **LLM Cost**: ${summary.llm_cost_usd:.6f} USD
- **Search Cost**: ${summary.search_cost_usd:.6f} USD
- **Total Tokens**: {summary.total_tokens:,} tokens ({summary.total_input_tokens:,} input, {summary.total_output_tokens:,} output)
- **Total Requests**: {summary.total_llm_requests + summary.total_search_requests:,} ({summary.total_llm_requests:,} LLM, {summary.total_search_requests:,} Search)
- **Generated at**: {timestamp}

## Cost Breakdown by Model

| Model | Requests | Input Tokens | Output Tokens | Cost (USD) |
|-------|----------|--------------|--------------|------------|
"""
        
        # Thêm dữ liệu cho từng model
        for model, data in summary.model_breakdown.items():
            report += f"| {model} | {data['requests']:,} | {data['input_tokens']:,} | {data['output_tokens']:,} | ${data['cost_usd']:.6f} |\n"
        
        report += "\n## Cost Breakdown by Search Provider\n\n"
        report += "| Provider | Requests | Cost (USD) |\n"
        report += "|----------|----------|------------|\n"
        
        # Thêm dữ liệu cho từng provider
        for provider, data in summary.provider_breakdown.items():
            report += f"| {provider} | {data['requests']:,} | ${data['cost_usd']:.6f} |\n"
        
        # Thêm thông tin về timing
        report += "\n## Phase Timing\n\n"
        report += "| Phase | Duration (seconds) | Status |\n"
        report += "|-------|-------------------|--------|\n"
        
        for phase in monitoring.phase_timings:
            duration = phase.duration_seconds or 0
            report += f"| {phase.phase_name} | {duration:.2f} | {phase.status} |\n"
        
        # Thêm thông tin về section timing
        report += "\n## Section Timing\n\n"
        report += "| Section | Duration (seconds) | Status |\n"
        report += "|---------|-------------------|--------|\n"
        
        for section in monitoring.section_timings:
            duration = section.duration_seconds or 0
            report += f"| {section.section_title} | {duration:.2f} | {section.status} |\n"
        
        return report

    async def _update_task_json(self, task_id: str, summary: CostSummary) -> None:
        """
        Cập nhật thông tin chi phí vào file task.json
        
        Args:
            task_id: ID của task
            summary: Tổng hợp chi phí
        """
        if not task_id:
            logger.error("Không thể cập nhật task.json: task_id là None")
            return
            
        if not self.storage_service:
            logger.warning(f"Không thể cập nhật task.json cho task {task_id}: storage_service chưa được cấu hình")
            return
            
        try:
            # Đọc file task.json
            task_file_path = f"research_tasks/{task_id}/task.json"
            task_data = None
            
            try:
                # Kiểm tra xem storage_service có phương thức load_data không
                if hasattr(self.storage_service, 'load_data'):
                    task_data = self.storage_service.load_data(task_file_path)
                else:
                    # Sử dụng phương thức load nếu load_data không tồn tại
                    task_data = await self.storage_service.load(task_file_path)
                logger.info(f"Đã đọc dữ liệu từ file: {task_file_path}")
            except Exception as e:
                logger.error(f"Lỗi khi đọc file task.json: {str(e)}")
                return
                
            if not task_data:
                logger.error(f"Không tìm thấy dữ liệu trong file task.json cho task {task_id}")
                return
                
            # Cập nhật thông tin chi phí
            if "cost_info" not in task_data:
                task_data["cost_info"] = {}
                
            # Kiểm tra task_data["cost_info"] không phải None trước khi cập nhật
            if task_data["cost_info"] is None:
                task_data["cost_info"] = {}
                
            # Cập nhật thông tin chi phí
            task_data["cost_info"]["total_cost_usd"] = summary.total_cost_usd
            task_data["cost_info"]["llm_cost_usd"] = summary.llm_cost_usd
            task_data["cost_info"]["search_cost_usd"] = summary.search_cost_usd
            task_data["cost_info"]["total_tokens"] = summary.total_tokens
            task_data["cost_info"]["total_requests"] = summary.total_llm_requests + summary.total_search_requests
            
            # Lưu lại file task.json
            # Kiểm tra xem storage_service có phương thức save_data không
            if hasattr(self.storage_service, 'save_data'):
                await self.storage_service.save_data(task_data, task_file_path)
            else:
                # Sử dụng phương thức save nếu save_data không tồn tại
                await self.storage_service.save(task_data, task_file_path)
            logger.info(f"Đã lưu dữ liệu vào file: {task_file_path}")
            logger.info(f"Đã cập nhật thông tin chi phí vào task.json cho task {task_id}")
            
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật task.json: {str(e)}")
            return

    def _json_serializer(self, obj):
        """Hàm hỗ trợ serialize các object đặc biệt sang JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    async def save_data(self, file_path: str, data: Any) -> None:
        """
        Phương thức đồng bộ để lưu dữ liệu vào file
        
        Args:
            file_path: Đường dẫn file
            data: Dữ liệu cần lưu
        """
        import asyncio
        import json
        import os
        
        try:
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Lưu trực tiếp vào file thay vì gọi storage_service
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            logger.info(f"Đã lưu dữ liệu vào file {file_path}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu vào file {file_path}: {str(e)}")
            raise

    async def load_data(self, file_path: str) -> Any:
        """
        Phương thức đồng bộ để đọc dữ liệu từ file
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            Any: Dữ liệu đã đọc
        """
        import json
        import os
        
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File không tồn tại: {file_path}")
            
            # Đọc trực tiếp từ file thay vì gọi storage_service
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Đã đọc dữ liệu từ file {file_path}")
            return data
        except Exception as e:
            logger.error(f"Lỗi khi đọc dữ liệu từ file {file_path}: {str(e)}")
            raise

    async def _get_monitoring_data(self, task_id: str) -> Optional[ResearchCostMonitoring]:
        """
        Lấy dữ liệu monitoring cho task
        
        Args:
            task_id: ID của task
            
        Returns:
            Optional[ResearchCostMonitoring]: Dữ liệu monitoring hoặc None nếu không tìm thấy
        """
        monitoring = self._cost_data.get(task_id)
        if not monitoring:
            logger.warning(f"Không tìm thấy dữ liệu monitoring cho task {task_id}")
        return monitoring

    async def save_monitoring_data(self, task_id: str) -> bool:
        """
        Lưu dữ liệu monitoring vào file và cập nhật task.json
        
        Args:
            task_id: ID của task
            
        Returns:
            bool: True nếu thành công, False nếu có lỗi
        """
        try:
            # Lấy dữ liệu monitoring
            monitoring = await self._get_monitoring_data(task_id)
            if not monitoring:
                return False
            
            # Cập nhật summary trước khi lưu
            summary = self._update_summary(monitoring)
                
            # Lưu dữ liệu vào file
            self._save_cost_data(task_id)
            
            # Cập nhật task.json
            await self._update_task_json(task_id, summary)
            
            return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu monitoring: {str(e)}")
            return False

    def _update_summary(self, monitoring: ResearchCostMonitoring) -> CostSummary:
        """
        Cập nhật summary cho monitoring
        
        Args:
            monitoring: Đối tượng ResearchCostMonitoring
            
        Returns:
            CostSummary: Đối tượng CostSummary đã cập nhật
        """
        # Tạo summary nếu chưa có
        if not monitoring.summary:
            monitoring.summary = CostSummary()
        
        # Reset summary data
        summary = monitoring.summary
        summary.total_cost_usd = 0.0
        summary.llm_cost_usd = 0.0
        summary.search_cost_usd = 0.0
        summary.total_tokens = 0
        summary.total_input_tokens = 0
        summary.total_output_tokens = 0
        summary.total_llm_requests = 0
        summary.total_search_requests = 0
        summary.model_breakdown = {}
        summary.provider_breakdown = {}
        summary.last_updated = datetime.now().isoformat()
        
        # Tính tổng chi phí và token từ LLM requests
        for req in monitoring.llm_requests:
            summary.llm_cost_usd += req.cost_usd
            summary.total_cost_usd += req.cost_usd
            summary.total_input_tokens += req.input_tokens
            summary.total_output_tokens += req.output_tokens
            summary.total_tokens += req.input_tokens + req.output_tokens
            summary.total_llm_requests += 1
            
            # Cập nhật breakdown theo model
            if req.model not in summary.model_breakdown:
                summary.model_breakdown[req.model] = {
                    "cost_usd": 0.0,
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            
            model_data = summary.model_breakdown[req.model]
            model_data["cost_usd"] += req.cost_usd
            model_data["requests"] += 1
            model_data["input_tokens"] += req.input_tokens
            model_data["output_tokens"] += req.output_tokens
        
        # Tính tổng chi phí từ Search requests
        for req in monitoring.search_requests:
            summary.search_cost_usd += req.cost_usd
            summary.total_cost_usd += req.cost_usd
            summary.total_search_requests += 1
            
            # Cập nhật breakdown theo provider
            if req.provider not in summary.provider_breakdown:
                summary.provider_breakdown[req.provider] = {
                    "cost_usd": 0.0,
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            
            provider_data = summary.provider_breakdown[req.provider]
            provider_data["cost_usd"] += req.cost_usd
            provider_data["requests"] += 1
            
            # Nếu có thông tin token cho search request (Perplexity), cập nhật tổng token
            if hasattr(req, 'input_tokens') and hasattr(req, 'output_tokens') and req.input_tokens and req.output_tokens:
                summary.total_input_tokens += req.input_tokens
                summary.total_output_tokens += req.output_tokens
                summary.total_tokens += req.input_tokens + req.output_tokens
                
                provider_data["input_tokens"] += req.input_tokens
                provider_data["output_tokens"] += req.output_tokens
        
        return summary
        
    async def get_cost_summary(self, task_id: str) -> ResearchCostInfo:
        """Lấy tổng hợp chi phí cho một task"""
        try:
            # Lấy hoặc tạo mới monitoring
            monitoring = await self.load_monitoring(task_id)
            if not monitoring:
                monitoring = self.initialize_monitoring(task_id)
            
            # Cập nhật summary
            summary = monitoring.summary
            if not summary:
                summary = monitoring._update_summary()
            
            # Chuyển đổi sang ResearchCostInfo
            cost_info = ResearchCostInfo(
                total_cost_usd=summary.total_cost_usd,
                llm_cost_usd=summary.llm_cost_usd,
                search_cost_usd=summary.search_cost_usd,
                total_tokens=summary.total_tokens,
                total_requests=summary.total_llm_requests + summary.total_search_requests,
                model_breakdown=summary.model_breakdown,
                execution_time_seconds={
                    timing.phase_name: timing.duration_seconds 
                    for timing in monitoring.phase_timings 
                    if timing.duration_seconds is not None
                }
            )
            
            return cost_info
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy cost summary cho task {task_id}: {str(e)}")
            # Trả về ResearchCostInfo mặc định nếu có lỗi
            return ResearchCostInfo()

# Singleton instance
cost_service = None

async def get_cost_service(storage_service=None):
    """Lấy singleton instance của CostMonitoringService"""
    global cost_service
    if not cost_service:
        cost_service = CostMonitoringService(storage_service)
    return cost_service 