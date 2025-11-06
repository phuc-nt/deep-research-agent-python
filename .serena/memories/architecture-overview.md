# Deep Research Agent - Architecture Overview

## Project Summary
Deep Research Agent là một hệ thống AI agent thông minh giúp thực hiện nghiên cứu chuyên sâu và tạo nội dung phân tích chất lượng cao. Hệ thống hỗ trợ quy trình hoàn chỉnh từ phân tích yêu cầu nghiên cứu đến tạo outline chi tiết, nghiên cứu chuyên sâu và chỉnh sửa bài viết.

## Technology Stack
- **Language**: Python 3.11.10
- **Web Framework**: FastAPI
- **LLM Providers**: OpenAI, Anthropic Claude
- **Search Services**: Perplexity, Google Custom Search
- **Storage**: File System, GitHub

## Architecture Layers

### 1. API Layer (`app/api/`)
**Entry Point**: [app/api/main.py](app/api/main.py)
- FastAPI application setup
- CORS configuration
- Router registration

**Routes**: [app/api/routes.py](app/api/routes.py)
- `POST /api/v1/research/complete` - Tạo research request hoàn chỉnh
- `GET /api/v1/research/{research_id}` - Lấy thông tin research
- `GET /api/v1/research/{research_id}/status` - Kiểm tra trạng thái
- `GET /api/v1/research/{research_id}/outline` - Lấy outline
- `GET /api/v1/research/{research_id}/progress` - Theo dõi tiến độ
- `GET /api/v1/research/{research_id}/cost` - Xem chi phí
- `GET /api/v1/research` - Danh sách research
- Background task: `process_complete_research()` - Xử lý research bất đồng bộ

### 2. Core Services (`app/services/core/`)

#### LLM Services (`app/services/core/llm/`)
**Base Class**: [BaseLLMService](app/services/core/llm/base.py)
- Phương thức chính:
  - `generate()` - Tạo completion
  - `stream()` - Stream response
  - `count_tokens()` - Đếm tokens
  - `_log_request_cost()` - Log chi phí

**Implementations**:
- [ClaudeLLMService](app/services/core/llm/claude.py) - Anthropic Claude
- [OpenAILLMService](app/services/core/llm/openai.py) - OpenAI GPT

#### Search Services (`app/services/core/search/`)
**Base Class**: [BaseSearchService](app/services/core/search/base.py)

**Implementations**:
- [PerplexitySearchService](app/services/core/search/perplexity.py)
- [GoogleSearchService](app/services/core/search/google.py)
- [DummySearchService](app/services/core/search/dummy.py) - For testing

#### Storage Services (`app/services/core/storage/`)
**Implementations**:
- [FileStorageService](app/services/core/storage/file.py) - Local file system
- [GitHubStorageService](app/services/core/storage/github.py) - GitHub repository

#### Monitoring (`app/services/core/monitoring/`)
**Cost Tracking**: [CostMonitoringService](app/services/core/monitoring/cost.py)
- Theo dõi chi phí LLM API calls
- Theo dõi chi phí search API calls
- Pricing models cho các providers khác nhau

### 3. Research Services (`app/services/research/`)

#### PrepareService (`app/services/research/prepare.py`)
**Phase 1: Preparation**
- Phương thức chính:
  - `execute()` - Điều phối quá trình prepare
  - `analyze_query()` - Phân tích yêu cầu nghiên cứu
  - `create_outline()` - Tạo outline chi tiết
  - `_validate_analysis_relevance()` - Kiểm tra tính liên quan
  - `_manual_parse_analysis()` - Parse kết quả phân tích
  - `_validate_outline_relevance()` - Kiểm tra outline
  - `_manual_parse_outline()` - Parse outline

#### ResearchService (`app/services/research/research.py`)
**Phase 2: Research**
- Phương thức chính:
  - `execute()` - Điều phối quá trình research
  - `research_section()` - Nghiên cứu từng section
  - `_search_section_info()` - Tìm kiếm thông tin cho section

