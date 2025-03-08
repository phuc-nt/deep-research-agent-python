# Deep Research Agent

Một agent thông minh giúp thực hiện nghiên cứu chuyên sâu và tạo ra các bài viết phân tích chất lượng cao. Hệ thống hỗ trợ quy trình hoàn chỉnh từ phân tích yêu cầu nghiên cứu đến tạo dàn ý, nghiên cứu chi tiết, và chỉnh sửa bài viết.

Dự án này bao gồm [tài liệu API chi tiết](docs/api.md) và [sequence diagrams](docs/sequence_diagrams.md) mô tả luồng tương tác giữa các thành phần trong hệ thống, giúp người dùng dễ dàng hiểu và tích hợp với hệ thống.

## Tính năng

- Phân tích yêu cầu nghiên cứu và tự động tạo các nhiệm vụ chi tiết
- Tạo đề cương nghiên cứu chi tiết dựa trên các yêu cầu
- Tiến hành nghiên cứu chuyên sâu và tổng hợp kết quả
- Tạo nội dung đầy đủ và định dạng cho tài liệu cuối cùng
- Hỗ trợ lưu trữ và quản lý nội dung trên GitHub
- Theo dõi tiến độ chi tiết của quá trình nghiên cứu
- Theo dõi chi phí sử dụng LLM và search API theo từng task
- Tối ưu hóa lưu trữ dữ liệu và giảm thiểu dư thừa
- Phân tích thông minh ngay cả khi chỉ cung cấp câu hỏi nghiên cứu
- Cơ chế validation và retry để đảm bảo chất lượng

## Quy trình hoạt động

