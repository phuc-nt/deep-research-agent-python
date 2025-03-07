import asyncio
import json
import time
import requests
import logging
import sys
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
    Chạy full flow của quá trình nghiên cứu:
    1. Tạo yêu cầu nghiên cứu
    2. Theo dõi tiến độ
    3. Kiểm tra kết quả và URL GitHub
    """
    logger.info("=== BẮT ĐẦU KIỂM TRA QUÁ TRÌNH NGHIÊN CỨU ===")
    
    # Dữ liệu yêu cầu nghiên cứu
    research_request = {
        "query": "Sự cực đoan của chủ nghĩa dân tọc ở Việt Nam"
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
                
                # Nếu đã hoàn thành, lấy kết quả
                if status == "completed":
                    logger.info("Nghiên cứu đã hoàn thành!")
                    print("\n3. Nghiên cứu đã hoàn thành!")
                    
                    result_response = requests.get(f"{BASE_URL}/research/{research_id}")
                    result_response.raise_for_status()
                    result = result_response.json()
                    
                    # Ghi log chi tiết về kết quả
                    title = result.get('result', {}).get('title', 'N/A')
                    sections_count = len(result.get('result', {}).get('sections', []))
                    sources_count = len(result.get('result', {}).get('sources', []))
                    
                    logger.info(f"Kết quả - Tiêu đề: {title}")
                    logger.info(f"Kết quả - Số phần: {sections_count}")
                    logger.info(f"Kết quả - Số nguồn tham khảo: {sources_count}")
                    
                    print("\nThông tin kết quả:")
                    print(f"- Tiêu đề: {title}")
                    print(f"- Số phần: {sections_count}")
                    print(f"- Số nguồn tham khảo: {sources_count}")
                    
                    # Kiểm tra GitHub URL
                    github_url = result.get("github_url")
                    if github_url:
                        logger.info(f"Kết quả đã được lưu trên GitHub: {github_url}")
                        print(f"\nKết quả đã được lưu trên GitHub: {github_url}")
                    else:
                        logger.warning("Không có thông tin về GitHub URL")
                        print("\nKhông có thông tin về GitHub URL")
                    
                    logger.info("=== KẾT THÚC KIỂM TRA - THÀNH CÔNG ===")
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
                    
                    logger.info("=== KẾT THÚC KIỂM TRA - THẤT BẠI ===")
                    return False
                
                # Nếu đang ở giai đoạn tạo dàn ý hoặc sau đó, kiểm tra outline
                if status in ["outlining", "researching", "editing"]:
                    try:
                        outline_response = requests.get(f"{BASE_URL}/research/{research_id}/outline")
                        outline_response.raise_for_status()
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
        
        logger.warning("Đã hết thời gian chờ, nghiên cứu vẫn chưa hoàn thành")
        print("\nĐã hết thời gian chờ, nghiên cứu vẫn chưa hoàn thành.")
        logger.info("=== KẾT THÚC KIỂM TRA - TIMEOUT ===")
        return False
        
    except requests.RequestException as e:
        logger.error(f"Lỗi khi tạo yêu cầu nghiên cứu: {str(e)}")
        print(f"Lỗi: {str(e)}")
        logger.info("=== KẾT THÚC KIỂM TRA - LỖI ===")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {str(e)}")
        print(f"Lỗi không xử lý được: {str(e)}")
        sys.exit(1) 