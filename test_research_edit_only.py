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

async def main(task_id: Optional[str] = None):
    """
    Chạy quá trình chỉnh sửa nội dung nghiên cứu:
    1. Sử dụng task_id đã có hoặc lấy task mới nhất
    2. Gọi endpoint /research/edit_only
    3. Theo dõi tiến độ chỉnh sửa
    4. Kiểm tra kết quả cuối cùng
    5. Kiểm tra và hiển thị thông tin chi phí
    
    Args:
        task_id: ID của research task đã có (tùy chọn)
    """
    logger.info("=== BẮT ĐẦU KIỂM TRA FLOW CHỈNH SỬA NGHIÊN CỨU ===")
    
    try:
        # Nếu không có task_id, lấy task mới nhất
        if not task_id:
            logger.info("Không có task_id, lấy danh sách research tasks...")
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
            task_id = tasks[0]["id"]
            
            logger.info(f"Đã tìm thấy task mới nhất với ID: {task_id}")
            print(f"Đã tìm thấy task mới nhất với ID: {task_id}")
        else:
            logger.info(f"Sử dụng task_id đã cung cấp: {task_id}")
            print(f"1. Sử dụng task_id đã cung cấp: {task_id}")
        
        # Kiểm tra trạng thái task
        status_response = requests.get(f"{BASE_URL}/research/{task_id}/status")
        status_response.raise_for_status()
        status_data = status_response.json()
        
        status = status_data.get("status")
        if status != "completed":
            logger.warning(f"Task {task_id} chưa hoàn thành nghiên cứu (trạng thái: {status})")
            print(f"Cảnh báo: Task {task_id} chưa hoàn thành nghiên cứu (trạng thái: {status})")
            print("Tiếp tục với quá trình chỉnh sửa...")
        
        # Gọi endpoint /research/edit_only
        logger.info(f"Gọi endpoint /research/edit_only với task_id: {task_id}")
        print("\n2. Gọi endpoint /research/edit_only...")
        
        edit_request = {
            "task_id": task_id
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
            logger.info(f"Lần kiểm tra {attempt + 1}/{max_attempts}")
            print(f"\nLần kiểm tra {attempt + 1}/{max_attempts}")
            
            try:
                # Kiểm tra tiến độ chi tiết
                progress_response = requests.get(f"{BASE_URL}/research/{task_id}/progress")
                progress_response.raise_for_status()
                progress_data = progress_response.json()
                
                status = progress_data.get("status")
                progress_info = progress_data.get("progress_info", {})
                phase = progress_info.get("phase", "unknown")
                
                # Ghi nhận thời gian bắt đầu của mỗi phase
                if phase != current_phase:
                    if current_phase is not None:
                        # Tính thời gian của phase trước đó
                        phase_end_time = time.time()
                        duration = phase_end_time - phase_start_times.get(current_phase, phase_end_time)
                        phase_durations[current_phase] = duration
                        logger.info(f"Phase {current_phase} hoàn thành trong {duration:.2f} giây")
                        print(f"Phase {current_phase} hoàn thành trong {duration:.2f} giây")
                    
                    # Ghi nhận phase mới
                    current_phase = phase
                    phase_start_times[current_phase] = time.time()
                    logger.info(f"Bắt đầu phase mới: {current_phase}")
                    print(f"Bắt đầu phase mới: {current_phase}")
                
                # Hiển thị thông tin tiến độ chi tiết
                logger.info(f"Trạng thái: {status}")
                logger.info(f"Phase: {phase}")
                logger.info(f"Thông tin tiến độ: {json.dumps(progress_info, ensure_ascii=False)}")
                
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
                    # Tính thời gian của phase cuối cùng
                    if current_phase is not None:
                        phase_end_time = time.time()
                        duration = phase_end_time - phase_start_times.get(current_phase, phase_end_time)
                        phase_durations[current_phase] = duration
                    
                    logger.info("Chỉnh sửa đã hoàn thành!")
                    print("\n4. Chỉnh sửa đã hoàn thành!")
                    
                    # Hiển thị thời gian của từng phase
                    logger.info("Thời gian của từng phase:")
                    print("\nThời gian của từng phase:")
                    for phase_name, duration in phase_durations.items():
                        logger.info(f"- {phase_name}: {duration:.2f} giây")
                        print(f"- {phase_name}: {duration:.2f} giây")
                    
                    # Lấy kết quả
                    result_response = requests.get(f"{BASE_URL}/research/{task_id}")
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
                    
                    # Lấy thông tin chi phí
                    print("\n5. Kiểm tra chi phí chỉnh sửa:")
                    logger.info("Đang lấy thông tin chi phí chỉnh sửa...")
                    
                    try:
                        cost_response = requests.get(f"{BASE_URL}/research/{task_id}/cost")
                        cost_response.raise_for_status()
                        cost_data = cost_response.json()
                        
                        # Hiển thị thông tin chi phí
                        logger.info("Thông tin chi phí:")
                        logger.info(f"- Tổng chi phí: ${cost_data.get('total_cost_usd', 0):.6f} USD")
                        logger.info(f"- Chi phí LLM: ${cost_data.get('llm_cost_usd', 0):.6f} USD")
                        logger.info(f"- Chi phí Search: ${cost_data.get('search_cost_usd', 0):.6f} USD")
                        logger.info(f"- Tổng tokens: {cost_data.get('total_tokens', 0):,}")
                        logger.info(f"- Tổng requests: {cost_data.get('total_requests', 0):,}")
                        
                        print("Thông tin chi phí:")
                        print(f"- Tổng chi phí: ${cost_data.get('total_cost_usd', 0):.6f} USD")
                        print(f"- Chi phí LLM: ${cost_data.get('llm_cost_usd', 0):.6f} USD")
                        print(f"- Chi phí Search: ${cost_data.get('search_cost_usd', 0):.6f} USD")
                        print(f"- Tổng tokens: {cost_data.get('total_tokens', 0):,}")
                        print(f"- Tổng requests: {cost_data.get('total_requests', 0):,}")
                        
                        # Hiển thị chi tiết từng model
                        model_breakdown = cost_data.get('model_breakdown', {})
                        if model_breakdown:
                            print("\nChi tiết theo model:")
                            logger.info("Chi tiết theo model:")
                            for model, model_data in model_breakdown.items():
                                log_msg = f"- {model}: ${model_data.get('cost_usd', 0):.6f} USD ({model_data.get('requests', 0):,} requests)"
                                if 'input_tokens' in model_data and 'output_tokens' in model_data:
                                    log_msg += f", {model_data.get('input_tokens', 0):,} input tokens, {model_data.get('output_tokens', 0):,} output tokens"
                                
                                logger.info(log_msg)
                                print(log_msg)
                        
                        # Hiển thị thời gian thực hiện từ dữ liệu cost
                        execution_time = cost_data.get('execution_time_seconds', {})
                        if execution_time:
                            print("\nThời gian thực hiện (từ cost monitoring):")
                            logger.info("Thời gian thực hiện (từ cost monitoring):")
                            for phase, seconds in execution_time.items():
                                minutes = seconds // 60
                                remaining_seconds = seconds % 60
                                time_str = f"{minutes} phút {remaining_seconds:.1f} giây" if minutes > 0 else f"{seconds:.1f} giây"
                                logger.info(f"- {phase}: {time_str}")
                                print(f"- {phase}: {time_str}")
                        
                    except requests.RequestException as e:
                        logger.error(f"Lỗi khi lấy thông tin chi phí: {str(e)}")
                        print(f"Lỗi khi lấy thông tin chi phí: {str(e)}")
                    
                    # Lưu kết quả vào file
                    output_dir = Path("data/test_output")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    
                    output_file = output_dir / f"research_edit_{task_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    # Lưu thông tin chi phí vào file
                    cost_output_file = output_dir / f"research_edit_cost_{task_id}.json"
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
                    error_response = requests.get(f"{BASE_URL}/research/{task_id}")
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
    # Kiểm tra xem có task_id được cung cấp qua tham số dòng lệnh không
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        print(f"Sử dụng task_id từ tham số dòng lệnh: {task_id}")
    else:
        task_id = None
        print("Không có task_id được cung cấp, sẽ sử dụng task mới nhất")
    
    try:
        asyncio.run(main(task_id))
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 