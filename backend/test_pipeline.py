import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.config import settings
from app.models.schemas import (
    ResearchJobCreate, 
    ResearchJobResponse, 
    SourceResponse, 
    ClaimResponse, 
    ReportResponse
)
from app.services.llm_service import get_model_name
from app.services.search_service import execute_search
from app.services.embedding_service import get_embeddings
from app.db.database import engine, AsyncSessionLocal, Base
from app.db.models import ResearchJob, Source, Claim, Evidence, Report
from app.api.routes import router
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

async def test_schemas():
    print("Testing Pydantic Schemas...")
    req = ResearchJobCreate(user_question="What is the future of quantum computing?", research_depth="deep")
    assert req.user_question == "What is the future of quantum computing?"
    assert req.research_depth == "deep"
    print("[OK] Schemas valid!")

def test_config_and_model():
    print("Testing Config and Model resolution...")
    model_name = get_model_name()
    assert model_name == "llama-3.3-70b-versatile" or model_name != "llama3-70b-8192"
    assert "llama3-70b-8192" not in model_name
    assert "gpt-oss-120b" not in model_name
    print(f"[OK] Config model is '{model_name}' (Decommissioned models removed)")

def test_search_service_resilience():
    print("Testing Search Service error handling and URL parsing...")
    # Without valid Tavily API key, execute_search should return [] gracefully without throwing unhandled exceptions
    results = execute_search("test query", max_results=2)
    assert isinstance(results, list)
    print("[OK] Search service safely handled missing/unauthorized Tavily key!")

def test_embeddings():
    print("Testing Embedding Service with FastEmbed...")
    texts = ["Quantum computing uses qubits", "Superposition enables parallel state evaluation"]
    embeddings = get_embeddings(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    print(f"[OK] Embeddings generated successfully: shape ({len(embeddings)}, {len(embeddings[0])})")

async def test_api_routes():
    print("Testing API Route Endpoints with in-memory SQLite / mock DB session...")
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.db.database import get_db

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app = FastAPI()
    app.include_router(router, prefix="/api/research")

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Test empty query rejection (400 Bad Request)
        res_empty = await ac.post("/api/research", json={"user_question": "   "})
        assert res_empty.status_code == 400
        print("[OK] Empty research query rejected with 400 Bad Request")

        # 2. Test valid job creation (200 OK)
        res_create = await ac.post("/api/research", json={"user_question": "Analyze quantum error correction", "research_depth": "deep"})
        assert res_create.status_code == 200
        job_data = res_create.json()
        assert job_data["status"] == "pending"
        assert job_data["user_question"] == "Analyze quantum error correction"
        assert job_data["research_depth"] == "deep"
        job_id = job_data["id"]
        print(f"[OK] Research job created successfully with ID: {job_id}")

        # 3. Test get job by ID (200 OK)
        res_get = await ac.get(f"/api/research/{job_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == job_id
        print("[OK] Retrieved research job successfully by ID")

        # 4. Test get sources for existing job (returns empty list if none yet)
        res_sources = await ac.get(f"/api/research/{job_id}/sources")
        assert res_sources.status_code == 200
        assert isinstance(res_sources.json(), list)
        print("[OK] Retrieved sources endpoint (Status 200, returned list)")

        # 5. Test get claims for existing job (returns empty list if none yet)
        res_claims = await ac.get(f"/api/research/{job_id}/claims")
        assert res_claims.status_code == 200
        assert isinstance(res_claims.json(), list)
        print("[OK] Retrieved claims endpoint (Status 200, returned list)")

        # 6. Test 404 for non-existent job
        res_not_found = await ac.get("/api/research/non-existent-id")
        assert res_not_found.status_code == 404
        print("[OK] Non-existent research job correctly returns 404")

        # 7. Test 404 for non-existent sources
        res_sources_404 = await ac.get("/api/research/non-existent-id/sources")
        assert res_sources_404.status_code == 404
        print("[OK] Non-existent sources correctly returns 404 (No longer 501!)")

        # 8. Test 404 for non-existent claims
        res_claims_404 = await ac.get("/api/research/non-existent-id/claims")
        assert res_claims_404.status_code == 404
        print("[OK] Non-existent claims correctly returns 404 (No longer 501!)")


    await test_engine.dispose()

async def main():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE BACKEND VALIDATION TESTS")
    print("=" * 60)
    await test_schemas()
    test_config_and_model()
    test_search_service_resilience()
    test_embeddings()
    await test_api_routes()
    print("=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
