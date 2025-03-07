from typing import Dict, Any
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
    
    # LLM settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    MODEL_NAME: str = "gpt-4"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@dataclass
class PreparePrompts:
    """Prompts for prepare phase"""
    ANALYZE_QUERY: str = """
    Analyze the following research query:
    {query}
    """

    CREATE_OUTLINE: str = """
    Create an outline for the following research query:
    {query}
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
    4. Thêm trích dẫn nguồn cho mỗi thông tin quan trọng
    5. Viết bằng tiếng Việt
    
    Format kết quả:
    - Nội dung được chia thành các đoạn rõ ràng
    - Mỗi đoạn tập trung vào một ý chính
    - Có trích dẫn nguồn dưới dạng link HTML
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
    1. Đảm bảo tính mạch lạc và liên kết giữa các phần
    2. Thêm phần giới thiệu tổng quan ở đầu bài
    3. Thêm phần kết luận tổng hợp ở cuối bài
    4. Chỉnh sửa các lỗi ngữ pháp, chính tả
    5. Đảm bảo văn phong nhất quán, phù hợp với đối tượng đọc
    6. Giữ nguyên các trích dẫn nguồn
    7. Viết bằng tiếng Việt
    
    Trả về nội dung đã chỉnh sửa hoàn chỉnh.
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
