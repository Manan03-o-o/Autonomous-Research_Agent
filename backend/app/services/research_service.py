import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import ResearchJob, Source, ExtractedContent, Claim, Evidence, Report
from app.agents.planner import create_research_plan
from app.agents.searcher import generate_search_queries, search_and_deduplicate
from app.agents.extractor import fetch_page_content, chunk_text, get_embeddings
from app.agents.evidence import extract_claims_from_text
from app.agents.critic import evaluate_research
from app.agents.reporter import generate_research_report
from app.agents.verifier import verify_citations

logger = logging.getLogger(__name__)

async def update_job_status(db: AsyncSession, job_id: str, status: str, error_message: Optional[str] = None):
    """
    Safely update the status and optional error message of a ResearchJob.
    """
    try:
        result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if status in ["completed", "failed", "research_completed", "research_failed"]:
                job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(job)
    except Exception as e:
        logger.error(f"Failed to update job status for {job_id} to {status}: {e}")
        await db.rollback()

async def run_research_pipeline(job_id: str, user_question: str, research_depth: str = "standard"):
    """
    Main orchestration function for the autonomous research agent.
    Manages its own async database session lifecycle.
    """
    logger.info(f"Starting research pipeline for job_id={job_id} depth={research_depth}")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. PLANNER
            await update_job_status(db, job_id, "planning")
            plan = await create_research_plan(user_question)
            
            # Determine iterations and results per depth
            if research_depth == "quick":
                max_iterations = 1
                max_results_per_query = 2
            elif research_depth == "deep":
                max_iterations = 3
                max_results_per_query = 5
            else: # standard
                max_iterations = 2
                max_results_per_query = 3
            
            iteration = 0
            is_sufficient = False
            all_queries = plan.sub_questions.copy() if plan.sub_questions else [user_question]
            
            while iteration < max_iterations and not is_sufficient:
                iteration += 1
                logger.info(f"Job {job_id}: Iteration {iteration}/{max_iterations}")
                
                # 2. SEARCH
                await update_job_status(db, job_id, "searching")
                queries = await generate_search_queries(all_queries, plan.research_dimensions)
                if not queries:
                    queries = all_queries
                
                sources_data = await search_and_deduplicate(queries, max_results_per_query=max_results_per_query)
                
                # Save Sources
                db_sources = []
                for i, sd in enumerate(sources_data):
                    src_id = f"{job_id}_iter{iteration}_source_{i}"
                    src = Source(
                        id=src_id,
                        research_job_id=job_id,
                        title=sd.get("title", "Untitled Source"),
                        url=sd.get("url", ""),
                        publisher=sd.get("publisher", ""),
                        published_at=sd.get("published_at", ""),
                        relevance_score=1.0
                    )
                    db.add(src)
                    db_sources.append(src)
                await db.commit()
                
                # 3. EXTRACTION
                await update_job_status(db, job_id, "extracting")
                
                for src in db_sources:
                    if not src.url:
                        continue
                    content = await fetch_page_content(src.url)
                    if not content:
                        # Fallback snippet if page scrape fails
                        continue
                        
                    chunks = chunk_text(content)
                    if chunks:
                        embeddings = await get_embeddings(chunks)
                        for idx, chunk in enumerate(chunks):
                            if idx < len(embeddings):
                                ex_content = ExtractedContent(
                                    id=f"{src.id}_chunk_{idx}",
                                    source_id=src.id,
                                    content=chunk,
                                    embedding=embeddings[idx]
                                )
                                db.add(ex_content)
                    
                    # Extract claims
                    claims = await extract_claims_from_text(content[:4000], user_question)
                    for c_idx, claim_data in enumerate(claims):
                        c_id = f"{src.id}_claim_{c_idx}"
                        claim_text = claim_data.get("claim", "")
                        if not claim_text:
                            continue
                        db_claim = Claim(
                            id=c_id,
                            research_job_id=job_id,
                            claim=claim_text,
                            confidence=float(claim_data.get("confidence", 0.8))
                        )
                        db.add(db_claim)
                        
                        db_ev = Evidence(
                            id=f"{c_id}_ev",
                            claim_id=c_id,
                            source_id=src.id,
                            text=content[:500] if len(content) >= 500 else content
                        )
                        db.add(db_ev)
                
                await db.commit()
                
                # Fetch current claims and evidence
                claims_result = await db.execute(
                    select(Claim, Evidence, Source)
                    .join(Evidence, Claim.id == Evidence.claim_id)
                    .join(Source, Evidence.source_id == Source.id)
                    .where(Claim.research_job_id == job_id)
                )
                
                evidence_list = []
                for claim_row, ev_row, src_row in claims_result:
                    evidence_list.append({
                        "claim": claim_row.claim,
                        "confidence": claim_row.confidence,
                        "source_url": src_row.url,
                        "evidence_text": ev_row.text
                    })
                
                # 4. CRITIC (only if we have evidence and not last iteration)
                if evidence_list and iteration < max_iterations:
                    await update_job_status(db, job_id, "critiquing")
                    evaluation = await evaluate_research(user_question, plan.model_dump(), evidence_list)
                    is_sufficient = evaluation.is_sufficient
                    if not is_sufficient and evaluation.additional_queries:
                        all_queries = evaluation.additional_queries
                else:
                    is_sufficient = True
            
            # Fetch final claims for report
            claims_result = await db.execute(
                select(Claim, Evidence, Source)
                .join(Evidence, Claim.id == Evidence.claim_id)
                .join(Source, Evidence.source_id == Source.id)
                .where(Claim.research_job_id == job_id)
            )
            
            evidence_list = []
            for claim_row, ev_row, src_row in claims_result:
                evidence_list.append({
                    "claim": claim_row.claim,
                    "confidence": claim_row.confidence,
                    "source_url": src_row.url,
                    "evidence_text": ev_row.text
                })
            
            # 5. REPORT GENERATION
            await update_job_status(db, job_id, "generating")
            draft_report = await generate_research_report(user_question, plan.model_dump(), evidence_list)
            
            # 6. CITATION VERIFICATION
            await update_job_status(db, job_id, "verifying")
            final_report = await verify_citations(draft_report, evidence_list)
            
            # Save Report
            report = Report(
                id=f"{job_id}_report",
                research_job_id=job_id,
                content=final_report
            )
            db.add(report)
            await db.commit()
            
            # 7. COMPLETE
            await update_job_status(db, job_id, "completed")
            logger.info(f"Research pipeline completed successfully for job_id={job_id}")

        except Exception as e:
            logger.exception(f"Error in research pipeline for job_id={job_id}: {e}")
            await db.rollback()
            await update_job_status(db, job_id, "failed", error_message=str(e))

