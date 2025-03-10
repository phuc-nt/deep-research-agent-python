from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.factory import init_service_factory

from app.api.routes import router

# Khởi tạo settings
settings = get_settings()

# Khởi tạo service factory
init_service_factory(settings)

app = FastAPI(
    title="Deep Research Agent API",
    description="""
    API for automated research using AI. Hệ thống cung cấp khả năng thực hiện toàn bộ quy trình nghiên cứu tự động, 
    bao gồm phân tích yêu cầu, tạo dàn ý, nghiên cứu chi tiết, và chỉnh sửa cuối cùng.
    
    ## Quy trình nghiên cứu
    
    1. **Phân tích yêu cầu**: Hiểu nội dung cần nghiên cứu, xác định scope và đối tượng
    2. **Tạo dàn ý**: Xây dựng dàn ý chi tiết cho bài nghiên cứu
    3. **Nghiên cứu**: Thực hiện nghiên cứu cho từng phần của dàn ý
    4. **Chỉnh sửa**: Hoàn thiện nội dung, đảm bảo tính mạch lạc và chất lượng
    5. **Lưu trữ**: Lưu trữ kết quả và (tùy chọn) đăng lên GitHub
    
    ## Lưu ý
    
    - Mỗi phần trong bài nghiên cứu sẽ có độ dài từ 350-400 từ
    - Trong quá trình chỉnh sửa, nội dung gốc được giữ nguyên độ dài và chi tiết
    - Các endpoints có thể thực hiện nghiên cứu đầy đủ hoặc từng phần
    
    Chi tiết về luồng tương tác của từng API có thể xem tại [Sequence Diagrams](../docs/sequence_diagrams.md).
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Health",
            "description": "Endpoints kiểm tra trạng thái hệ thống"
        },
        {
            "name": "Research",
            "description": "Các endpoints để tạo và quản lý nghiên cứu"
        }
    ],
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes
app.include_router(router, prefix="/api/v1") 