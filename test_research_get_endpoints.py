import asyncio
import json
import time
import requests
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Cấu hình logging
def setup_logging():
    """Cấu hình logging"""
    # Tạo thư mục logs nếu chưa tồn tại
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Cấu hình logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/test_research_get_endpoints.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Tạo logger
    return logging.getLogger("test-research-get-endpoints")

# Khởi tạo logger
logger = setup_logging()

BASE_URL = "http://localhost:8000/api/v1"
RESEARCH_ID = "a5f44a2d-346d-4871-aadd-aa5a11b9f261"

async def test_get_research():
    """Test endpoint GET /research/{research_id}"""
    logger.info("=== KIỂM TRA ENDPOINT GET /research/{research_id} ===")
    print("\n1. Kiểm tra endpoint GET /research/{research_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/research/{RESEARCH_ID}")
        response.raise_for_status()
        
        data = response.json()
        logger.info("Đã nhận response thành công")
        print("Đã nhận response thành công")
        
        # Hiển thị thông tin chi tiết
        print("\nThông tin chi tiết:")
        print(f"- ID: {data['id']}")
        print(f"- Trạng thái: {data['status']}")
        print(f"- Query: {data['request']['query']}")
        print(f"- Topic: {data['request'].get('topic', 'N/A')}")
        print(f"- Scope: {data['request'].get('scope', 'N/A')}")
        print(f"- Target Audience: {data['request'].get('target_audience', 'N/A')}")
        
        if data.get('outline'):
            print(f"\nSố phần trong outline: {len(data['outline']['sections'])}")
        
        if data.get('result'):
            print(f"\nKết quả:")
            print(f"- Tiêu đề: {data['result']['title']}")
            print(f"- Độ dài nội dung: {len(data['result']['content'])} ký tự")
            print(f"- Số nguồn tham khảo: {len(data['result']['sources'])}")
        
        # Lưu kết quả vào file
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"research_get_{RESEARCH_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu kết quả vào file: {output_file}")
        print(f"\nĐã lưu kết quả vào file: {output_file}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi request: {str(e)}")
        print(f"Lỗi: {str(e)}")
        return False

async def test_get_research_status():
    """Test endpoint GET /research/{research_id}/status"""
    logger.info("=== KIỂM TRA ENDPOINT GET /research/{research_id}/status ===")
    print("\n2. Kiểm tra endpoint GET /research/{research_id}/status...")
    
    try:
        response = requests.get(f"{BASE_URL}/research/{RESEARCH_ID}/status")
        response.raise_for_status()
        
        data = response.json()
        logger.info("Đã nhận response thành công")
        print("Đã nhận response thành công")
        
        # Hiển thị thông tin trạng thái
        print("\nThông tin trạng thái:")
        print(f"- Status: {data['status']}")
        if 'progress_info' in data:
            progress = data['progress_info']
            print(f"- Phase: {progress.get('phase', 'N/A')}")
            print(f"- Message: {progress.get('message', 'N/A')}")
            if 'time_taken' in progress:
                print(f"- Time taken: {progress['time_taken']}")
            if 'total_time' in progress:
                print(f"- Total time: {progress['total_time']}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi request: {str(e)}")
        print(f"Lỗi: {str(e)}")
        return False

async def test_get_research_outline():
    """Test endpoint GET /research/{research_id}/outline"""
    logger.info("=== KIỂM TRA ENDPOINT GET /research/{research_id}/outline ===")
    print("\n3. Kiểm tra endpoint GET /research/{research_id}/outline...")
    
    try:
        response = requests.get(f"{BASE_URL}/research/{RESEARCH_ID}/outline")
        response.raise_for_status()
        
        data = response.json()
        logger.info("Đã nhận response thành công")
        print("Đã nhận response thành công")
        
        # Hiển thị thông tin outline
        print("\nThông tin outline:")
        print(f"Số phần: {len(data['sections'])}")
        for i, section in enumerate(data['sections'], 1):
            print(f"\nPhần {i}:")
            print(f"- Tiêu đề: {section['title']}")
            print(f"- Mô tả: {section.get('description', 'N/A')}")
        
        # Lưu outline vào file
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"research_outline_{RESEARCH_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu outline vào file: {output_file}")
        print(f"\nĐã lưu outline vào file: {output_file}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi request: {str(e)}")
        print(f"Lỗi: {str(e)}")
        return False

