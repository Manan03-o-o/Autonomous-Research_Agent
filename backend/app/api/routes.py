import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse
from typing import List
import asyncio

from app.db.database import get_db
from app.db.models import ResearchJob
from app.models.schemas import ResearchJobCreate, ResearchJobResponse, SourceResponse, ClaimResponse, ReportResponse
from app.services.research_service import run_research_pipeline

router = APIRouter()

@router.post("", response_model=ResearchJobResponse)
async def create_research_job(job: ResearchJobCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    job_id = str(uuid.uuid4())
    db_job = ResearchJob(
        id=job_id,
        user_question=job.user_question,
        research_depth=job.research_depth
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    background_tasks.add_task(run_research_pipeline, job_id, job.user_question, db)
    
    return db_job

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
    async def event_generator():
        # Simple polling for MVP
        last_status = None
        while True:
            result = await db.execute(select(ResearchJob).where(ResearchJob.id == research_id))
            job = result.scalar_one_or_none()
            if not job:
                yield {"event": "error", "data": "Job not found"}
                break
                
            if job.status != last_status:
                last_status = job.status
                yield {"event": "status", "data": job.status}
                
            if job.status in ["completed", "failed"]:
                break
                
            await asyncio.sleep(2)
            
    return EventSourceResponse(event_generator())
