from typing import Type, Optional, Dict, Any
import importlib
from app.core.config import Settings
from app.core.logging import get_logger

from app.services.core.llm.base import BaseLLMService
from app.services.core.search.base import BaseSearchService
from app.services.core.storage.base import BaseStorageService

# These will be implemented later
from app.services.core.llm.openai import OpenAIService
from app.services.core.llm.claude import ClaudeService
from app.services.core.search.perplexity import PerplexityService
from app.services.core.search.google import GoogleService
from app.services.core.storage.github import GitHubService
from app.services.core.storage.file import FileStorageService

from .config import get_settings
from .exceptions import ConfigError

logger = get_logger(__name__)

class ServiceFactory:
    """Factory for creating service instances"""
    
    def __init__(self, config: Settings):
        self.config = config
        self.services = {}
    
    def get_llm_service(self, provider: Optional[str] = None) -> Any:
        """Get LLM service instance by provider name"""
        provider = provider or self.config.DEFAULT_LLM_PROVIDER
        service_key = f"llm_{provider}"
        
        if service_key in self.services:
            return self.services[service_key]
        
        try:
            module_name = f"app.services.core.llm.{provider.lower()}"
            module = importlib.import_module(module_name)
            
            # Xử lý các trường hợp đặc biệt
            if provider.lower() == "openai":
                service_class_name = "OpenAIService"
            elif provider.lower() == "claude":
                service_class_name = "ClaudeService"
            else:
                service_class_name = f"{provider.capitalize()}Service"
            
            service_class = getattr(module, service_class_name)
            
            service = service_class(self.config.dict())
            self.services[service_key] = service
            
            return service
        except Exception as e:
            logger.error(f"Error creating LLM service for provider {provider}: {str(e)}")
            # Fallback to default provider if different
            if provider != self.config.DEFAULT_LLM_PROVIDER:
                logger.info(f"Falling back to default provider {self.config.DEFAULT_LLM_PROVIDER}")
                return self.get_llm_service(self.config.DEFAULT_LLM_PROVIDER)
            raise e
    
    async def get_search_service(self, provider: Optional[str] = None) -> Any:
        """Get search service instance by provider name"""
        provider = provider or self.config.DEFAULT_SEARCH_PROVIDER
        service_key = f"search_{provider}"
        
        if service_key in self.services:
            return self.services[service_key]
        
        try:
            if provider == "perplexity":
                # Kiểm tra API key trước khi khởi tạo service
                if not self.config.PERPLEXITY_API_KEY or self.config.PERPLEXITY_API_KEY == "your_perplexity_api_key":
                    logger.error("PERPLEXITY_API_KEY không hợp lệ hoặc chưa được cấu hình")
                    raise ValueError("PERPLEXITY_API_KEY không hợp lệ hoặc chưa được cấu hình")
                service = PerplexityService()
                # Thử gọi một phương thức đơn giản để kiểm tra kết nối
                logger.info(f"Đã khởi tạo Perplexity service với API key: {self.config.PERPLEXITY_API_KEY[:5]}...")
            elif provider == "google":
                # Kiểm tra API key trước khi khởi tạo service
                if not self.config.GOOGLE_API_KEY or self.config.GOOGLE_API_KEY == "your_google_api_key" or not self.config.GOOGLE_CSE_ID or self.config.GOOGLE_CSE_ID == "your_google_cse_id":
                    logger.error("GOOGLE_API_KEY hoặc GOOGLE_CSE_ID không hợp lệ hoặc chưa được cấu hình")
                    raise ValueError("GOOGLE_API_KEY hoặc GOOGLE_CSE_ID không hợp lệ hoặc chưa được cấu hình")
                service = GoogleService()
                logger.info(f"Đã khởi tạo Google service với API key: {self.config.GOOGLE_API_KEY[:5]}...")
            else:
                logger.error(f"Không hỗ trợ search provider: {provider}")
                # Fallback to default provider
                if provider != self.config.DEFAULT_SEARCH_PROVIDER:
                    logger.info(f"Thử sử dụng provider mặc định: {self.config.DEFAULT_SEARCH_PROVIDER}")
                    return await self.get_search_service(self.config.DEFAULT_SEARCH_PROVIDER)
                else:
                    raise ValueError(f"Không hỗ trợ search provider: {provider}")
            
            self.services[service_key] = service
            return service
        except Exception as e:
            logger.error(f"Lỗi khi tạo search service cho provider {provider}: {str(e)}")
            # Fallback to default provider if different
            if provider != self.config.DEFAULT_SEARCH_PROVIDER:
                logger.info(f"Thử sử dụng provider mặc định: {self.config.DEFAULT_SEARCH_PROVIDER}")
                return await self.get_search_service(self.config.DEFAULT_SEARCH_PROVIDER)
            # Nếu đã là provider mặc định mà vẫn lỗi, trả về None
            logger.error(f"Không thể tạo search service với provider mặc định: {str(e)}")
            return None
    
    def get_storage_service(self, provider: Optional[str] = None) -> Any:
        """Get storage service instance by provider name"""
        provider = provider or self.config.DEFAULT_STORAGE_PROVIDER
        service_key = f"storage_{provider}"
        
        if service_key in self.services:
            return self.services[service_key]
        
        try:
            if provider == "file":
                service = FileStorageService()
            elif provider == "github":
                service = GitHubService()
            else:
                logger.error(f"Không hỗ trợ storage provider: {provider}")
                # Fallback to default provider
                return self.get_storage_service(self.config.DEFAULT_STORAGE_PROVIDER)
            
            self.services[service_key] = service
            return service
        except Exception as e:
            logger.error(f"Error creating storage service for provider {provider}: {str(e)}")
            # Fallback to file if different
            if provider != self.config.DEFAULT_STORAGE_PROVIDER:
                return self.get_storage_service(self.config.DEFAULT_STORAGE_PROVIDER)
            raise e
    
    def create_storage_service(self, provider: Optional[str] = None) -> Any:
        """
        Create storage service instance by provider name.
        This is an alias for get_storage_service for backward compatibility.
        """
        return self.get_storage_service(provider)
    
    def get_cost_monitoring_service(self) -> Any:
        """Get cost monitoring service instance"""
        service_key = "cost_monitoring"
        
        if service_key in self.services:
            return self.services[service_key]
        
        try:
            # Lấy storage service
            storage_service = self.get_storage_service()
            
            # Import function để lấy cost service
            from app.services.core.monitoring.cost import get_cost_service
            
            # Tạo cost service
            service = get_cost_service(storage_service)
            
            self.services[service_key] = service
            logger.info(f"Đã tạo cost monitoring service")
            
            return service
        except Exception as e:
            logger.error(f"Error creating cost monitoring service: {str(e)}")
            raise e
            
    def create_llm_service_for_phase(self, phase: str) -> Any:
        """
        Create LLM service for a specific research phase
        
        Args:
            phase: Research phase (prepare, research, edit)
            
        Returns:
            LLM service instance
        """
        # Lấy provider từ config dựa trên phase
        provider_key = f"{phase.upper()}_LLM_PROVIDER"
        provider = getattr(self.config, provider_key, self.config.DEFAULT_LLM_PROVIDER)
        
        logger.info(f"Tạo LLM service cho phase {phase} với provider {provider}")
        return self.get_llm_service(provider)
        
    async def create_search_service(self, provider: Optional[str] = None) -> Any:
        """
        Create search service
        
        Args:
            provider: Search provider name
            
        Returns:
            Search service instance
        """
        provider = provider or self.config.DEFAULT_SEARCH_PROVIDER
        logger.info(f"Tạo search service với provider {provider}")
        return await self.get_search_service(provider)

# Singleton instance
service_factory = None

def init_service_factory(config: Settings) -> ServiceFactory:
    """Initialize the service factory"""
    global service_factory
    service_factory = ServiceFactory(config)
    return service_factory

def get_service_factory() -> ServiceFactory:
    """Get the service factory instance"""
    global service_factory
    if not service_factory:
        from app.core.config import get_settings
        service_factory = ServiceFactory(get_settings())
    return service_factory
