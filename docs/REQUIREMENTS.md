# Tài liệu yêu cầu - Deep Research Agent

## 1. Giới thiệu

### 1.1 Mục đích
Deep Research Agent là một hệ thống thông minh được thiết kế để thực hiện nghiên cứu chuyên sâu và tạo ra các bài viết phân tích chất lượng cao. Hệ thống hỗ trợ quy trình hoàn chỉnh từ phân tích yêu cầu nghiên cứu đến tạo dàn ý, nghiên cứu chi tiết, và chỉnh sửa bài viết cuối cùng.

### 1.2 Phạm vi
Tài liệu này mô tả chi tiết các yêu cầu chức năng và phi chức năng cần thiết để phát triển hệ thống Deep Research Agent, bao gồm:
- Kiến trúc tổng thể
- Các thành phần chính của hệ thống
- API endpoints và luồng tương tác
- Các dịch vụ tích hợp (LLM, Search, Storage)
- Quy trình nghiên cứu và xử lý dữ liệu
- Yêu cầu về triển khai và Docker

### 1.3 Công nghệ yêu cầu
- Python 3.11.10 trở lên
- Framework FastAPI
- Các thư viện Python được liệt kê trong requirements.txt
- Docker và Docker Compose
- Async/Await framework

## 2. Kiến trúc tổng thể

### 2.1 Mô hình kiến trúc

Hệ thống sẽ được phát triển theo mô hình kiến trúc phân lớp:
1. **API Layer**: Xử lý các HTTP requests/responses và định tuyến
2. **Service Layer**: Chứa business logic của các quy trình nghiên cứu
3. **Core Services**: Các dịch vụ nền tảng (LLM, Search, Storage, Monitoring)
4. **Models**: Các Pydantic models biểu diễn dữ liệu

### 2.2 Sơ đồ thành phần

```
Client/API Consumers → API Layer → Backend Services
    
Backend Services bao gồm:
- Prepare Service: Phân tích yêu cầu và tạo dàn ý
- Research Service: Thực hiện nghiên cứu chi tiết
- Edit Service: Chỉnh sửa và tổng hợp nội dung
- Storage Service: Lưu trữ và quản lý dữ liệu
- Cost Monitoring Service: Theo dõi chi phí sử dụng

Các dịch vụ tích hợp:
- LLM Service (OpenAI, Claude)
- Search Service (Perplexity, Google)
- Storage Service (File System, GitHub)
```

## 3. Yêu cầu chức năng

### 3.1 Quy trình nghiên cứu hoàn chỉnh

Hệ thống cần hỗ trợ quy trình nghiên cứu hoàn chỉnh bao gồm các giai đoạn sau:

#### 3.1.1 Phase 1: Chuẩn bị
- Phân tích yêu cầu nghiên cứu từ người dùng
- Tạo dàn ý nghiên cứu chi tiết với các sections

#### 3.1.2 Phase 2: Nghiên cứu
- Tiến hành nghiên cứu chi tiết cho từng section trong dàn ý
- Thu thập thông tin từ các nguồn tìm kiếm
- Tổng hợp thông tin với trích dẫn nguồn

#### 3.1.3 Phase 3: Chỉnh sửa
- Chỉnh sửa nội dung nghiên cứu
- Tổng hợp thành bài viết hoàn chỉnh
- Chuẩn hóa định dạng và phong cách

#### 3.1.4 Phase 4: Lưu trữ
- Lưu trữ kết quả nghiên cứu vào hệ thống
- Hỗ trợ đăng lên GitHub (tùy chọn)

### 3.2 API Endpoints

Hệ thống cần cung cấp các API endpoints sau:

#### 3.2.1 Endpoints chính
1. `POST /api/v1/research/complete`: Tạo yêu cầu nghiên cứu hoàn chỉnh
2. `GET /api/v1/research/{research_id}`: Lấy thông tin chi tiết về một nghiên cứu
3. `GET /api/v1/research/{research_id}/status`: Kiểm tra trạng thái của nghiên cứu
4. `GET /api/v1/research/{research_id}/progress`: Lấy thông tin tiến độ chi tiết
5. `GET /api/v1/research/{research_id}/outline`: Lấy dàn ý nghiên cứu
6. `GET /api/v1/research/{research_id}/cost`: Lấy thông tin chi phí
7. `GET /api/v1/research`: Lấy danh sách các nghiên cứu

#### 3.2.2 Health Check
1. `GET /api/v1/health`: Kiểm tra trạng thái hoạt động của server

### 3.3 Các dịch vụ nền tảng

#### 3.3.1 LLM Service
- Tích hợp với OpenAI API (GPT-4, GPT-3.5)
- Tích hợp với Anthropic API (Claude)
- Hỗ trợ các tham số cho LLM (temperature, max_tokens, etc.)
- Xử lý lỗi và retry tự động

#### 3.3.2 Search Service
- Tích hợp với Perplexity API
- Tích hợp với Google Search API
- DummySearchService cho trường hợp không có API
- Xử lý lỗi và retry tự động

