import asyncio
import json
import time
import requests
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

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
            logging.FileHandler("logs/test_research_edit_only.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Tạo logger
    return logging.getLogger("test-research-edit-only")

# Khởi tạo logger
logger = setup_logging()

BASE_URL = "http://localhost:8000/api/v1"

async def main(research_id: Optional[str] = None):
    """
    Chạy quá trình chỉnh sửa nội dung nghiên cứu:
    1. Sử dụng research_id đã có hoặc lấy task mới nhất
    2. Gọi endpoint /research/edit_only
    3. Theo dõi tiến độ chỉnh sửa
    4. Kiểm tra kết quả cuối cùng
    5. Kiểm tra và hiển thị thông tin chi phí
    
    Args:
        research_id: ID của research task đã có (tùy chọn)
    """
    logger.info("=== BẮT ĐẦU KIỂM TRA FLOW CHỈNH SỬA NGHIÊN CỨU ===")
    
    try:
        # Nếu không có research_id, lấy task mới nhất
        if not research_id:
            logger.info("Không có research_id, lấy danh sách research tasks...")
            print("1. Lấy danh sách research tasks...")
            
            response = requests.get(f"{BASE_URL}/research")
            response.raise_for_status()
            
            tasks = response.json()
            if not tasks:
                logger.error("Không có research task nào")
                print("Không có research task nào. Vui lòng chạy test_research.py trước.")
                return False
            
            # Sắp xếp theo thời gian tạo mới nhất
            tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            research_id = tasks[0]["id"]
            
            logger.info(f"Đã tìm thấy task mới nhất với ID: {research_id}")
            print(f"Đã tìm thấy task mới nhất với ID: {research_id}")
        else:
            logger.info(f"Sử dụng research_id đã cung cấp: {research_id}")
            print(f"1. Sử dụng research_id đã cung cấp: {research_id}")
        
        # Kiểm tra trạng thái task
        status_response = requests.get(f"{BASE_URL}/research/{research_id}/status")
        status_response.raise_for_status()
        status_data = status_response.json()
        
        status = status_data.get("status")
        if status != "completed":
            logger.warning(f"Task {research_id} chưa hoàn thành nghiên cứu (trạng thái: {status})")
            print(f"Cảnh báo: Task {research_id} chưa hoàn thành nghiên cứu (trạng thái: {status})")
            print("Tiếp tục với quá trình chỉnh sửa...")
        
        # Gọi endpoint /research/edit_only
        logger.info(f"Gọi endpoint /research/edit_only với research_id: {research_id}")
        print("\n2. Gọi endpoint /research/edit_only...")
        
        edit_request = {
            "research_id": research_id
        }
        
        edit_response = requests.post(f"{BASE_URL}/research/edit_only", json=edit_request)
        edit_response.raise_for_status()
        
        logger.info("Đã gửi yêu cầu chỉnh sửa thành công")
        print("Đã gửi yêu cầu chỉnh sửa thành công")
        
        # Theo dõi tiến độ
        max_attempts = 50
        delay_seconds = 6
        
        logger.info(f"Bắt đầu theo dõi tiến độ chỉnh sửa (tối đa {max_attempts} lần kiểm tra)")
        print("\n3. Theo dõi tiến độ chỉnh sửa...")
        
        current_phase = None
        phase_start_times = {}
        phase_durations = {}
        
        for attempt in range(max_attempts):
            try:
                # Lấy thông tin tiến độ
                progress_response = requests.get(f"{BASE_URL}/research/{research_id}/progress")
                progress_response.raise_for_status()
                progress_data = progress_response.json()
                
                # Lấy thông tin trạng thái
                status_response = requests.get(f"{BASE_URL}/research/{research_id}/status")
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get("status")
                progress_info = progress_data.get("progress_info", {})
                phase = progress_info.get("phase", "unknown")
                
                # Theo dõi thời gian cho từng phase
                if phase != current_phase:
                    if current_phase:
                        phase_end = time.time()
                        duration = phase_end - phase_start_times[current_phase]
                        phase_durations[current_phase] = duration
                        logger.info(f"Phase {current_phase} kết thúc sau {duration:.2f} giây")
                        print(f"\nPhase {current_phase} kết thúc sau {duration:.2f} giây")
                    
                    current_phase = phase
                    phase_start_times[phase] = time.time()
                    logger.info(f"Bắt đầu phase mới: {phase}")
                    print(f"\nBắt đầu phase mới: {phase}")
                
                print(f"\nLần kiểm tra {attempt + 1}/{max_attempts}")
                print(f"Trạng thái: {status}")
                print(f"Phase: {phase}")
                print(f"Thông điệp: {progress_info.get('message', 'N/A')}")
                
                # Hiển thị thông tin thời gian
                if "elapsed_time" in progress_data:
                    elapsed = progress_data["elapsed_time"]
                    print(f"Thời gian đã trôi qua: {elapsed.get('formatted', 'N/A')}")
                
                # Hiển thị thông tin chi tiết về bước chỉnh sửa
                if phase == "editing" and "step" in progress_info:
                    step = progress_info.get("step", "")
                    print(f"Bước hiện tại: {step}")
                
                # Nếu đã hoàn thành
                if status == "completed":
                    # Tính thời gian cho phase cuối cùng
                    if current_phase:
                        phase_end = time.time()
                        duration = phase_end - phase_start_times[current_phase]
                        phase_durations[current_phase] = duration
                    
                    logger.info("Chỉnh sửa hoàn thành!")
                    print("\nChỉnh sửa hoàn thành!")
                    
                    # Hiển thị tổng thời gian cho từng phase
                    print("\nThời gian xử lý cho từng phase:")
                    total_duration = 0
                    for phase_name, duration in phase_durations.items():
                        print(f"- {phase_name}: {duration:.2f} giây")
                        total_duration += duration
                    print(f"Tổng thời gian: {total_duration:.2f} giây")
                    
                    # Lấy kết quả cuối cùng
                    logger.info("Lấy kết quả cuối cùng...")
                    print("\n4. Lấy kết quả cuối cùng...")
                    
                    result_response = requests.get(f"{BASE_URL}/research/{research_id}")
                    result_response.raise_for_status()
                    result = result_response.json()
                    
                    # Lấy thông tin chi phí
                    logger.info("Lấy thông tin chi phí...")
                    print("\n5. Lấy thông tin chi phí...")
                    
                    cost_response = requests.get(f"{BASE_URL}/research/{research_id}/cost")
                    cost_response.raise_for_status()
                    cost_data = cost_response.json()
                    
                    # Hiển thị thông tin chi phí
                    print("\nThông tin chi phí:")
                    print(json.dumps(cost_data, indent=2, ensure_ascii=False))
                    
                    # Lưu kết quả vào file
                    output_dir = Path("test_outputs")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    
                    output_file = output_dir / f"research_edit_{research_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    # Lưu thông tin chi phí vào file
                    cost_output_file = output_dir / f"research_edit_cost_{research_id}.json"
                    try:
                        with open(cost_output_file, 'w', encoding='utf-8') as f:
                            json.dump(cost_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Đã lưu thông tin chi phí vào file: {cost_output_file}")
                        print(f"\nĐã lưu thông tin chi phí vào file: {cost_output_file}")
                    except Exception as e:
                        logger.error(f"Lỗi khi lưu thông tin chi phí: {str(e)}")
                    
                    logger.info(f"Đã lưu kết quả vào file: {output_file}")
                    print(f"\nĐã lưu kết quả vào file: {output_file}")
                    
                    logger.info("=== KẾT THÚC KIỂM TRA FLOW CHỈNH SỬA NGHIÊN CỨU - THÀNH CÔNG ===")
                    return True
                    
                elif status == "failed":
                    logger.error("Chỉnh sửa thất bại!")
                    print("\nChỉnh sửa thất bại!")
                    
                    # Lấy thông tin lỗi
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
                    
                    logger.info("=== KẾT THÚC KIỂM TRA FLOW CHỈNH SỬA NGHIÊN CỨU - THẤT BẠI ===")
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
        
        logger.warning("Đã hết thời gian chờ, chỉnh sửa vẫn chưa hoàn thành")
        print("\nĐã hết thời gian chờ, chỉnh sửa vẫn chưa hoàn thành.")
        logger.info("=== KẾT THÚC KIỂM TRA FLOW CHỈNH SỬA NGHIÊN CỨU - TIMEOUT ===")
        return False
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi gửi yêu cầu: {str(e)}")
        print(f"Lỗi: {str(e)}")
        logger.info("=== KẾT THÚC KIỂM TRA FLOW CHỈNH SỬA NGHIÊN CỨU - LỖI ===")
        return False

if __name__ == "__main__":
    # Kiểm tra xem có research_id được cung cấp qua tham số dòng lệnh không
    if len(sys.argv) > 1:
        research_id = sys.argv[1]
        print(f"Sử dụng research_id từ tham số dòng lệnh: {research_id}")
    else:
        research_id = None
        print("Không có research_id được cung cấp, sẽ sử dụng task mới nhất")
    
    try:
        asyncio.run(main(research_id))
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 