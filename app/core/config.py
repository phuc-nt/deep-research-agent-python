from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dataclasses import dataclass


class Settings(BaseSettings):
    """Application settings"""
    
    # API version
    API_VERSION: str = "v1"
    
    # Environment
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    
    # API Keys
    OPENAI_API_KEY: str = "your_openai_api_key"
    ANTHROPIC_API_KEY: str = "your_anthropic_api_key"
    PERPLEXITY_API_KEY: str = "your_perplexity_api_key"
    GOOGLE_API_KEY: str = "your_google_api_key"
    GOOGLE_CSE_ID: str = "your_google_cse_id"
    GITHUB_ACCESS_TOKEN: str = "your_github_token"
    GITHUB_USERNAME: str = "your_github_username"
    GITHUB_REPO: str = "your_github_repo"
    
    # Provider settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_SEARCH_PROVIDER: str = "perplexity"
    DEFAULT_STORAGE_PROVIDER: str = "file"
    
    # LLM settings
    MODEL_NAME: str = "gpt-4"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    # Phase-specific LLM settings
    PREPARE_LLM_PROVIDER: str = "openai"
    PREPARE_MODEL_NAME: str = "gpt-4"
    PREPARE_MAX_TOKENS: int = 4000
    PREPARE_TEMPERATURE: float = 0.7
    
    RESEARCH_LLM_PROVIDER: str = "openai"
    RESEARCH_MODEL_NAME: str = "gpt-4"
    RESEARCH_MAX_TOKENS: int = 4000
    RESEARCH_TEMPERATURE: float = 0.7
    
    EDIT_LLM_PROVIDER: str = "openai"
    EDIT_MODEL_NAME: str = "gpt-4o"
    EDIT_MAX_TOKENS: int = 4000
    EDIT_TEMPERATURE: float = 0.7
    
    # Cost monitoring settings
    ENABLE_COST_MONITORING: bool = True
    COST_STORAGE_PROVIDER: str = "file"
    
    # Cost Tracking
    ENABLE_COST_TRACKING: bool = True
    OPENAI_COST_PROMPT_TOKEN: float = 0.00000025
    OPENAI_COST_COMPLETION_TOKEN: float = 0.00000075
    CLAUDE_COST_PROMPT_TOKEN: float = 0.000008
    CLAUDE_COST_COMPLETION_TOKEN: float = 0.000024
    PERPLEXITY_COST_PROMPT_TOKEN: float = 0.000002
    PERPLEXITY_COST_COMPLETION_TOKEN: float = 0.000002
    
    # Storage settings
    storage_provider: Optional[str] = None
    data_dir: Optional[str] = None
    logs_dir: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow",  # Allow extra fields
        protected_namespaces=()  # Disable protected namespaces check
    )


