import os
import json
import uuid
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
import dotenv

# Đảm bảo load biến môi trường nếu có
dotenv.load_dotenv()

# Thiết lập giá trị mặc định cho biến môi trường trước khi import các module
os.environ.setdefault("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
os.environ.setdefault("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
os.environ.setdefault("PERPLEXITY_API_KEY", os.environ.get("PERPLEXITY_API_KEY", ""))
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("API_VERSION", "v1")

from app.services.core.monitoring.cost import CostMonitoringService, get_cost_service
from app.services.core.storage.file import FileStorageService
from app.services.core.llm.openai import OpenAIService
from app.services.core.llm.claude import ClaudeService
from app.services.core.search.perplexity import PerplexityService
from app.core.factory import ServiceFactory
from app.core.config import get_settings

async def test_real_api_cost_monitoring():
    """
    Test tính năng theo dõi chi phí với các API thật
    
    Kiểm tra:
    1. Ghi nhận chi phí cho OpenAI
    2. Ghi nhận chi phí cho Claude
    3. Ghi nhận chi phí cho Perplexity
    4. Tổng hợp chi phí
    """
    print("\n===== TESTING COST MONITORING WITH REAL APIs =====")
    
    # Tạo thư mục test_data
    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(exist_ok=True)
    
    # Tạo task ID
    task_id = str(uuid.uuid4())
    print(f"Task ID: {task_id}")
    
    # Tạo thư mục cho task
    task_dir = test_dir / "data" / "research_tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo task.json mẫu
    task_json_path = task_dir / "task.json"
    task_data = {
        "id": task_id,
        "created_at": datetime.now().isoformat(),
        "query": "Các ứng dụng của AI trong giáo dục năm 2024",
        "status": "in_progress",
        "total_budget": 0.5,
        "current_phase": "research",
        "phases": [
            {
                "name": "research",
                "status": "in_progress"
            },
            {
                "name": "analysis",
                "status": "pending"
            }
        ]
    }
    
    with open(task_json_path, "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=2)
    
    # Khởi tạo storage service với đường dẫn cố định
    storage_service = FileStorageService(base_dir=str(test_dir))
    
    # Khởi tạo cost service với storage service
    cost_service = get_cost_service(storage_service)
    
    # Khởi tạo monitoring
    cost_service.initialize_monitoring(task_id)
    
    # Lấy cấu hình
    settings = get_settings()
    
    # Khởi tạo factory với storage_service đã cấu hình
    factory = ServiceFactory(config=settings)
    # Ghi đè service đã tạo vào factory để đảm bảo sử dụng cùng một instance
    factory.services["storage_file"] = storage_service
    factory.services["cost_monitoring"] = cost_service
    
    # Kiểm tra từng API key và tạo service tương ứng
    services_to_test = []
    
    if os.environ.get("OPENAI_API_KEY"):
        try:
            print("\nKhởi tạo OpenAI service...")
            # Truyền config vào OpenAIService
            openai_service = OpenAIService(settings.dict())
            
            services_to_test.append(("OpenAI", openai_service))
        except Exception as e:
            print(f"❌ Lỗi khi khởi tạo OpenAI service: {str(e)}")
    
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print("Khởi tạo Claude service...")
            # Tạo cấu hình riêng cho Claude với model name thích hợp
            claude_config = settings.dict()
            claude_config["ANTHROPIC_MODEL_NAME"] = "claude-3-5-sonnet-latest"  # Sử dụng model Claude mới nhất
            claude_service = ClaudeService(claude_config)
            services_to_test.append(("Claude", claude_service))
        except Exception as e:
            print(f"❌ Lỗi khi khởi tạo Claude service: {str(e)}")
    
    # Khởi tạo search service nếu có Perplexity API key
    search_service = None
    if os.environ.get("PERPLEXITY_API_KEY"):
        try:
            print("Khởi tạo Perplexity service...")
            search_service = PerplexityService(settings.dict())
        except Exception as e:
            print(f"❌ Lỗi khi khởi tạo Perplexity service: {str(e)}")
    
    # Test các LLM service
    for name, service in services_to_test:
        print(f"\nTesting {name} service...")
        try:
            # Đặt prompt ngắn
            prompt = "Hãy giải thích khái niệm trí tuệ nhân tạo trong 2-3 câu."
            
            print(f"Gửi prompt: '{prompt}'")
            response = await service.generate(
                prompt=prompt,
                task_id=task_id,
                purpose=f"test_{name.lower()}"
            )
            
            print(f"Nhận phản hồi: '{response[:100]}...'")
            print(f"✅ Test {name} thành công!")
        except Exception as e:
            print(f"❌ Lỗi khi test {name}: {str(e)}")
    
    # Test search service nếu có
    if search_service:
        print("\nTesting Search service...")
        try:
            query = "Các ứng dụng của AI trong giáo dục năm 2024"
            
            print(f"Gửi truy vấn: '{query}'")
            results = await search_service.search(
                query=query,
                task_id=task_id,
                purpose="test_search"
            )
            
            print(f"Nhận {len(results)} kết quả")
            print(f"✅ Test Search thành công!")
        except Exception as e:
            print(f"❌ Lỗi khi test Search: {str(e)}")
    
    # Lưu dữ liệu monitoring
    print("\nLưu dữ liệu monitoring...")
    await cost_service.save_monitoring_data(task_id)
    
    # Hiển thị tổng hợp chi phí
    print("\n===== COST SUMMARY =====")
    monitoring = cost_service.get_monitoring(task_id)
    summary = monitoring.summary
    
    print(f"Total Cost: ${summary.total_cost_usd:.6f} USD")
    print(f"LLM Cost: ${summary.llm_cost_usd:.6f} USD")
    print(f"Search Cost: ${summary.search_cost_usd:.6f} USD")
    print(f"Total Tokens: {summary.total_tokens:,} ({summary.total_input_tokens:,} input, {summary.total_output_tokens:,} output)")
    print(f"Total Requests: {summary.total_llm_requests + summary.total_search_requests:,} ({summary.total_llm_requests:,} LLM, {summary.total_search_requests:,} Search)")
    
    # Hiển thị chi tiết từng model
    print("\nModel Breakdown:")
    for model, data in summary.model_breakdown.items():
        print(f"  - {model}: ${data['cost_usd']:.6f} USD ({data['requests']:,} requests, {data['input_tokens']:,} input, {data['output_tokens']:,} output)")
    
    # Hiển thị chi tiết từng provider
    print("\nSearch Provider Breakdown:")
    for provider, data in summary.provider_breakdown.items():
        if "input_tokens" in data and "output_tokens" in data and (data["input_tokens"] > 0 or data["output_tokens"] > 0):
            print(f"  - {provider}: ${data['cost_usd']:.6f} USD ({data['requests']:,} requests, {data['input_tokens']:,} input, {data['output_tokens']:,} output)")
        else:
            print(f"  - {provider}: ${data['cost_usd']:.6f} USD ({data['requests']:,} requests)")
    
    # Kiểm tra file cost.json
    cost_json_path = task_dir / "cost.json"
    if cost_json_path.exists():
        print(f"\n✅ File cost.json đã được tạo tại: {cost_json_path}")
        
        # Đọc nội dung file để kiểm tra
        with open(cost_json_path, "r", encoding="utf-8") as f:
            cost_data = json.load(f)
            print(f"  - Số lượng LLM requests: {len(cost_data.get('llm_requests', []))}")
            print(f"  - Số lượng Search requests: {len(cost_data.get('search_requests', []))}")
    else:
        print(f"\n❌ File cost.json không được tạo")
    
    # Kiểm tra file task.json
    if task_json_path.exists():
        print(f"\n✅ File task.json đã được tạo tại: {task_json_path}")
        
        # Đọc nội dung file để kiểm tra
        with open(task_json_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)
            if "cost_info" in task_data:
                print(f"  - Thông tin chi phí đã được lưu trong task.json")
                print(f"  - Total cost: ${task_data['cost_info'].get('total_cost_usd', 0):.6f} USD")
            else:
                print(f"  - Thông tin chi phí KHÔNG được lưu trong task.json")
    else:
        print(f"\n❌ File task.json không được tạo")
    
    print("\n===== TEST COMPLETED =====")

if __name__ == "__main__":
    # Chạy test bất đồng bộ
    asyncio.run(test_real_api_cost_monitoring()) 