from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from typing import List

from app.db.database import get_db
from app.models.schemas import ResearchJobCreate, ResearchJobResponse, SourceResponse, ClaimResponse, ReportResponse

router = APIRouter()

@router.post("", response_model=ResearchJobResponse)
async def create_research_job(job: ResearchJobCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # TODO: Initialize job in db and start agent workflow in background
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{research_id}", response_model=ResearchJobResponse)
async def get_research_job(research_id: str, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{research_id}/sources", response_model=List[SourceResponse])
async def get_research_sources(research_id: str, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{research_id}/claims", response_model=List[ClaimResponse])
async def get_research_claims(research_id: str, db: AsyncSession = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{research_id}/stream")
async def stream_research_progress(research_id: str, db: AsyncSession = Depends(get_db)):
    # Server-Sent Events (SSE) endpoint to stream progress
    async def event_generator():
        # TODO: Yield events from a pub/sub or database status check
        yield {"event": "status", "data": "planning_started"}
        
    return EventSourceResponse(event_generator())
