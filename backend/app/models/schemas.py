from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ResearchJobBase(BaseModel):
    user_question: str
    research_depth: str = "standard"

class ResearchJobCreate(ResearchJobBase):
    pass

class ResearchJobResponse(ResearchJobBase):
    id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class SourceResponse(BaseModel):
    id: str
    title: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[str] = None
    source_type: Optional[str] = None
    relevance_score: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class EvidenceResponse(BaseModel):
    id: str
    text: str
    source: Optional[SourceResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class ClaimResponse(BaseModel):
    id: str
    claim: str
    confidence: float
    evidence: List[EvidenceResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class ReportResponse(BaseModel):
    id: str
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