#### 3.3.3 Storage Service
- Lưu trữ file-based local
- Tích hợp với GitHub cho lưu trữ kết quả
- Cấu trúc lưu trữ tối ưu và hiệu quả

#### 3.3.4 Cost Monitoring Service
- Theo dõi chi phí sử dụng LLM APIs
- Theo dõi chi phí sử dụng Search APIs
- Báo cáo chi phí theo từng task

### 3.4 Service Factory Pattern

Hệ thống cần triển khai Service Factory Pattern để:
- Tạo các instances của các service
- Quản lý lifecycle của các service
- Đảm bảo khả năng mở rộng
- Hỗ trợ đổi service implementation dễ dàng

## 4. Yêu cầu phi chức năng

### 4.1 Hiệu suất
- Xử lý nhiều yêu cầu nghiên cứu đồng thời
- Tối ưu hóa việc sử dụng các API bên ngoài
- Giảm thời gian khởi động server
- Tối ưu hóa bộ nhớ khi xử lý nhiều task

### 4.2 Khả năng mở rộng
- Kiến trúc module hóa cao
- Khả năng thêm LLM providers mới
- Khả năng thêm Search services mới
- Khả năng mở rộng storage options

### 4.3 Bảo mật
- Bảo vệ API keys
- Xác thực API requests
- Kiểm soát quyền truy cập
- Xử lý dữ liệu an toàn

### 4.4 Độ tin cậy
- Cơ chế validation và retry
- Phục hồi từ lỗi
- Xử lý timeout và lỗi kết nối
- Async/Await framework cải tiến

### 4.5 Chi phí
- Theo dõi và tối ưu hóa chi phí API
- Cảnh báo vượt ngân sách
- Báo cáo chi phí chi tiết

## 5. Cấu trúc dự án

### 5.1 Cấu trúc thư mục

```
app/
├── api/                # API endpoints và routes
│   ├── main.py         # Entry point FastAPI
│   └── routes.py       # API routes
├── core/               # Core utilities
│   ├── config.py       # Cấu hình ứng dụng
│   └── factory.py      # Service factory pattern
├── models/             # Pydantic models
│   ├── cost.py         # Models cho cost monitoring
│   └── research.py     # Models cho research process
├── services/           # Business logic
│   ├── core/           # Core services
│   │   ├── llm/        # LLM services (OpenAI, Claude)
│   │   ├── monitoring/ # Cost monitoring
│   │   ├── search/     # Search services
│   │   └── storage/    # Storage services
│   └── research/       # Research services
│       ├── base.py     # Base classes cho research
│       ├── prepare.py  # Phase chuẩn bị
│       ├── research.py # Phase nghiên cứu
│       ├── edit.py     # Phase chỉnh sửa
│       └── storage.py  # Lưu trữ dữ liệu nghiên cứu
└── utils/              # Utilities
```

### 5.2 Mô hình dữ liệu

#### 5.2.1 Research Models
- `ResearchTask`: Thông tin về nhiệm vụ nghiên cứu
- `ResearchOutline`: Dàn ý nghiên cứu
- `ResearchSection`: Section trong nghiên cứu
- `ResearchProgress`: Thông tin về tiến độ

#### 5.2.2 Cost Models
- `CostRecord`: Ghi lại chi phí sử dụng API
- `CostSummary`: Tổng hợp chi phí cho một task
- `APIUsage`: Thông tin về việc sử dụng API

## 6. Triển khai

### 6.1 Docker
- Dockerfile sử dụng Python 3.11.10
- Docker Compose cho development và production
- Cấu hình volumes cho lưu trữ dữ liệu
- Health check endpoint

### 6.2 Môi trường
- Cấu hình cho các môi trường khác nhau
- Environment variables qua .env file
- Tài liệu hướng dẫn triển khai

## 7. Testing

### 7.1 Unit Tests
- Tests cho từng module và service
- Tests cho API endpoints
- Tests cho error handling

### 7.2 Integration Tests
- Tests cho quy trình end-to-end
- Tests cho interaction giữa các service
- Tests cho tích hợp với external APIs

### 7.3 End-to-End Tests
- Test scripts cho toàn bộ quy trình
- Performance benchmarking
- Stress testing

## 8. Tương lai

### 8.1 Tính năng nâng cao
- Dashboard cho monitoring research tasks
- Notification system
- Multi-model enhancement (Mistral, Gemini, etc.)
- Multi-source research
- Advanced security & authentication

### 8.2 Scaling
- Horizontal scaling
- Load balancing
- Message queue (RabbitMQ/Kafka)
- Kubernetes deployment

## 9. Tài liệu

### 9.1 API Documentation
- Tài liệu chi tiết về các API endpoints
- Request/response examples
- Sequence diagrams

### 9.2 Developer Documentation
- Setup guides
- Coding standards
- Contribution guidelines

### 9.3 User Documentation
- Hướng dẫn sử dụng
- Ví dụ thực tế
- Troubleshooting guide 