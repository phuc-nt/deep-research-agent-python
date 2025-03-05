from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ResearchStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    EDITING = "editing"
    COMPLETED = "completed"
    FAILED = "failed"

class ResearchRequest(BaseModel):
    topic: str = Field(..., description="Chủ đề nghiên cứu")
    scope: str = Field(..., description="Phạm vi nghiên cứu")
    target_audience: str = Field(..., description="Đối tượng độc giả")

class QueryAnalysis(BaseModel):
    topic: str
    scope: str
    target_audience: str
    depth: str
    key_points: List[str]

class Section(BaseModel):
    title: str
    description: str
    key_points: List[str]

class Outline(BaseModel):
    sections: List[Section]
    estimated_word_count: int

class ResearchResponse(BaseModel):
    id: str = Field(..., description="ID của research task")
    status: ResearchStatus
    github_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 