@dataclass
class PreparePrompts:
    """Prompts for prepare phase"""
    ANALYZE_QUERY: str = """
    Phân tích yêu cầu nghiên cứu sau đây:
    {query}
    
    Hãy phân tích yêu cầu trên và xác định các thông tin sau:
    1. Chủ đề (Topic): Chủ đề chính của nghiên cứu
    2. Phạm vi (Scope): Phạm vi và giới hạn của nghiên cứu
    3. Đối tượng độc giả (Target Audience): Nhóm đối tượng mục tiêu của nghiên cứu
    
    ĐỊNH DẠNG PHẢN HỒI:
    1. Phản hồi của bạn PHẢI là một đối tượng JSON hợp lệ, không có bất kỳ văn bản nào khác.
    2. KHÔNG bao gồm markdown, giải thích, hoặc bất kỳ nội dung nào khác ngoài JSON.
    3. KHÔNG sử dụng dấu backtick (```) hoặc định dạng markdown cho JSON.
    4. JSON phải có cấu trúc chính xác như mẫu dưới đây.
    
    Trả về kết quả dưới dạng JSON có cấu trúc như sau:
    {{
        "topic": "Chủ đề của nghiên cứu",
        "scope": "Phạm vi của nghiên cứu",
        "target_audience": "Đối tượng độc giả"
    }}
    """

    CREATE_OUTLINE: str = """
    Tạo dàn ý cho yêu cầu nghiên cứu sau đây:
    
    Chủ đề: {topic}
    Phạm vi: {scope}
    Đối tượng độc giả: {target_audience}
    
    Dưới đây là một số kết quả tìm kiếm liên quan đến chủ đề:
    {search_results}
    
    Hãy tạo một dàn ý nghiên cứu chi tiết bao gồm các phần logic và có cấu trúc rõ ràng.
    
    LƯU Ý QUAN TRỌNG: 
    1. Dàn ý PHẢI tập trung vào chủ đề cụ thể được yêu cầu, KHÔNG tạo dàn ý chung chung về quy trình nghiên cứu.
    2. Mỗi phần trong dàn ý phải liên quan trực tiếp đến chủ đề, với tiêu đề cụ thể phản ánh nội dung của phần đó.
    3. KHÔNG sử dụng các tiêu đề chung chung như "Giới thiệu", "Phương pháp nghiên cứu", "Kết luận" mà không có thông tin cụ thể về chủ đề.
    4. Mỗi tiêu đề phần phải chứa các từ khóa liên quan trực tiếp đến chủ đề nghiên cứu.
    
    ĐỊNH DẠNG PHẢN HỒI:
    1. Phản hồi của bạn PHẢI là một đối tượng JSON hợp lệ, không có bất kỳ văn bản nào khác.
    2. KHÔNG bao gồm markdown, giải thích, hoặc bất kỳ nội dung nào khác ngoài JSON.
    3. KHÔNG sử dụng dấu backtick (```) hoặc định dạng markdown cho JSON.
    4. JSON phải có cấu trúc chính xác như mẫu dưới đây.
    
    Trả về kết quả dưới dạng JSON có cấu trúc như sau:
    {{
        "sections": [
            {{
                "title": "Tiêu đề phần 1 (phải liên quan trực tiếp đến chủ đề)",
                "description": "Mô tả ngắn gọn về nội dung phần 1, nêu rõ các điểm chính sẽ được đề cập"
            }},
            {{
                "title": "Tiêu đề phần 2 (phải liên quan trực tiếp đến chủ đề)",
                "description": "Mô tả ngắn gọn về nội dung phần 2, nêu rõ các điểm chính sẽ được đề cập"
            }}
        ]
    }}
    """

    CREATE_OUTLINE_WITHOUT_SEARCH: str = """
    Tạo dàn ý cho yêu cầu nghiên cứu sau đây:
    
    Chủ đề: {topic}
    Phạm vi: {scope}
    Đối tượng độc giả: {target_audience}
    
    Hãy tạo một dàn ý nghiên cứu chi tiết bao gồm các phần logic và có cấu trúc rõ ràng. Vì không có kết quả tìm kiếm từ internet, hãy sử dụng kiến thức sẵn có của bạn để tạo dàn ý chất lượng cao nhất có thể.
    
    LƯU Ý QUAN TRỌNG: 
    1. Dàn ý PHẢI tập trung vào chủ đề cụ thể được yêu cầu, KHÔNG tạo dàn ý chung chung về quy trình nghiên cứu.
    2. Mỗi phần trong dàn ý phải liên quan trực tiếp đến chủ đề, với tiêu đề cụ thể phản ánh nội dung của phần đó.
    3. KHÔNG sử dụng các tiêu đề chung chung như "Giới thiệu", "Phương pháp nghiên cứu", "Kết luận" mà không có thông tin cụ thể về chủ đề.
    4. Mỗi tiêu đề phần phải chứa các từ khóa liên quan trực tiếp đến chủ đề nghiên cứu.
    5. Tạo ít nhất 5 phần để đảm bảo nghiên cứu đủ chi tiết và toàn diện.
    6. Đảm bảo các phần có tính liên kết và logic, tạo thành một bài nghiên cứu hoàn chỉnh.
    
    ĐỊNH DẠNG PHẢN HỒI:
    1. Phản hồi của bạn PHẢI là một đối tượng JSON hợp lệ, không có bất kỳ văn bản nào khác.
    2. KHÔNG bao gồm markdown, giải thích, hoặc bất kỳ nội dung nào khác ngoài JSON.
    3. KHÔNG sử dụng dấu backtick (```) hoặc định dạng markdown cho JSON.
    4. JSON phải có cấu trúc chính xác như mẫu dưới đây.
    
    Trả về kết quả dưới dạng JSON có cấu trúc như sau:
    {{
        "sections": [
            {{
                "title": "Tiêu đề phần 1 (phải liên quan trực tiếp đến chủ đề)",
                "description": "Mô tả ngắn gọn về nội dung phần 1, nêu rõ các điểm chính sẽ được đề cập"
            }},
            {{
                "title": "Tiêu đề phần 2 (phải liên quan trực tiếp đến chủ đề)",
                "description": "Mô tả ngắn gọn về nội dung phần 2, nêu rõ các điểm chính sẽ được đề cập"
            }}
        ]
    }}
    """


