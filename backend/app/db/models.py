from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base

class ResearchJob(Base):
    __tablename__ = "research_jobs"
    id = Column(String, primary_key=True, index=True)
    user_question = Column(String, nullable=False)
    status = Column(String, default="planning") # planning, searching, extracting, generating, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    research_depth = Column(String, default="standard")
    
    sources = relationship("Source", back_populates="job")
    claims = relationship("Claim", back_populates="job")
    report = relationship("Report", uselist=False, back_populates="job")

class Source(Base):
    __tablename__ = "sources"
    id = Column(String, primary_key=True, index=True)
    research_job_id = Column(String, ForeignKey("research_jobs.id"))
    title = Column(String)
    url = Column(String)
    publisher = Column(String)
    published_at = Column(String, nullable=True)
    source_type = Column(String, default="webpage")
    relevance_score = Column(Float, nullable=True)
    
    job = relationship("ResearchJob", back_populates="sources")
    chunks = relationship("ExtractedContent", back_populates="source")
    evidence = relationship("Evidence", back_populates="source")

class ExtractedContent(Base):
    __tablename__ = "extracted_contents"
    id = Column(String, primary_key=True, index=True)
    source_id = Column(String, ForeignKey("sources.id"))
    content = Column(Text)
    embedding = Column(Vector(768))
    
    source = relationship("Source", back_populates="chunks")

class Claim(Base):
    __tablename__ = "claims"
    id = Column(String, primary_key=True, index=True)
    research_job_id = Column(String, ForeignKey("research_jobs.id"))
    claim = Column(Text)
    confidence = Column(Float)
    
    job = relationship("ResearchJob", back_populates="claims")
    evidence = relationship("Evidence", back_populates="claim")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(String, primary_key=True, index=True)
    claim_id = Column(String, ForeignKey("claims.id"))
    source_id = Column(String, ForeignKey("sources.id"))
    text = Column(Text)
    
    claim = relationship("Claim", back_populates="evidence")
    source = relationship("Source", back_populates="evidence")

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, index=True)
    research_job_id = Column(String, ForeignKey("research_jobs.id"), unique=True)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    job = relationship("ResearchJob", back_populates="report")
