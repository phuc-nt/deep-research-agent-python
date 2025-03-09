import json
import os
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.core.logging import logger
from app.services.core.storage.base import BaseStorageService

class FileStorageService(BaseStorageService):
    """Service lưu trữ dữ liệu vào file"""
    
    def __init__(self, base_dir: str = "data"):
        """
        Khởi tạo service với thư mục cơ sở
        
        Args:
            base_dir: Thư mục cơ sở để lưu trữ dữ liệu
        """
        self.base_dir = Path(base_dir)
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Khởi tạo FileStorageService với thư mục cơ sở: {self.base_dir}")
    
    async def save(self, data: Any, file_path: str, **kwargs) -> str:
        """
        Lưu dữ liệu vào file
        
        Args:
            data: Dữ liệu cần lưu (có thể là string hoặc object)
            file_path: Đường dẫn file tương đối so với base_dir
            
        Returns:
            str: Đường dẫn đầy đủ đến file đã lưu
        """
        try:
            # Tạo đường dẫn đầy đủ
            full_path = self.base_dir / file_path
            
            # Tạo thư mục cha nếu chưa tồn tại
            os.makedirs(full_path.parent, exist_ok=True)
            
            # Xác định loại dữ liệu và lưu phù hợp
            if isinstance(data, (dict, list)):
                # Lưu dữ liệu dạng JSON
                async with asyncio.Lock():
                    with open(full_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # Lưu dữ liệu dạng string
                async with asyncio.Lock():
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(str(data))
            
            logger.info(f"Đã lưu dữ liệu vào file: {full_path}")
            return str(full_path)
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu vào file {file_path}: {str(e)}")
            raise
    
    async def load(self, file_path: str, as_json: bool = True, **kwargs) -> Any:
        """
        Đọc dữ liệu từ file
        
        Args:
            file_path: Đường dẫn file tương đối so với base_dir
            as_json: Có parse dữ liệu dưới dạng JSON hay không
            
        Returns:
            Any: Dữ liệu đã đọc
            
        Raises:
            FileNotFoundError: Nếu file không tồn tại
        """
        try:
            # Tạo đường dẫn đầy đủ
            full_path = self.base_dir / file_path
            
            # Kiểm tra file tồn tại
            if not full_path.exists():
                logger.error(f"File không tồn tại: {full_path}")
                raise FileNotFoundError(f"File không tồn tại: {full_path}")
            
            # Đọc dữ liệu
            async with asyncio.Lock():
                with open(full_path, 'r', encoding='utf-8') as f:
                    if as_json:
                        data = json.load(f)
                    else:
                        data = f.read()
            
            logger.info(f"Đã đọc dữ liệu từ file: {full_path}")
            return data
            
        except json.JSONDecodeError:
            logger.error(f"Lỗi khi parse JSON từ file {file_path}")
            raise
        except Exception as e:
            logger.error(f"Lỗi khi đọc dữ liệu từ file {file_path}: {str(e)}")
            raise
    
    async def delete(self, file_path: str, **kwargs) -> bool:
        """
        Xóa file
        
        Args:
            file_path: Đường dẫn file tương đối so với base_dir
            
        Returns:
            bool: True nếu xóa thành công, False nếu file không tồn tại
        """
        try:
            # Tạo đường dẫn đầy đủ
            full_path = self.base_dir / file_path
            
            # Kiểm tra file tồn tại
            if not full_path.exists():
                logger.warning(f"File không tồn tại khi cố gắng xóa: {full_path}")
                return False
            
            # Xóa file
            os.remove(full_path)
            logger.info(f"Đã xóa file: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi xóa file {file_path}: {str(e)}")
            raise
    
    async def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        """
        Liệt kê các file trong thư mục
        
        Args:
            directory: Thư mục tương đối so với base_dir
            pattern: Mẫu để lọc file
            
        Returns:
            List[str]: Danh sách đường dẫn tương đối của các file
        """
        try:
            # Tạo đường dẫn đầy đủ
            full_path = self.base_dir / directory
            
            # Kiểm tra thư mục tồn tại
            if not full_path.exists():
                logger.warning(f"Thư mục không tồn tại: {full_path}")
                return []
            
            # Liệt kê các file
            files = list(full_path.glob(pattern))
            
            # Chuyển đổi sang đường dẫn tương đối so với base_dir
            relative_paths = [str(f.relative_to(self.base_dir)) for f in files if f.is_file()]
            
            logger.info(f"Đã liệt kê {len(relative_paths)} file trong thư mục {directory}")
            return relative_paths
            
        except Exception as e:
            logger.error(f"Lỗi khi liệt kê file trong thư mục {directory}: {str(e)}")
            raise
    
    def save_data(self, data: Any, file_path: str) -> str:
        """
        Lưu dữ liệu vào file (phương thức đồng bộ)
        
        Args:
            data: Dữ liệu cần lưu (có thể là string hoặc object)
            file_path: Đường dẫn file tương đối so với base_dir
            
        Returns:
            str: Đường dẫn đầy đủ đến file đã lưu
        """
        try:
            # Tạo đường dẫn đầy đủ
            full_path = os.path.join(self.base_dir, file_path)
            
            # Tạo thư mục cha nếu chưa tồn tại
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Xác định loại dữ liệu và lưu phù hợp
            if isinstance(data, (dict, list)):
                # Lưu dữ liệu dạng JSON
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # Lưu dữ liệu dạng string
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
            
            logger.info(f"Đã lưu dữ liệu vào file: {full_path}")
            return str(full_path)
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu vào file {file_path}: {str(e)}")
            raise 