@dataclass
class ResearchPrompts:
    """Prompts for research phase"""
    
    SEARCH_QUERY: str = """
    Tìm kiếm thông tin chi tiết cho phần sau trong bài nghiên cứu:
    
    Chủ đề: {topic}
    Phạm vi: {scope}
    Tiêu đề phần: {section_title}
    Mô tả phần: {section_description}
    
    Hãy tìm các nguồn đáng tin cậy, ưu tiên:
    - Bài báo khoa học
    - Báo cáo nghiên cứu
    - Tài liệu chuyên ngành
    - Bài viết từ các chuyên gia
    
    Trả về 3-5 từ khóa tìm kiếm cụ thể để tìm thông tin cho phần này.
    """

    ANALYZE_AND_SYNTHESIZE: str = """
    Phân tích và tổng hợp thông tin cho phần sau trong bài nghiên cứu:
    
    Chủ đề: {topic}
    Phạm vi: {scope}
    Đối tượng đọc: {target_audience}
    
    Tiêu đề phần: {section_title}
    Mô tả phần: {section_description}
    
    Kết quả tìm kiếm:
    {search_results}
    
    Yêu cầu:
    1. Phân tích thông tin từ các nguồn một cách khách quan
    2. Tổng hợp thành nội dung mạch lạc, dễ hiểu
    3. Đảm bảo phù hợp với đối tượng đọc
    4. Thêm trích dẫn nguồn cho mỗi thông tin quan trọng (dạng link HTML)
    5. Viết bằng tiếng Việt
    6. Độ dài chính xác từ 350 đến 400 từ
    
    Format kết quả:
    - Nội dung được chia thành các đoạn rõ ràng
    - Mỗi đoạn tập trung vào một ý chính
    - Có trích dẫn nguồn dưới dạng link HTML
    
    Không thêm tiêu đề phần hoặc tiêu đề phụ, chỉ trả về nội dung.
    """


@dataclass
class EditPrompts:
    """Prompts for edit phase"""
    EDIT_CONTENT: str = """
    Chỉnh sửa và hoàn thiện bài nghiên cứu sau:
    
    Chủ đề: {topic}
    Phạm vi: {scope}
    Đối tượng đọc: {target_audience}
    
    Nội dung bài nghiên cứu:
    {content}
    
    Yêu cầu:
    1. KHÔNG tóm tắt hay rút gọn nội dung của các phần, giữ nguyên độ dài và chi tiết của mỗi phần
    2. Chỉ kết nối các phần lại với nhau thành một bài viết mạch lạc, thêm các câu chuyển tiếp giữa các phần
    3. Thêm phần giới thiệu tổng quan ở đầu bài
    4. Thêm phần kết luận tổng hợp ở cuối bài
    5. Chỉnh sửa các lỗi ngữ pháp, chính tả
    6. Đảm bảo văn phong nhất quán, phù hợp với đối tượng đọc
    7. Giữ nguyên các trích dẫn nguồn
    8. Viết bằng tiếng Việt
    
    Trả về nội dung đã chỉnh sửa hoàn chỉnh.
    """
    
    CREATE_TITLE: str = """
    Tạo tiêu đề cho bài nghiên cứu sau:
    
    Chủ đề: {topic}
    Phạm vi: {scope}
    Đối tượng đọc: {target_audience}
    
    Nội dung bài nghiên cứu (phần đầu):
    {content}
    
    Yêu cầu:
    1. Tiêu đề ngắn gọn, súc tích (dưới 15 từ)
    2. Phản ánh chính xác nội dung bài nghiên cứu
    3. Thu hút sự chú ý của đối tượng đọc
    4. Viết bằng tiếng Việt
    
    QUAN TRỌNG: Chỉ trả về tiêu đề dạng text thuần túy, KHÔNG trả về JSON, KHÔNG thêm giải thích hay định dạng khác.
    """


# Global instances
_settings = Settings()
_prepare_prompts = PreparePrompts()
_research_prompts = ResearchPrompts()
_edit_prompts = EditPrompts()


def get_settings() -> Settings:
    """Get application settings"""
    return _settings


def get_prepare_prompts() -> PreparePrompts:
    """Get prepare phase prompts"""
    return _prepare_prompts


def get_research_prompts() -> ResearchPrompts:
    """Get research phase prompts"""
    return _research_prompts


def get_edit_prompts() -> EditPrompts:
    """Get edit phase prompts"""
    return _edit_prompts
