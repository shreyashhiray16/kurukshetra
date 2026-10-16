from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.models.entities import RequirementType

class ExtractedRequirement(BaseModel):
    title: str
    category: str
    requirement_type: RequirementType
    weight: float
    source_snippet: str

class JobExtractionResult(BaseModel):
    title: str
    company: Optional[str] = None
    requirements: List[ExtractedRequirement]

class JobImportRequest(BaseModel):
    source_url: Optional[str] = None
    raw_text: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    source_url: Optional[str] = None
    raw_text: str
    created_at: datetime
    requirements: List[dict]
    extraction_source: Optional[str] = None
    llm_model: Optional[str] = None
