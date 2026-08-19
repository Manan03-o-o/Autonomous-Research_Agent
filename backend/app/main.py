from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.db.database import engine, Base
from app.db import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Create pgvector extension if it doesn't exist
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield

from sqlalchemy import text

app = FastAPI(
    title="Autonomous Research Agent",
    description="A multi-agent system for autonomous AI research",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
