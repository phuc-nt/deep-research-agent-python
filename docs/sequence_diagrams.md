# Sequence Diagrams cho API Endpoints

## 1. POST `/research` - Tạo yêu cầu nghiên cứu mới

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant PrepareService
    participant ResearchService
    participant StorageService
    participant LLMService
    participant SearchService
    
    Client->>API: POST /research (request)
    Note over Client,API: {query, topic?, scope?, target_audience?}
    
    API->>+StorageService: Tạo task mới (task_id)
    StorageService-->>-API: Task đã tạo
    
    API->>Client: Trả về task_id (status: pending)
    Note over API,Client: Background task bắt đầu
    
    API->>+PrepareService: analyze_query(query)
    PrepareService->>+LLMService: Analyze query
    LLMService-->>-PrepareService: Kết quả phân tích
    PrepareService-->>-API: Analysis (topic, scope, target_audience)
    
    API->>+StorageService: Cập nhật task (analysis)
    StorageService-->>-API: Task đã cập nhật
    
    API->>+PrepareService: create_outline(request)
    PrepareService->>+LLMService: Generate outline
    LLMService-->>-PrepareService: Outline
    PrepareService-->>-API: Outline (sections)
    
    API->>+StorageService: Lưu outline
    StorageService-->>-API: Outline đã lưu
    
    API->>+ResearchService: execute(request, outline)
    Note over ResearchService: Mỗi phần 350-400 từ
    ResearchService->>+SearchService: Tìm thông tin cho từng phần
    SearchService-->>-ResearchService: Kết quả tìm kiếm
    ResearchService->>+LLMService: Phân tích và tổng hợp
    LLMService-->>-ResearchService: Nội dung đã nghiên cứu
    ResearchService-->>-API: Sections đã nghiên cứu
    
    API->>+StorageService: Lưu sections
    StorageService-->>-API: Sections đã lưu
    
    API->>+StorageService: Cập nhật task (status: completed)
    StorageService-->>-API: Task đã cập nhật
```

## 2. POST `/research/complete` - Tạo yêu cầu nghiên cứu hoàn chỉnh (tự động)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant PrepareService
    participant ResearchService
    participant EditService
    participant StorageService
    participant GitHubService
    participant LLMService
    participant SearchService
    
    Client->>API: POST /research/complete (request)
    Note over Client,API: {query, topic?, scope?, target_audience?}
    
    API->>+StorageService: Tạo task mới (task_id)
    StorageService-->>-API: Task đã tạo
    
    API->>Client: Trả về task_id (status: pending)
    Note over API,Client: Background task bắt đầu
    
    API->>+PrepareService: analyze_query(query)
    PrepareService->>+LLMService: Analyze query
    LLMService-->>-PrepareService: Kết quả phân tích
    PrepareService-->>-API: Analysis (topic, scope, target_audience)
    
    API->>+StorageService: Cập nhật task (status: analyzing)
    StorageService-->>-API: Task đã cập nhật
    
    API->>+PrepareService: create_outline(request)
    PrepareService->>+LLMService: Generate outline
    LLMService-->>-PrepareService: Outline
    PrepareService-->>-API: Outline (sections)
    
    API->>+StorageService: Lưu outline
    StorageService-->>-API: Outline đã lưu
    
    API->>+StorageService: Cập nhật task (status: outlining)
    StorageService-->>-API: Task đã cập nhật
    
    API->>+ResearchService: execute(request, outline)
    Note over ResearchService: Mỗi phần 350-400 từ
    ResearchService->>+SearchService: Tìm thông tin cho từng phần
    SearchService-->>-ResearchService: Kết quả tìm kiếm
    ResearchService->>+LLMService: Phân tích và tổng hợp
    LLMService-->>-ResearchService: Nội dung đã nghiên cứu
    ResearchService-->>-API: Sections đã nghiên cứu
    
    API->>+StorageService: Lưu sections
    StorageService-->>-API: Sections đã lưu
    
    API->>+StorageService: Cập nhật task (status: researching)
    StorageService-->>-API: Task đã cập nhật
    
    Note over API: Tự động chuyển sang giai đoạn chỉnh sửa
    
    API->>+EditService: execute(request, outline, sections)
    Note over EditService: Không tóm tắt/rút gọn nội dung
    Note over EditService: Giữ nguyên độ dài 350-400 từ/phần
    EditService->>+LLMService: Chỉnh sửa và kết nối các phần
    LLMService-->>-EditService: Nội dung đã chỉnh sửa
    EditService-->>-API: Result (title, content, sources)
    
    API->>+StorageService: Lưu result
    StorageService-->>-API: Result đã lưu
    
    API->>+StorageService: Cập nhật task (status: editing)
    StorageService-->>-API: Task đã cập nhật
    
    API->>+GitHubService: save(content, file_path)
    GitHubService-->>-API: github_url
    
    API->>+StorageService: Cập nhật task (status: completed, github_url)
    StorageService-->>-API: Task đã cập nhật
```

