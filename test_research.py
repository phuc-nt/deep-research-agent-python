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
            logging.FileHandler("logs/test_research.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Tạo logger
    return logging.getLogger("test-research")

# Khởi tạo logger
logger = setup_logging()

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    """
    Chạy quá trình nghiên cứu từ đầu đến khi hoàn thành giai đoạn nghiên cứu:
    1. Tạo yêu cầu nghiên cứu
    2. Theo dõi tiến độ qua các phase (phân tích, tạo dàn ý, nghiên cứu)
    3. Kiểm tra kết quả nghiên cứu
    4. Kiểm tra và hiển thị thông tin chi phí
    """
    logger.info("=== BẮT ĐẦU KIỂM TRA FLOW NGHIÊN CỨU ===")
    
    # Dữ liệu yêu cầu nghiên cứu
    research_request = {
        "query": "Tác hại của mạng xã hỗi tới kỹ năng tranh luận"
    }
    
    logger.info(f"Tạo yêu cầu nghiên cứu: {research_request}")
    print("1. Tạo yêu cầu nghiên cứu...")
    
    try:
        # Tạo yêu cầu nghiên cứu
        response = requests.post(f"{BASE_URL}/research", json=research_request)
        response.raise_for_status()
        
        data = response.json()
        research_id = data["id"]
        logger.info(f"Đã tạo research task với ID: {research_id}")
        print(f"Đã tạo research task với ID: {research_id}")
        
        # Theo dõi tiến độ
        max_attempts = 50  # Giảm số lần kiểm tra để tránh chờ quá lâu
        delay_seconds = 6  # Giảm thời gian delay xuống 6 giây
        
        logger.info(f"Bắt đầu theo dõi tiến độ nghiên cứu (tối đa {max_attempts} lần kiểm tra)")
        print("\n2. Theo dõi tiến độ nghiên cứu...")
        
        current_phase = None
        phase_start_times = {}
        phase_durations = {}
        
        for attempt in range(max_attempts):
            logger.info(f"Lần kiểm tra {attempt + 1}/{max_attempts}")
            print(f"\nLần kiểm tra {attempt + 1}/{max_attempts}")
            
            try:
                # Kiểm tra tiến độ chi tiết
                progress_response = requests.get(f"{BASE_URL}/research/{research_id}/progress")
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
                
                # Hiển thị thông tin tiến độ phần trăm nếu có
                if "completion_percentage" in progress_data:
                    print(f"Hoàn thành: {progress_data['completion_percentage']}%")
                
                # Hiển thị thông tin chi tiết về section hiện tại nếu đang ở giai đoạn nghiên cứu
                if phase == "researching" and "current_section" in progress_info:
                    current_section = progress_info.get("current_section", 0)
                    total_sections = progress_info.get("total_sections", 0)
                    section_title = progress_info.get("current_section_title", "")
                    
                    if current_section and total_sections:
                        print(f"Đang nghiên cứu phần {current_section}/{total_sections}: {section_title}")
                
                # Nếu đã hoàn thành
                if status == "completed":
                    # Tính thời gian của phase cuối cùng
                    if current_phase is not None:
                        phase_end_time = time.time()
                        duration = phase_end_time - phase_start_times.get(current_phase, phase_end_time)
                        phase_durations[current_phase] = duration
                    
                    logger.info("Nghiên cứu đã hoàn thành!")
                    print("\n3. Nghiên cứu đã hoàn thành!")
                    
                    # Hiển thị thời gian của từng phase
                    logger.info("Thời gian của từng phase:")
                    print("\nThời gian của từng phase:")
                    for phase_name, duration in phase_durations.items():
                        logger.info(f"- {phase_name}: {duration:.2f} giây")
                        print(f"- {phase_name}: {duration:.2f} giây")
                    
                    # Lấy kết quả
                    result_response = requests.get(f"{BASE_URL}/research/{research_id}")
                    result_response.raise_for_status()
                    result = result_response.json()
                    
                    # Kiểm tra sections
                    sections = result.get('sections', [])
                    sections_count = len(sections) if sections else 0
                    
                    logger.info(f"Kết quả - Số phần đã nghiên cứu: {sections_count}")
                    print(f"\nSố phần đã nghiên cứu: {sections_count}")
                    
                    if sections:
                        for i, section in enumerate(sections):
                            title = section.get('title', 'N/A')
                            content_length = len(section.get('content', '')) if section.get('content') else 0
                            logger.info(f"Phần {i+1}: {title} - {content_length} ký tự")
                            print(f"- Phần {i+1}: {title} - {content_length} ký tự")
                    
                    # Lấy thông tin chi phí
                    print("\n4. Kiểm tra chi phí nghiên cứu:")
                    logger.info("Đang lấy thông tin chi phí nghiên cứu...")
                    
                    try:
                        cost_response = requests.get(f"{BASE_URL}/research/{research_id}/cost")
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
                    
                    output_file = output_dir / f"research_{research_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    # Lưu thông tin chi phí vào file
                    cost_output_file = output_dir / f"research_cost_{research_id}.json"
                    try:
                        with open(cost_output_file, 'w', encoding='utf-8') as f:
                            json.dump(cost_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Đã lưu thông tin chi phí vào file: {cost_output_file}")
                        print(f"\nĐã lưu thông tin chi phí vào file: {cost_output_file}")
                    except Exception as e:
                        logger.error(f"Lỗi khi lưu thông tin chi phí: {str(e)}")
                    
                    logger.info(f"Đã lưu kết quả vào file: {output_file}")
                    print(f"\nĐã lưu kết quả vào file: {output_file}")
                    
                    print("\n5. Bước tiếp theo: Sử dụng endpoint /research/edit_only để chỉnh sửa nội dung")
                    print(f"   Sử dụng task_id: {research_id}")
                    
                    logger.info("=== KẾT THÚC KIỂM TRA FLOW NGHIÊN CỨU - THÀNH CÔNG ===")
                    return research_id
                    
                elif status == "failed":
                    logger.error("Nghiên cứu thất bại!")
                    print("\nNghiên cứu thất bại!")
                    
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
                    
                    logger.info("=== KẾT THÚC KIỂM TRA FLOW NGHIÊN CỨU - THẤT BẠI ===")
                    return None
                
                # Đợi trước khi kiểm tra lại
                if attempt < max_attempts - 1:
                    logger.info(f"Đợi {delay_seconds} giây trước lần kiểm tra tiếp theo")
                    print(f"Đợi {delay_seconds} giây...")
                    time.sleep(delay_seconds)
                    
            except requests.RequestException as e:
                logger.error(f"Lỗi khi gửi request: {str(e)}")
                print(f"Lỗi khi gửi request: {str(e)}")
                time.sleep(delay_seconds)
        
        logger.warning("Đã hết thời gian chờ, nghiên cứu vẫn chưa hoàn thành")
        print("\nĐã hết thời gian chờ, nghiên cứu vẫn chưa hoàn thành.")
        logger.info("=== KẾT THÚC KIỂM TRA FLOW NGHIÊN CỨU - TIMEOUT ===")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi tạo yêu cầu nghiên cứu: {str(e)}")
        print(f"Lỗi: {str(e)}")
        logger.info("=== KẾT THÚC KIỂM TRA FLOW NGHIÊN CỨU - LỖI ===")
        return None

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 