async def test_get_research_progress():
    """Test endpoint GET /research/{research_id}/progress"""
    logger.info("=== KIỂM TRA ENDPOINT GET /research/{research_id}/progress ===")
    print("\n4. Kiểm tra endpoint GET /research/{research_id}/progress...")
    
    try:
        response = requests.get(f"{BASE_URL}/research/{RESEARCH_ID}/progress")
        response.raise_for_status()
        
        data = response.json()
        logger.info("Đã nhận response thành công")
        print("Đã nhận response thành công")
        
        # Hiển thị thông tin tiến độ
        print("\nThông tin tiến độ:")
        progress_info = data.get('progress_info', {})
        print(f"- Phase: {progress_info.get('phase', 'N/A')}")
        print(f"- Message: {progress_info.get('message', 'N/A')}")
        
        if 'current_section' in progress_info and 'total_sections' in progress_info:
            print(f"- Tiến độ: {progress_info['current_section']}/{progress_info['total_sections']} phần")
        
        if 'time_taken' in progress_info:
            print(f"- Thời gian xử lý: {progress_info['time_taken']}")
        
        if 'total_time' in progress_info:
            print(f"- Tổng thời gian: {progress_info['total_time']}")
        
        # Lưu thông tin tiến độ vào file
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"research_progress_{RESEARCH_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu thông tin tiến độ vào file: {output_file}")
        print(f"\nĐã lưu thông tin tiến độ vào file: {output_file}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi request: {str(e)}")
        print(f"Lỗi: {str(e)}")
        return False

async def test_get_research_cost():
    """Test endpoint GET /research/{research_id}/cost"""
    logger.info("=== KIỂM TRA ENDPOINT GET /research/{research_id}/cost ===")
    print("\n5. Kiểm tra endpoint GET /research/{research_id}/cost...")
    
    try:
        response = requests.get(f"{BASE_URL}/research/{RESEARCH_ID}/cost")
        response.raise_for_status()
        
        data = response.json()
        logger.info("Đã nhận response thành công")
        print("Đã nhận response thành công")
        
        # Hiển thị thông tin chi tiết
        print("\nThông tin chi tiết chi phí:")
        print(f"Task ID: {data.get('task_id')}")
        print(f"Thời gian tạo: {data.get('created_at')}")
        print(f"Cập nhật lần cuối: {data.get('updated_at')}")
        
        # Hiển thị summary
        summary = data.get('summary', {})
        print("\nTổng quan chi phí:")
        print(f"- Tổng chi phí: ${summary.get('total_cost_usd', 0):.6f} USD")
        print(f"- Chi phí LLM: ${summary.get('llm_cost_usd', 0):.6f} USD")
        print(f"- Chi phí Search: ${summary.get('search_cost_usd', 0):.6f} USD")
        print(f"- Tổng tokens: {summary.get('total_tokens', 0):,}")
        print(f"- Input tokens: {summary.get('total_input_tokens', 0):,}")
        print(f"- Output tokens: {summary.get('total_output_tokens', 0):,}")
        print(f"- Tổng LLM requests: {summary.get('total_llm_requests', 0):,}")
        print(f"- Tổng Search requests: {summary.get('total_search_requests', 0):,}")
        
        # Hiển thị chi tiết LLM requests
        llm_requests = data.get('llm_requests', [])
        if llm_requests:
            print("\nChi tiết LLM Requests:")
            for i, req in enumerate(llm_requests, 1):
                print(f"\nRequest {i}:")
                print(f"- Thời gian: {req.get('timestamp')}")
                print(f"- Model: {req.get('model')}")
                print(f"- Input tokens: {req.get('input_tokens'):,}")
                print(f"- Output tokens: {req.get('output_tokens'):,}")
                print(f"- Chi phí: ${req.get('cost_usd', 0):.6f} USD")
                if req.get('purpose'):
                    print(f"- Mục đích: {req.get('purpose')}")
        
        # Hiển thị chi tiết Search requests
        search_requests = data.get('search_requests', [])
        if search_requests:
            print("\nChi tiết Search Requests:")
            for i, req in enumerate(search_requests, 1):
                print(f"\nRequest {i}:")
                print(f"- Thời gian: {req.get('timestamp')}")
                print(f"- Provider: {req.get('provider')}")
                print(f"- Chi phí: ${req.get('cost_usd', 0):.6f} USD")
                if req.get('purpose'):
                    print(f"- Mục đích: {req.get('purpose')}")
                if req.get('num_results'):
                    print(f"- Số kết quả: {req.get('num_results')}")
        
        # Hiển thị timing information
        phase_timings = data.get('phase_timings', [])
        if phase_timings:
            print("\nThời gian thực hiện theo phase:")
            for timing in phase_timings:
                duration = timing.get('duration_seconds', 0)
                if duration:
                    minutes = duration // 60
                    seconds = duration % 60
                    time_str = f"{minutes} phút {seconds:.1f} giây" if minutes > 0 else f"{seconds:.1f} giây"
                    print(f"- {timing.get('phase_name')}: {time_str} ({timing.get('status', 'N/A')})")
        
        # Lưu thông tin chi tiết vào file
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"research_cost_{RESEARCH_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu thông tin chi phí vào file: {output_file}")
        print(f"\nĐã lưu thông tin chi phí vào file: {output_file}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi request: {str(e)}")
        print(f"Lỗi: {str(e)}")
        return False