## 3. POST `/research/edit_only` - Chỉnh sửa nội dung nghiên cứu sẵn có

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant EditService
    participant StorageService
    participant GitHubService
    participant LLMService
    
    Client->>API: POST /research/edit_only (request)
    Note over Client,API: {task_id}
    
    API->>+StorageService: load_full_task(task_id)
    StorageService-->>-API: Task, Outline, Sections
    
    Note over API: Kiểm tra điều kiện:
    Note over API: - Có request
    Note over API: - Có outline
    Note over API: - Có sections
    
    API->>Client: Trả về thông báo đã nhận yêu cầu
    Note over API,Client: Background task bắt đầu
    
    API->>+StorageService: Cập nhật task (status: editing)
    StorageService-->>-API: Task đã cập nhật
    
    API->>+EditService: execute(request, outline, sections)
    Note over EditService: Không tóm tắt/rút gọn nội dung
    Note over EditService: Giữ nguyên độ dài 350-400 từ/phần
    EditService->>+LLMService: Chỉnh sửa và kết nối các phần
    LLMService-->>-EditService: Nội dung đã chỉnh sửa
    EditService-->>-API: Result (title, content, sources)
    
    API->>+StorageService: Lưu result
    StorageService-->>-API: Result đã lưu
    
    API->>+GitHubService: save(content, file_path)
    GitHubService-->>-API: github_url
    
    API->>+StorageService: Cập nhật task (status: completed, github_url)
    StorageService-->>-API: Task đã cập nhật
```

## 4. GET `/research/{research_id}` - Lấy thông tin và kết quả nghiên cứu

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant StorageService
    
    Client->>API: GET /research/{research_id}
    
    API->>+StorageService: load_full_task(research_id)
    StorageService-->>-API: Task, Outline, Sections, Result
    
    API->>Client: Trả về đầy đủ thông tin
    Note over API,Client: {id, status, request, outline, sections, result, github_url, ...}
```

## 5. GET `/research/{research_id}/status` - Lấy trạng thái hiện tại của yêu cầu nghiên cứu

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant StorageService
    
    Client->>API: GET /research/{research_id}/status
    
    API->>+StorageService: load_task(research_id)
    StorageService-->>-API: Task (basic info)
    
    API->>Client: Trả về trạng thái
    Note over API,Client: {status, progress_info}
```

## 6. GET `/research/{research_id}/progress` - Lấy thông tin tiến độ chi tiết

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant StorageService
    
    Client->>API: GET /research/{research_id}/progress
    
    API->>+StorageService: load_task(research_id)
    StorageService-->>-API: Task (basic info)
    
    Alt status = analyzing hoặc outlining
        API->>+StorageService: load_task(research_id)
        StorageService-->>-API: Task details
    else status = researching
        API->>+StorageService: load_outline(research_id)
        StorageService-->>-API: Outline
    else status = editing hoặc completed
        API->>+StorageService: load_sections(research_id)
        StorageService-->>-API: Sections
    end
    
    API->>Client: Trả về thông tin tiến độ chi tiết
    Note over API,Client: {phase, message, timestamp, current_section, total_sections, ...}
```

## 7. GET `/research/list` - Lấy danh sách các yêu cầu nghiên cứu

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant StorageService
    
    Client->>API: GET /research/list
    
    API->>+StorageService: list_tasks()
    StorageService-->>-API: Danh sách task_ids
    
    loop Với mỗi task_id
        API->>+StorageService: load_task(task_id)
        StorageService-->>-API: Task (basic info)
    end
    
    API->>Client: Trả về danh sách nghiên cứu
    Note over API,Client: [{id, status, query, created_at, updated_at}, ...]
```

## Tóm tắt quy trình nghiên cứu hoàn chỉnh

```mermaid
graph TB
    A[Yêu cầu nghiên cứu] --> B[Phân tích yêu cầu]
    B --> C[Tạo dàn ý]
    C --> D[Nghiên cứu từng phần]
    D --> E[Chỉnh sửa và tổng hợp]
    E --> F[Lưu trữ kết quả]
    F --> G[Đăng lên GitHub]
    
    subgraph "Phase 1: Chuẩn bị"
        B
        C
    end
    
    subgraph "Phase 2: Nghiên cứu"
        D
    end
    
    subgraph "Phase 3: Chỉnh sửa"
        E
    end
    
    subgraph "Phase 4: Lưu trữ"
        F
        G
    end
``` 