> Xem thêm: [Biểu đồ tổng quan quy trình nghiên cứu hoàn chỉnh](docs/sequence_diagrams.md#tóm-tắt-quy-trình-nghiên-cứu-hoàn-chỉnh)

```mermaid
graph TD
    Client[Client/API Consumers] --> API[API Layer]
    
    subgraph "Backend Services"
        API --> Prepare[Prepare Service]
        API --> Research[Research Service]
        API --> Edit[Edit Service]
        API --> Storage[Storage Service]
        API --> Cost[Cost Monitoring Service]
        
        Prepare --> LLM1[LLM Service]
        Prepare --> Search1[Search Service]
        Research --> LLM2[LLM Service]
        Research --> Search2[Search Service]
        Edit --> LLM3[LLM Service]
        
        Storage --> FileSystem[File System]
        Storage --> GitHub[GitHub Storage]
        
        LLM1 --> Cost
        LLM2 --> Cost
        LLM3 --> Cost
        Search1 --> Cost
        Search2 --> Cost
    end
    
    style API fill:#f9f,stroke:#333,stroke-width:2px
    style Cost fill:#bbf,stroke:#333,stroke-width:2px
```

Hệ thống được thiết kế theo kiến trúc module hóa cao, bao gồm các thành phần chính:

1. **API Layer**: Cung cấp các endpoints RESTful để tương tác với hệ thống.
   - Xử lý yêu cầu từ người dùng
   - Điều phối các services liên quan
   - Cập nhật và theo dõi tiến độ nghiên cứu

2. **Backend Services**:
   - **Prepare Service**: Phân tích yêu cầu và tạo dàn ý nghiên cứu
   - **Research Service**: Thực hiện nghiên cứu cho từng phần của dàn ý
   - **Edit Service**: Chỉnh sửa và tổng hợp nội dung thành bài viết hoàn chỉnh
   - **Storage Service**: Quản lý lưu trữ và truy xuất dữ liệu

3. **External Services**:
   - **LLM Service**: Tương tác với các mô hình ngôn ngữ lớn (OpenAI, Claude)
   - **Search Service**: Tìm kiếm thông tin từ các nguồn (Google, Perplexity)
   - **GitHub Storage**: Lưu trữ và quản lý kết quả nghiên cứu trên GitHub

4. **Quy trình nghiên cứu**:
   - Phân tích yêu cầu → Tạo dàn ý → Nghiên cứu từng phần → Chỉnh sửa nội dung → Lưu trữ kết quả

Kiến trúc này đảm bảo tính module hóa cao, dễ bảo trì và mở rộng, đồng thời cho phép theo dõi tiến độ chi tiết trong từng giai đoạn của quá trình nghiên cứu.

## Cấu trúc dự án

```
app/
├── api/                      # API endpoints
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   └── routes.py            # API routes
├── core/                     # Core functionality
│   ├── __init__.py
│   ├── config.py            # Configuration
│   ├── factory.py           # Service factory
│   └── logging.py           # Logging setup
├── models/                   # Data models
│   ├── __init__.py
│   ├── research.py          # Research models
│   └── cost.py              # Cost models
├── services/
│   ├── core/                # Các dịch vụ cơ bản
│   │   ├── llm/            # Dịch vụ xử lý ngôn ngữ
│   │   │   ├── base.py
│   │   │   ├── openai.py   # OpenAI service
│   │   │   └── claude.py   # Claude service
│   │   ├── monitoring/     # Dịch vụ theo dõi
│   │   │   ├── __init__.py
│   │   │   ├── cost.py     # Theo dõi chi phí
│   │   │   └── custom_pricing.py # Cấu hình giá
│   │   ├── search/         # Dịch vụ tìm kiếm
│   │   │   ├── base.py
│   │   │   ├── google.py   # Google search
│   │   │   └── perplexity.py # Perplexity search
│   │   └── storage/        # Dịch vụ lưu trữ
│   │       ├── base.py
│   │       └── github.py   # GitHub storage
│   ├── research/           # Các dịch vụ nghiệp vụ
│   │   ├── base.py        # Base classes
│   │   ├── prepare.py     # Chuẩn bị nghiên cứu
│   │   ├── research.py    # Thực hiện nghiên cứu
│   │   ├── edit.py        # Chỉnh sửa nội dung
│   │   └── storage.py     # Lưu trữ dữ liệu nghiên cứu
│   └── __init__.py
└── utils/                   # Các tiện ích
    ├── __init__.py
    └── helpers.py          # Hàm tiện ích
```

## Cấu trúc dữ liệu

```
data/
├── research_tasks/          # Thư mục chứa dữ liệu nghiên cứu
│   ├── {task_id}/          # Thư mục của mỗi task
│   │   ├── task.json       # Thông tin cơ bản của task
│   │   ├── outline.json    # Dàn ý nghiên cứu
│   │   ├── sections.json   # Nội dung các phần đã nghiên cứu
│   │   └── result.json     # Kết quả cuối cùng
└── test_output/            # Thư mục chứa kết quả test
    └── research_phase1_{task_id}.json  # Kết quả test phase 1
    └── research_phase2_{task_id}.json  # Kết quả test phase 2
```

## Mô hình dữ liệu

### ResearchRequest
Chứa thông tin về yêu cầu nghiên cứu:
- `query`: Câu hỏi hoặc chủ đề nghiên cứu
- `topic`: Chủ đề nghiên cứu (tùy chọn)
- `scope`: Phạm vi nghiên cứu (tùy chọn)
- `target_audience`: Đối tượng đọc (tùy chọn)

### ResearchOutline
Chứa thông tin về dàn ý nghiên cứu:
- `sections`: Danh sách các phần trong bài nghiên cứu

### ResearchSection
Chứa thông tin về một phần của bài nghiên cứu:
- `title`: Tiêu đề phần
- `description`: Mô tả phần
- `content`: Nội dung chi tiết (chỉ có sau khi đã nghiên cứu)

### ResearchResult
Chứa kết quả nghiên cứu hoàn chỉnh:
- `title`: Tiêu đề bài nghiên cứu
- `content`: Nội dung bài nghiên cứu
- `sections`: Các phần của bài nghiên cứu
- `sources`: Danh sách nguồn tham khảo

### ResearchResponse
Chứa phản hồi cho yêu cầu nghiên cứu:
- `id`: ID của research task
- `status`: Trạng thái hiện tại
- `request`: Yêu cầu nghiên cứu gốc
- `outline`: Dàn ý nghiên cứu
- `sections`: Các phần đã nghiên cứu
- `result`: Kết quả nghiên cứu
- `error`: Thông tin lỗi nếu có
- `github_url`: URL của repository trên GitHub
- `progress_info`: Thông tin chi tiết về tiến độ nghiên cứu
- `created_at`: Thời điểm tạo
- `updated_at`: Thời điểm cập nhật cuối

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/yourusername/deep-research-agent.git
cd deep-research-agent
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Cấu hình environment variables:
Tạo file `.env` với các biến môi trường sau:
```
# LLM Services
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Search Services
PERPLEXITY_API_KEY=your_perplexity_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id

# Storage Services
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username
GITHUB_REPO=your_github_repo
```

## Sử dụng

### Chạy ứng dụng:
```bash
python run.py
```

### API Endpoints:

1. Tạo yêu cầu nghiên cứu mới:
```
POST /research
```
[Chi tiết API →](docs/api.md#tạo-yêu-cầu-nghiên-cứu-mới) | [Sequence diagram →](docs/sequence_diagrams.md#1-post-research---tạo-yêu-cầu-nghiên-cứu-mới)

Body:
```json
{
  "query": "Chủ đề cần nghiên cứu",
  "topic": "Chủ đề chi tiết (tùy chọn)",
  "scope": "Phạm vi nghiên cứu (tùy chọn)",
  "target_audience": "Đối tượng đọc (tùy chọn)"
}
```

2. Kiểm tra trạng thái và tiến độ nghiên cứu:
```
GET /research/{research_id}/status
```
[Chi tiết API →](docs/api.md#lấy-trạng-thái-nghiên-cứu) | [Sequence diagram →](docs/sequence_diagrams.md#5-get-researchresearch_idstatus---lấy-trạng-thái-hiện-tại-của-yêu-cầu-nghiên-cứu)

3. Theo dõi tiến trình chi tiết:
```
GET /research/{research_id}/progress
```
[Chi tiết API →](docs/api.md#lấy-thông-tin-tiến-độ-chi-tiết) | [Sequence diagram →](docs/sequence_diagrams.md#6-get-researchresearch_idprogress---lấy-thông-tin-tiến-độ-chi-tiết)

4. Lấy kết quả nghiên cứu:
```
GET /research/{research_id}
```
[Chi tiết API →](docs/api.md#lấy-thông-tin-và-kết-quả-nghiên-cứu) | [Sequence diagram →](docs/sequence_diagrams.md#4-get-researchresearch_id---lấy-thông-tin-và-kết-quả-nghiên-cứu)

5. Chỉ thực hiện giai đoạn chỉnh sửa (sử dụng dữ liệu có sẵn):
```
POST /research/edit_only
```
[Chi tiết API →](docs/api.md#chỉ-thực-hiện-giai-đoạn-chỉnh-sửa) | [Sequence diagram →](docs/sequence_diagrams.md#3-post-researchedit_only---chỉnh-sửa-nội-dung-nghiên-cứu-sẵn-có)

Body:
```json
{
  "task_id": "id_của_nghiên_cứu_đã_có"
}
```

6. Tạo và thực hiện yêu cầu nghiên cứu hoàn chỉnh (tự động):
```
POST /research/complete
```
[Chi tiết API →](docs/api.md#tạo-yêu-cầu-nghiên-cứu-hoàn-chỉnh-tự-động) | [Sequence diagram →](docs/sequence_diagrams.md#2-post-researchcomplete---tạo-yêu-cầu-nghiên-cứu-hoàn-chỉnh-tự-động)

Body:
```json
{
  "query": "Chủ đề cần nghiên cứu"
}
```

### Ví dụ sử dụng với curl:
```bash
# Tạo yêu cầu nghiên cứu mới
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Sự phát triển của trí tuệ nhân tạo ở Việt Nam"}'

# Kiểm tra trạng thái
curl -X GET "http://localhost:8000/research/{task_id}/status"

# Theo dõi tiến trình chi tiết
curl -X GET "http://localhost:8000/research/{task_id}/progress"

# Lấy kết quả
curl -X GET "http://localhost:8000/research/{task_id}"
```

## Các cải tiến mới

### Quy trình nghiên cứu tự động hoàn chỉnh
- Endpoint mới `/research/complete` cho phép thực hiện toàn bộ quy trình từ đầu đến cuối với một lần gọi API
- Tự động phát hiện khi nghiên cứu hoàn thành và chuyển sang giai đoạn chỉnh sửa
- Theo dõi tiến độ chi tiết xuyên suốt qua các giai đoạn
- Tự động xử lý quá trình lưu trữ và đăng kết quả lên GitHub

### Theo dõi chi phí
- Hệ thống ghi nhận và theo dõi chi phí theo từng task nghiên cứu
- Tính toán chi phí chi tiết cho các yêu cầu LLM và search
- Lưu trữ thông tin chi phí theo từng giai đoạn của quá trình nghiên cứu
- Cung cấp báo cáo chi phí tổng hợp cho mỗi task nghiên cứu
- Tùy chỉnh mức giá theo từng nhà cung cấp dịch vụ (OpenAI, Claude, Perplexity)

### Theo dõi tiến độ chi tiết
- Thêm trường `progress_info` trong `ResearchResponse` để cung cấp thông tin chi tiết về tiến độ
- Theo dõi từng bước nhỏ trong quá trình nghiên cứu, bao gồm phân tích, tạo dàn ý, nghiên cứu từng phần, và chỉnh sửa
- Thông tin thời gian xử lý cho mỗi giai đoạn

### Cải thiện xử lý lỗi
- Xử lý tốt hơn các tình huống khi file không tồn tại
- Thay thế lỗi bằng cảnh báo khi phù hợp
- Cơ chế retry và validation để đảm bảo chất lượng kết quả

### Tối ưu lưu trữ dữ liệu
- Cải thiện cấu trúc lưu trữ dữ liệu để giảm thiểu dư thừa
- Tách biệt giữa thông tin cơ bản và dữ liệu chi tiết
- Hỗ trợ việc tiếp tục nghiên cứu từ các giai đoạn trước đó

### Phân tích yêu cầu thông minh
- Phân tích tự động yêu cầu nghiên cứu khi người dùng chỉ cung cấp câu hỏi
- Trích xuất chủ đề, phạm vi và đối tượng đọc từ yêu cầu
- Đảm bảo dàn ý phù hợp với yêu cầu nghiên cứu gốc

### Cơ chế validation
- Validation dữ liệu đầu vào để đảm bảo tính nhất quán
- Kiểm tra sự phù hợp của dàn ý với chủ đề nghiên cứu
- Cơ chế retry tự động khi nhận được kết quả không hợp lệ

## Luồng xử lý chính

1. **Prepare Phase**:
   - Phân tích yêu cầu nghiên cứu (`analyze_query`)
   - Tạo dàn ý chi tiết (`create_outline`)
   - Validation dàn ý đảm bảo phù hợp với yêu cầu

2. **Research Phase**:
   - Nghiên cứu từng phần của dàn ý (`research_section`)
   - Cập nhật tiến độ thông qua callback
   - Lưu trữ thông tin nghiên cứu

3. **Edit Phase**:
   - Tổng hợp nội dung từ các phần
   - Chỉnh sửa và định dạng bài viết
   - Tạo tiêu đề và trích dẫn nguồn
   - Lưu trữ kết quả cuối cùng

## Testing

Chạy tests:
```bash
pytest tests/ -v
```

Chạy test research phase 1:
```bash
python test_research_phase1.py
```

Chạy test research phase 2:
```bash
python test_research_phase2.py
```

## Contributing

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/your-feature`)
3. Commit thay đổi (`git commit -am 'Add new feature'`)
4. Push lên branch (`git push origin feature/your-feature`)
5. Tạo Pull Request

## License

MIT License - xem [LICENSE](LICENSE) để biết thêm chi tiết.

## Tài liệu

Hệ thống được cung cấp kèm theo các tài liệu chi tiết để giúp bạn hiểu rõ và sử dụng hiệu quả:

- [Tài liệu API](docs/api.md) - Chi tiết về các endpoints API, cách sử dụng và mô tả response/request
- [Sequence Diagrams](docs/sequence_diagrams.md) - Biểu đồ tuần tự mô tả luồng tương tác giữa các thành phần
- [Mô hình dữ liệu](docs/api.md#mô-hình-dữ-liệu) - Chi tiết về cấu trúc dữ liệu được sử dụng
- [Quy trình nghiên cứu](docs/api.md#quy-trình-nghiên-cứu-cải-tiến) - Mô tả chi tiết về quy trình hoạt động

## Chạy với Docker

Deep Research Agent có thể được chạy dễ dàng bằng Docker. Dưới đây là các bước để chạy ứng dụng trong container:

### Yêu cầu
- Docker và Docker Compose đã được cài đặt
- API keys cho các dịch vụ (OpenAI, Anthropic, Google, GitHub)

### Cài đặt và chạy

1. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/deep-research-agent.git
   cd deep-research-agent
   ```

2. **Sao chép file .env.example thành .env và cấu hình các biến môi trường:**
   ```bash
   cp .env.example .env
   ```
   Mở file .env và cập nhật các API keys và cấu hình khác:
   ```
   # API Keys
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_google_cse_id
   
   # GitHub Configuration
   GITHUB_ACCESS_TOKEN=your_github_access_token
   GITHUB_USERNAME=your_github_username
   GITHUB_REPO=your_github_repo
   ```

3. **Xây dựng và chạy container với Docker Compose:**
   ```bash
   docker compose up -d --build
   ```
   Lệnh này sẽ:
   - Xây dựng image từ Dockerfile
   - Tạo và chạy container trong chế độ detached (chạy nền)
   - Cấu hình volumes cho dữ liệu và logs
   - Thiết lập biến môi trường từ file .env

4. **Kiểm tra logs:**
   ```bash
   docker compose logs -f
   ```
   Sử dụng flag `-f` để theo dõi logs theo thời gian thực.

5. **Kiểm tra trạng thái container:**
   ```bash
   docker compose ps
   ```

6. **Truy cập API:**
   - API có sẵn tại: http://localhost:8000/api/v1
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

7. **Dừng container:**
   ```bash
   docker compose down
   ```

### Quản lý dữ liệu

Dữ liệu nghiên cứu được lưu trữ trong thư mục `./data` trên máy host, được mount vào container. Điều này đảm bảo dữ liệu được giữ lại ngay cả khi container bị xóa.

Cấu trúc thư mục dữ liệu:
```
data/
├── research_tasks/          # Thư mục chứa dữ liệu nghiên cứu
│   ├── {task_id}/          # Thư mục của mỗi task
│   │   ├── task.json       # Thông tin cơ bản của task
│   │   ├── outline.json    # Dàn ý nghiên cứu
│   │   ├── sections.json   # Nội dung các phần đã nghiên cứu
│   │   └── result.json     # Kết quả cuối cùng
```

### Xử lý lỗi phổ biến

1. **Lỗi "command not found: docker-compose"**:
   - Sử dụng `docker compose` (có khoảng cách) thay vì `docker-compose` trong Docker mới.

2. **Lỗi "executable file not found in $PATH"**:
   - Đảm bảo tất cả dependencies đã được liệt kê trong requirements.txt.
   - Kiểm tra xem uvicorn và fastapi đã được thêm vào requirements.txt chưa.

3. **Lỗi kết nối API**:
   - Kiểm tra xem container có đang chạy không với lệnh `docker compose ps`.
   - Kiểm tra logs với lệnh `docker compose logs`.
   - Đảm bảo cổng 8000 không bị sử dụng bởi ứng dụng khác.

4. **Lỗi API keys**:
   - Đảm bảo tất cả API keys đã được cấu hình đúng trong file .env.
   - Kiểm tra logs để xem lỗi xác thực API.

### Cấu hình nâng cao

Bạn có thể điều chỉnh cấu hình trong file `docker-compose.yml` để phù hợp với nhu cầu của mình:

- **Thay đổi cổng**: Chỉnh sửa `ports: - "8000:8000"` thành cổng mong muốn
- **Thay đổi biến môi trường**: Cập nhật phần `environment` hoặc file `.env`
- **Thêm volumes**: Cấu hình thêm volumes nếu cần
- **Tùy chỉnh healthcheck**: Điều chỉnh các tham số healthcheck để phù hợp với môi trường

### Build từ source code

Nếu bạn muốn build từ source code mà không sử dụng Docker:

1. **Cài đặt Python 3.11**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv
   
   # macOS
   brew install python@3.11
   ```

2. **Tạo và kích hoạt môi trường ảo**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Cài đặt dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Chạy ứng dụng**:
   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