async def test_get_research_list():
    """Test endpoint GET /research"""
    logger.info("=== KIỂM TRA ENDPOINT GET /research ===")
    print("\n6. Kiểm tra endpoint GET /research...")
    
    try:
        response = requests.get(f"{BASE_URL}/research")
        response.raise_for_status()
        
        data = response.json()
        logger.info("Đã nhận response thành công")
        print("Đã nhận response thành công")
        
        # Hiển thị danh sách research tasks
        print(f"\nSố lượng research tasks: {len(data)}")
        print("\nDanh sách research tasks:")
        for task in data:
            print(f"\n- ID: {task['id']}")
            print(f"  Status: {task['status']}")
            print(f"  Query: {task.get('query', 'N/A')}")
            print(f"  Created at: {task.get('created_at', 'N/A')}")
            print(f"  Updated at: {task.get('updated_at', 'N/A')}")
        
        # Lưu danh sách vào file
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / "research_list.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu danh sách vào file: {output_file}")
        print(f"\nĐã lưu danh sách vào file: {output_file}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi request: {str(e)}")
        print(f"Lỗi: {str(e)}")
        return False

async def main():
    """Hàm chính để chạy tất cả các test"""
    logger.info("=== BẮT ĐẦU KIỂM TRA CÁC ENDPOINT GET ===")
    print("=== BẮT ĐẦU KIỂM TRA CÁC ENDPOINT GET ===")
    print(f"Research ID: {RESEARCH_ID}")
    
    # Test từng endpoint
    results = {
        "get_research": await test_get_research(),
        "get_research_status": await test_get_research_status(),
        "get_research_outline": await test_get_research_outline(),
        "get_research_progress": await test_get_research_progress(),
        "get_research_cost": await test_get_research_cost(),
        "get_research_list": await test_get_research_list()
    }
    
    # Hiển thị kết quả tổng hợp
    print("\n=== KẾT QUẢ KIỂM TRA ===")
    all_passed = True
    for endpoint, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{endpoint}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("=== KẾT THÚC KIỂM TRA - TẤT CẢ PASSED ===")
        print("\n=== KẾT THÚC KIỂM TRA - TẤT CẢ PASSED ===")
    else:
        logger.error("=== KẾT THÚC KIỂM TRA - CÓ ENDPOINT FAILED ===")
        print("\n=== KẾT THÚC KIỂM TRA - CÓ ENDPOINT FAILED ===")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 