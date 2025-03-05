from fastapi import APIRouter, HTTPException
from uuid import uuid4

from app.models.research import ResearchRequest, ResearchResponse, ResearchStatus

router = APIRouter()

@router.post("/research", response_model=ResearchResponse)
async def create_research(request: ResearchRequest) -> ResearchResponse:
    """
    Create a new research task.
    This is a placeholder implementation that just returns a response with PENDING status.
    """
    return ResearchResponse(
        id=str(uuid4()),
        status=ResearchStatus.PENDING
    )

@router.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(research_id: str) -> ResearchResponse:
    """
    Get status of a research task.
    This is a placeholder implementation that just returns a response with PENDING status.
    """
    return ResearchResponse(
        id=research_id,
        status=ResearchStatus.PENDING
    ) 