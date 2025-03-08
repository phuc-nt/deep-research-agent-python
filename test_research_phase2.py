import asyncio
import json
import time
import requests
import logging
import sys
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

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
            logging.FileHandler("logs/test_research_phase2.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Tạo logger
    return logging.getLogger("test-research")

# Khởi tạo logger
logger = setup_logging()

BASE_URL = "http://localhost:8000/api/v1"

def find_latest_research_task():
    """Tìm research task mới nhất trong thư mục data/research_tasks"""
    tasks_dir = Path("data/research_tasks")
    if not tasks_dir.exists():
        return None
    
    # Lấy danh sách các thư mục task
    task_dirs = [d for d in tasks_dir.iterdir() if d.is_dir()]
    if not task_dirs:
        return None
    
    # Sắp xếp theo thời gian sửa đổi, lấy thư mục mới nhất
    task_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    latest_task_dir = task_dirs[0]
    
    # Kiểm tra xem có đủ dữ liệu không
    task_file = latest_task_dir / "task.json"
    outline_file = latest_task_dir / "outline.json"
    sections_file = latest_task_dir / "sections.json"
    
    if not task_file.exists() or not outline_file.exists() or not sections_file.exists():
        logger.warning(f"Task {latest_task_dir.name} không có đủ dữ liệu")
        return None
    
    # Đọc dữ liệu
    task_data = {}
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data["task"] = json.load(f)
        
        with open(outline_file, 'r', encoding='utf-8') as f:
            task_data["outline"] = json.load(f)
        
        with open(sections_file, 'r', encoding='utf-8') as f:
            task_data["sections"] = json.load(f)
        
        # Tạo request data
        request_data = task_data["task"].get("request", {})
        if not request_data:
            logger.warning(f"Task {latest_task_dir.name} không có thông tin request")
            return None
        
        task_data["request"] = request_data
        task_data["task_id"] = latest_task_dir.name
        
        logger.info(f"Đã tìm thấy task mới nhất: {latest_task_dir.name}")
        return task_data
    
    except Exception as e:
        logger.error(f"Lỗi khi đọc dữ liệu task {latest_task_dir.name}: {str(e)}")
        return None

async def continue_with_editing():
    """
    Tiếp tục xử lý giai đoạn chỉnh sửa cho task mới nhất, sử dụng dữ liệu có sẵn
    
    Returns:
        str: ID của research task đã cập nhật
    """
    try:
        # Tiếp tục xử lý giai đoạn chỉnh sửa cho task mới nhất
        response = requests.post(f"{BASE_URL}/research/edit_only")
        response.raise_for_status()
        
        result = response.json()
        research_id = result["id"]
        logger.info(f"Đã cập nhật research task với ID: {research_id}")
        
        return research_id
        
    except Exception as e:
        logger.error(f"Lỗi khi tiếp tục xử lý giai đoạn chỉnh sửa: {str(e)}")
        raise

async def main():
    """
    Chạy quá trình nghiên cứu từ việc lấy nội dung các sections có sẵn để tiếp tục chỉnh sửa và lưu GitHub:
    1. Tìm file kết quả phase 1 mới nhất
    2. Tạo research task mới với sections có sẵn
    3. Theo dõi tiến độ phase chỉnh sửa
    4. Kiểm tra kết quả và URL GitHub
    """
    logger.info("=== BẮT ĐẦU KIỂM TRA PHASE 2: TỪ SECTIONS CÓ SẴN ĐẾN CHỈNH SỬA VÀ LƯU GITHUB ===")
    
    # Tìm file kết quả phase 1 mới nhất
    phase1_file = find_latest_research_task()
    if not phase1_file:
        logger.error("Không tìm thấy task mới nhất. Vui lòng chạy test_research_phase1.py trước.")
        print("Lỗi: Không tìm thấy task mới nhất. Vui lòng chạy test_research_phase1.py trước.")
        return False
    
    logger.info(f"Đã tìm thấy task mới nhất: {phase1_file['task_id']}")
    print(f"1. Đã tìm thấy task mới nhất: {phase1_file['task_id']}")
    
    try:
        # Đọc dữ liệu từ file
        request_data = phase1_file["request"]
        sections_data = phase1_file["sections"]
        outline_data = phase1_file["outline"]
        
        if not request_data or not sections_data or not outline_data:
            logger.error("Dữ liệu trong task không đầy đủ.")
            print("Lỗi: Dữ liệu trong task không đầy đủ.")
            return False
        
        logger.info(f"Đã đọc dữ liệu từ task: {len(sections_data)} sections")
        print(f"Đã đọc dữ liệu từ task: {len(sections_data)} sections")
        
        # Tiếp tục xử lý giai đoạn chỉnh sửa
        logger.info("Tiếp tục xử lý giai đoạn chỉnh sửa...")
        print("\n2. Tiếp tục xử lý giai đoạn chỉnh sửa...")
        
        research_id = await continue_with_editing()
        
        logger.info(f"Đã cập nhật research task với ID: {research_id}")
        print(f"Đã cập nhật research task với ID: {research_id}")
        
        # Theo dõi tiến độ
        max_attempts = 30
        delay_seconds = 5
        
        logger.info(f"Bắt đầu theo dõi tiến độ phase chỉnh sửa (tối đa {max_attempts} lần kiểm tra)")
        print("\n3. Theo dõi tiến độ phase chỉnh sửa...")
        
        for attempt in range(max_attempts):
            logger.info(f"Lần kiểm tra {attempt + 1}/{max_attempts}")
            print(f"\nLần kiểm tra {attempt + 1}/{max_attempts}")
            
            try:
                # Kiểm tra trạng thái
                status_response = requests.get(f"{BASE_URL}/research/{research_id}/status")
                status_response.raise_for_status()
                status = status_response.json()
                
                logger.info(f"Trạng thái: {status}")
                print(f"Trạng thái: {status}")
                
                # Nếu đã hoàn thành
                if status.get("status") == "completed":
                    logger.info("Nghiên cứu đã hoàn thành!")
                    print("\n4. Nghiên cứu đã hoàn thành!")
                    
                    result_response = requests.get(f"{BASE_URL}/research/{research_id}")
                    result_response.raise_for_status()
                    result = result_response.json()
                    
                    # Ghi log chi tiết về kết quả
                    result_data = result.get('result', {})
                    title = result_data.get('title', 'N/A')
                    content_length = len(result_data.get('content', '')) if result_data.get('content') else 0
                    sources_count = len(result_data.get('sources', [])) if result_data.get('sources') else 0
                    
                    logger.info(f"Kết quả - Tiêu đề: {title}")
                    logger.info(f"Kết quả - Độ dài nội dung: {content_length} ký tự")
                    logger.info(f"Kết quả - Số nguồn tham khảo: {sources_count}")
                    
                    print("\nThông tin kết quả:")
                    print(f"- Tiêu đề: {title}")
                    print(f"- Độ dài nội dung: {content_length} ký tự")
                    print(f"- Số nguồn tham khảo: {sources_count}")
                    
                    # Kiểm tra GitHub URL
                    github_url = result.get("github_url")
                    if github_url:
                        logger.info(f"Kết quả đã được lưu trên GitHub: {github_url}")
                        print(f"\nKết quả đã được lưu trên GitHub: {github_url}")
                    else:
                        logger.warning("Không có thông tin về GitHub URL")
                        print("\nKhông có thông tin về GitHub URL")
                    
                    # Lưu kết quả vào file
                    output_dir = Path("data/test_output")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    
                    output_file = output_dir / f"research_phase2_{research_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Đã lưu kết quả vào file: {output_file}")
                    print(f"\nĐã lưu kết quả vào file: {output_file}")
                    
                    logger.info("=== KẾT THÚC KIỂM TRA PHASE 2 - THÀNH CÔNG ===")
                    return True
                    
                elif status.get("status") == "failed":
                    logger.error("Nghiên cứu thất bại!")
                    print("\nNghiên cứu thất bại!")
                    
                    error_response = requests.get(f"{BASE_URL}/research/{research_id}")
                    error_response.raise_for_status()
                    error_data = error_response.json()
                    error = error_data.get("error", {})
                    
                    error_message = error.get('message', 'Unknown error')
                    details = error.get("details", {})
                    
                    logger.error(f"Lỗi: {error_message}")
                    if details:
                        logger.error(f"Chi tiết lỗi: {json.dumps(details, ensure_ascii=False)}")
                    
                    print(f"Lỗi: {error_message}")
                    if details:
                        print(f"Chi tiết: {json.dumps(details, indent=2, ensure_ascii=False)}")
                    
                    logger.info("=== KẾT THÚC KIỂM TRA PHASE 2 - THẤT BẠI ===")
                    return False
                
                # Đợi trước khi kiểm tra lại
                if attempt < max_attempts - 1:
                    logger.info(f"Đợi {delay_seconds} giây trước lần kiểm tra tiếp theo")
                    print(f"Đợi {delay_seconds} giây...")
                    time.sleep(delay_seconds)
                    
            except requests.RequestException as e:
                logger.error(f"Lỗi khi gửi request: {str(e)}")
                print(f"Lỗi khi gửi request: {str(e)}")
                time.sleep(delay_seconds)
        
        logger.warning("Đã hết thời gian chờ, phase chỉnh sửa vẫn chưa hoàn thành")
        print("\nĐã hết thời gian chờ, phase chỉnh sửa vẫn chưa hoàn thành.")
        logger.info("=== KẾT THÚC KIỂM TRA PHASE 2 - TIMEOUT ===")
        return False
        
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        logger.info("=== KẾT THÚC KIỂM TRA PHASE 2 - LỖI ===")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 