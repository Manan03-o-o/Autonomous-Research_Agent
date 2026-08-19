from fastapi import APIRouter
from .routes import router as research_router

router = APIRouter()
router.include_router(research_router, prefix="/research", tags=["research"])
