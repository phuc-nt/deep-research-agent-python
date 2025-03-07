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
            logging.FileHandler("logs/test_research_phase1.log"),
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
    Chạy quá trình nghiên cứu từ đầu đến khi hoàn thành việc viết nội dung cho tất cả sections:
    1. Tạo yêu cầu nghiên cứu
    2. Theo dõi tiến độ đến khi hoàn thành phase nghiên cứu
    3. Lưu thông tin sections để sử dụng cho phase chỉnh sửa sau này
    """
    logger.info("=== BẮT ĐẦU KIỂM TRA PHASE 1: TỪ ĐẦU ĐẾN KHI HOÀN THÀNH VIẾT NỘI DUNG CHO TẤT CẢ SECTIONS ===")
    
    # Dữ liệu yêu cầu nghiên cứu
    research_request = {
        "query": "tại sao con gái thích tặng quà"
    }
    
    logger.info(f"Tạo yêu cầu nghiên cứu: {research_request}")
    print("1. Tạo yêu cầu nghiên cứu...")
    
    try:
        response = requests.post(f"{BASE_URL}/research", json=research_request)
        response.raise_for_status()
        
        data = response.json()
        research_id = data["id"]
        logger.info(f"Đã tạo research task với ID: {research_id}")
        print(f"Đã tạo research task với ID: {research_id}")
        
        # Theo dõi tiến độ
        max_attempts = 100
        delay_seconds = 5
        
        logger.info(f"Bắt đầu theo dõi tiến độ nghiên cứu (tối đa {max_attempts} lần kiểm tra)")
        print("\n2. Theo dõi tiến độ nghiên cứu...")
        
        outline = None
        sections = []
        
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
                
                # Nếu đã hoàn thành phase nghiên cứu hoặc đang ở phase chỉnh sửa
                if status in ["editing", "completed"]:
                    logger.info("Phase nghiên cứu đã hoàn thành!")
                    print("\n3. Phase nghiên cứu đã hoàn thành!")
                    
                    # Lấy thông tin task
                    result_response = requests.get(f"{BASE_URL}/research/{research_id}")
                    result_response.raise_for_status()
                    result = result_response.json()
                    
                    # Lấy thông tin sections
                    sections = result.get('sections', [])
                    
                    # Ghi log chi tiết về sections
                    logger.info(f"Đã nghiên cứu {len(sections)} sections")
                    
                    print(f"\nĐã nghiên cứu {len(sections)} sections:")
                    for i, section in enumerate(sections):
                        section_title = section['title']
                        content_length = len(section.get('content', '')) if section.get('content') else 0
                        sources_count = len(section.get('sources', [])) if section.get('sources') else 0
                        
                        logger.info(f"Section {i+1}: {section_title} - {content_length} ký tự, {sources_count} nguồn")
                        print(f"  {i+1}. {section_title} - {content_length} ký tự, {sources_count} nguồn")
                    
                    # Lưu thông tin sections vào file để sử dụng cho phase 2
                    output_dir = Path("data/test_output")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    
                    output_file = output_dir / f"research_phase1_{research_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "research_id": research_id,
                            "request": research_request,
                            "outline": result.get('outline'),
                            "sections": sections
                        }, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Đã lưu thông tin nghiên cứu vào file: {output_file}")
                    print(f"\nĐã lưu thông tin nghiên cứu vào file: {output_file}")
                    
                    logger.info("=== KẾT THÚC KIỂM TRA PHASE 1 - THÀNH CÔNG ===")
                    return True
                    
                elif status == "failed":
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
                    
                    logger.info("=== KẾT THÚC KIỂM TRA PHASE 1 - THẤT BẠI ===")
                    return False
                
                # Nếu đang ở giai đoạn tạo dàn ý hoặc nghiên cứu, kiểm tra outline
                if status in ["outlining", "researching"]:
                    try:
                        outline_response = requests.get(f"{BASE_URL}/research/{research_id}/outline")
                        if outline_response.status_code == 200:
                            outline = outline_response.json()
                            
                            if outline:
                                sections = outline.get("sections", [])
                                logger.info(f"Đã có dàn ý với {len(sections)} phần")
                                
                                print("\nĐã có dàn ý:")
                                for i, section in enumerate(sections):
                                    section_title = section['title']
                                    logger.info(f"Phần {i+1}: {section_title}")
                                    print(f"  {i+1}. {section_title}")
                    except Exception as e:
                        logger.warning(f"Không thể lấy thông tin dàn ý: {str(e)}")
                
                # Đợi trước khi kiểm tra lại
                if attempt < max_attempts - 1:
                    logger.info(f"Đợi {delay_seconds} giây trước lần kiểm tra tiếp theo")
                    print(f"Đợi {delay_seconds} giây...")
                    time.sleep(delay_seconds)
                    
            except requests.RequestException as e:
                logger.error(f"Lỗi khi gửi request: {str(e)}")
                print(f"Lỗi khi gửi request: {str(e)}")
                time.sleep(delay_seconds)
        
        logger.warning("Đã hết thời gian chờ, phase nghiên cứu vẫn chưa hoàn thành")
        print("\nĐã hết thời gian chờ, phase nghiên cứu vẫn chưa hoàn thành.")
        logger.info("=== KẾT THÚC KIỂM TRA PHASE 1 - TIMEOUT ===")
        return False
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi tạo yêu cầu nghiên cứu: {str(e)}")
        print(f"Lỗi: {str(e)}")
        logger.info("=== KẾT THÚC KIỂM TRA PHASE 1 - LỖI ===")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 