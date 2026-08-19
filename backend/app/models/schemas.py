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
    
    model_config = ConfigDict(from_attributes=True)

class SourceResponse(BaseModel):
    id: str
    title: Optional[str]
    url: Optional[str]
    publisher: Optional[str]
    published_at: Optional[str]
    source_type: Optional[str]
    relevance_score: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)

class EvidenceResponse(BaseModel):
    id: str
    text: str
    source: SourceResponse
    
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
