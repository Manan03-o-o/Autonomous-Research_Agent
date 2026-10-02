import uuid
import json
import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.db.database import get_db, AsyncSessionLocal
from app.db.models import ResearchJob, Source, Claim, Evidence, Report
from app.models.schemas import (
    ResearchJobCreate,
    ResearchJobResponse,
    SourceResponse,
    ClaimResponse,
    ReportResponse,
)
from app.services.research_service import run_research_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=ResearchJobResponse)
async def create_research_job(
    job: ResearchJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not job.user_question or not job.user_question.strip():
        raise HTTPException(status_code=400, detail="user_question cannot be empty")

    job_id = str(uuid.uuid4())
    db_job = ResearchJob(
        id=job_id,
        user_question=job.user_question.strip(),
        research_depth=job.research_depth or "standard",
        status="pending",
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    # Pass only serializable primitives into background task.
    # The pipeline manages its own database session.
    background_tasks.add_task(
        run_research_pipeline,
        job_id,
        db_job.user_question,
        db_job.research_depth,
    )
    
    return db_job

@router.get("/{research_id}", response_model=ResearchJobResponse)
async def get_research_job(research_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchJob).where(ResearchJob.id == research_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")
    return job

@router.get("/{research_id}/sources", response_model=List[SourceResponse])
async def get_research_sources(research_id: str, db: AsyncSession = Depends(get_db)):
    # Verify job exists
    job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == research_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Research job not found")
        
    result = await db.execute(
        select(Source)
        .where(Source.research_job_id == research_id)
        .order_by(Source.relevance_score.desc())
    )
    sources = result.scalars().all()
    return sources

@router.get("/{research_id}/claims", response_model=List[ClaimResponse])
async def get_research_claims(research_id: str, db: AsyncSession = Depends(get_db)):
    # Verify job exists
    job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == research_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Research job not found")

    result = await db.execute(
        select(Claim)
        .options(
            selectinload(Claim.evidence).selectinload(Evidence.source)
        )
        .where(Claim.research_job_id == research_id)
        .order_by(Claim.confidence.desc())
    )
    claims = result.scalars().all()
    return claims

@router.get("/{research_id}/report", response_model=ReportResponse)
async def get_research_report(research_id: str, db: AsyncSession = Depends(get_db)):
    # Verify job exists
    job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == research_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")

    result = await db.execute(
        select(Report).where(Report.research_job_id == research_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        if job.status == "failed":
            raise HTTPException(status_code=400, detail=f"Research failed: {job.error_message or 'Unknown error'}")
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return report

@router.get("/{research_id}/stream")
async def stream_research_progress(research_id: str, request: Request):
    """
    SSE endpoint to stream real-time research progress.
    Uses short-lived sessions per poll to prevent holding or leaking connections.
    """
    async def event_generator():
        last_status = None
        
        while True:
            if await request.is_disconnected():
                logger.info(f"Client disconnected from SSE stream for job {research_id}")
                break

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ResearchJob).where(ResearchJob.id == research_id)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Job not found", "status": "failed"})
                    }
                    break

                current_status = job.status
                if current_status != last_status:
                    last_status = current_status
                    payload = {
                        "status": current_status,
                        "error_message": job.error_message,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None
                    }
                    # Send both standard event data and named events for compatibility
                    yield {
                        "event": "status",
                        "data": current_status
                    }
                    yield {
                        "event": "progress",
                        "data": json.dumps(payload)
                    }

                if current_status in ["completed", "failed", "research_completed", "research_failed"]:
                    yield {
                        "event": "done",
                        "data": json.dumps({
                            "status": current_status,
                            "error": job.error_message
                        })
                    }
                    break

            await asyncio.sleep(1.0)
            
    return EventSourceResponse(event_generator())

