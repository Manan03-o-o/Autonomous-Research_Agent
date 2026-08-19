import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import ResearchJob, Source, ExtractedContent, Claim, Evidence, Report
from app.agents.planner import create_research_plan
from app.agents.searcher import generate_search_queries, search_and_deduplicate
from app.agents.extractor import fetch_page_content, chunk_text, get_embeddings
from app.agents.evidence import extract_claims_from_text
from app.agents.reporter import generate_research_report

async def run_research_pipeline(job_id: str, user_question: str, db: AsyncSession):
    """
    Main orchestration function for the autonomous research agent.
    """
    try:
        # Get Job
        result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        # 1. PLANNER
        job.status = "planning"
        await db.commit()
        plan = await create_research_plan(user_question)
        
        # 2. SEARCH
        job.status = "searching"
        await db.commit()
        queries = await generate_search_queries(plan.sub_questions, plan.research_dimensions)
        sources_data = await search_and_deduplicate(queries, max_results_per_query=3)
        
        # Save Sources
        db_sources = []
        for i, sd in enumerate(sources_data):
            src = Source(
                id=f"{job_id}_source_{i}",
                research_job_id=job_id,
                title=sd.get("title", ""),
                url=sd.get("url", ""),
                relevance_score=1.0 # placeholder
            )
            db.add(src)
            db_sources.append(src)
        await db.commit()
        
        # 3. EXTRACTION
        job.status = "extracting"
        await db.commit()
        
        for src in db_sources:
            content = await fetch_page_content(src.url)
            if not content:
                continue
                
            chunks = chunk_text(content)
            # We can parallelize embedding and claim extraction
            # For simplicity in MVP, we do it sequentially or batch it
            
            # Extract claims directly for MVP
            claims = await extract_claims_from_text(content[:4000], user_question)
            
            for c_idx, claim_data in enumerate(claims):
                c_id = f"{src.id}_claim_{c_idx}"
                db_claim = Claim(
                    id=c_id,
                    research_job_id=job_id,
                    claim=claim_data.get("claim"),
                    confidence=claim_data.get("confidence")
                )
                db.add(db_claim)
                
                db_ev = Evidence(
                    id=f"{c_id}_ev",
                    claim_id=c_id,
                    source_id=src.id,
                    text=content[:500] # just a snippet for MVP
                )
                db.add(db_ev)
                
        await db.commit()
        
        # 4. REPORT GENERATION
        job.status = "generating"
        await db.commit()
        
        # Fetch all claims and evidence
        claims_result = await db.execute(select(Claim, Evidence, Source)
                                       .join(Evidence, Claim.id == Evidence.claim_id)
                                       .join(Source, Evidence.source_id == Source.id)
                                       .where(Claim.research_job_id == job_id))
        
        evidence_list = []
        for claim, ev, src in claims_result:
            evidence_list.append({
                "claim": claim.claim,
                "confidence": claim.confidence,
                "source_url": src.url,
                "evidence_text": ev.text
            })
            
        report_markdown = await generate_research_report(user_question, plan.model_dump(), evidence_list)
        
        report = Report(
            id=f"{job_id}_report",
            research_job_id=job_id,
            content=report_markdown
        )
        db.add(report)
        
        # Finish
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        await db.commit()

    except Exception as e:
        print(f"Error in pipeline: {e}")
        if job:
            job.status = "failed"
            await db.commit()
