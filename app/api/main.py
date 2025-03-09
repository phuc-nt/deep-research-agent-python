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
    description="API for automated research using AI",
    version="1.0.0"
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