#### EditService (`app/services/research/edit.py`)
**Phase 3: Editing**
- Phương thức chính:
  - `execute()` - Điều phối quá trình editing
  - `edit_content()` - Chỉnh sửa và tổng hợp nội dung
  - `create_title()` - Tạo tiêu đề
  - `_collect_sources()` - Thu thập sources
  - `research_section()` - Research thêm nếu cần

### 4. Models (`app/models/`)

#### Research Models (`app/models/research.py`)
**Enums**:
- `ResearchStatus`: PENDING, ANALYZING, OUTLINING, RESEARCHING, EDITING, COMPLETED, FAILED

**Request/Response Models**:
- `ResearchRequest` - Input cho research
- `EditRequest` - Input cho editing
- `ResearchSection` - Một section trong outline
- `ResearchOutline` - Cấu trúc outline
- `ProgressInfo` - Thông tin tiến độ
- `ResearchResult` - Kết quả research
- `ResearchError` - Thông tin lỗi
- `ResearchCostInfo` - Thông tin chi phí
- `ResearchResponse` - Response tổng hợp

#### Cost Models (`app/models/cost.py`)
- Models cho tracking chi phí API

### 5. Core Utilities (`app/core/`)

#### Service Factory (`app/core/factory.py`)
**ServiceFactory Class**:
- Singleton pattern để quản lý services
- Phương thức chính:
  - `get_llm_service()` - Lấy LLM service theo provider
  - `get_search_service()` - Lấy search service
  - `get_storage_service()` - Lấy storage service
  - `get_cost_monitoring_service()` - Lấy cost monitoring service
  - `create_llm_service_for_phase()` - Tạo LLM service cho phase cụ thể
  - `create_search_service()` - Tạo search service
  - `create_storage_service()` - Tạo storage service

#### Configuration (`app/core/config.py`)
- Application settings và configuration

#### Logging (`app/core/logging.py`)
- Logging setup và utilities

#### Exceptions (`app/core/exceptions.py`)
- Custom exception classes

## Research Workflow

### Complete Flow:
1. **API Request** → `POST /api/v1/research/complete`
2. **Background Task** → `process_complete_research()`
3. **Phase 1: Prepare** → `PrepareService.execute()`
   - Analyze query
   - Create outline
4. **Phase 2: Research** → `ResearchService.execute()`
   - Research each section
   - Collect information
5. **Phase 3: Edit** → `EditService.execute()`
   - Edit and synthesize content
   - Create title
   - Finalize document
6. **Phase 4: Storage** → Store results
   - Save to file system
   - Optionally push to GitHub

## Key Features

### 1. Modular Service Architecture
- Dependency injection through ServiceFactory
- Pluggable LLM providers (OpenAI, Claude)
- Pluggable search services (Perplexity, Google)
- Flexible storage backends

### 2. Cost Monitoring
- Track LLM API usage and costs
- Track search API usage and costs
- Real-time cost calculation
- Budget management support

### 3. Progress Tracking
- Real-time progress updates
- Status tracking through all phases
- Error handling and reporting

### 4. Asynchronous Processing
- Background task execution
- Non-blocking API responses
- Status polling support

## Configuration Files

### Environment Variables (`.env`)
```
# LLM Services
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx

# Search Services
PERPLEXITY_API_KEY=xxx
GOOGLE_API_KEY=xxx
GOOGLE_CSE_ID=xxx

# Storage (optional)
GITHUB_TOKEN=xxx
GITHUB_USERNAME=xxx
GITHUB_REPO=xxx
```

### Settings (`app/config/settings.py`)
- Application-wide settings
- Default configurations

## Test Structure
- Unit tests in `tests/` directory
- Test files: `test_research.py`, `test_research_complete.py`, etc.

## Data Storage
- `data/` - Research data storage
- `logs/` - Application logs
- `test_data/` - Test fixtures
- `test_outputs/` - Test results
