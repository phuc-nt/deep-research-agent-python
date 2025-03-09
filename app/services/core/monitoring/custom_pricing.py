import os
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)

def get_custom_pricing():
    """Lấy bảng giá tùy chỉnh từ biến môi trường hoặc từ config"""
    settings = get_settings()
    
    # Bảng giá model - giá trên 1000 token
    model_pricing = {
        # OpenAI models - giá mặc định
        "gpt-4o": {"input": 0.003, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        
        # Anthropic models - giá mặc định
        "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-2": {"input": 0.008, "output": 0.024},
        "claude-instant": {"input": 0.0008, "output": 0.0024},
        
        # Perplexity models - giá mặc định
        "llama-3.1-sonar-small-128k-online": {"input": 0.0002, "output": 0.0002},
        "pplx-70b-online": {"input": 0.0002, "output": 0.0002},
    }
    
    # Cập nhật giá từ biến môi trường nếu có
    try:
        # OpenAI
        if hasattr(settings, 'OPENAI_COST_PROMPT_TOKEN') and hasattr(settings, 'OPENAI_COST_COMPLETION_TOKEN'):
            openai_prompt = float(settings.OPENAI_COST_PROMPT_TOKEN) * 1000  # Chuyển từ giá/token sang giá/1000 token
            openai_completion = float(settings.OPENAI_COST_COMPLETION_TOKEN) * 1000
            
            # Cập nhật tất cả model OpenAI
            for model in [m for m in model_pricing.keys() if m.startswith("gpt-")]:
                model_pricing[model]["input"] = openai_prompt
                model_pricing[model]["output"] = openai_completion
            
            logger.info(f"Đã cập nhật giá OpenAI từ biến môi trường: {openai_prompt}/1000 input tokens, {openai_completion}/1000 output tokens")
        
        # Claude
        if hasattr(settings, 'CLAUDE_COST_PROMPT_TOKEN') and hasattr(settings, 'CLAUDE_COST_COMPLETION_TOKEN'):
            claude_prompt = float(settings.CLAUDE_COST_PROMPT_TOKEN) * 1000
            claude_completion = float(settings.CLAUDE_COST_COMPLETION_TOKEN) * 1000
            
            # Cập nhật tất cả model Claude
            for model in [m for m in model_pricing.keys() if m.startswith("claude-")]:
                model_pricing[model]["input"] = claude_prompt
                model_pricing[model]["output"] = claude_completion
            
            logger.info(f"Đã cập nhật giá Claude từ biến môi trường: {claude_prompt}/1000 input tokens, {claude_completion}/1000 output tokens")
        
        # Perplexity
        if hasattr(settings, 'PERPLEXITY_COST_PROMPT_TOKEN') and hasattr(settings, 'PERPLEXITY_COST_COMPLETION_TOKEN'):
            perplexity_prompt = float(settings.PERPLEXITY_COST_PROMPT_TOKEN) * 1000
            perplexity_completion = float(settings.PERPLEXITY_COST_COMPLETION_TOKEN) * 1000
            
            # Cập nhật tất cả model Perplexity
            for model in [m for m in model_pricing.keys() if "pplx" in m or "llama" in m]:
                model_pricing[model]["input"] = perplexity_prompt
                model_pricing[model]["output"] = perplexity_completion
            
            logger.info(f"Đã cập nhật giá Perplexity từ biến môi trường: {perplexity_prompt}/1000 input tokens, {perplexity_completion}/1000 output tokens")
    
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật bảng giá từ biến môi trường: {str(e)}")
    
    # Giá cho search providers - giá trên mỗi request
    search_pricing = {
        "google": 0.01,  # 1 cent mỗi request
        "perplexity": 0.005,  # 0.5 cent mỗi request
        "custom": 0.0  # Không tính phí
    }
    
    return model_pricing, search_pricing 