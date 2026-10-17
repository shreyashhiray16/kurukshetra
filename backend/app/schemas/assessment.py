from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.entities import AssessmentStatus

class CitationItem(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    commit_sha: str
    snippet_text: str
    github_url: Optional[str] = None
    is_dependency_or_doc_only: bool = False
    repo_full_name: Optional[str] = None

class SkillAssessmentResult(BaseModel):
    requirement_id: int
    requirement_title: str
    category: str
    requirement_type: str
    weight: float
    source_snippet: str
    status: AssessmentStatus
    confidence_score: float
    reason: str
    limitations: List[str] = []
    next_step: Optional[str] = None
    citations: List[CitationItem] = []
    llm_used: bool = False
    llm_model: Optional[str] = None
    llm_response: Optional[dict] = None
    winning_repo: Optional[str] = None
    evidence_repos: List[str] = []

class AssessmentRunRequest(BaseModel):
    job_id: int
    repo_id: int

class MultiRepoAssessmentRunRequest(BaseModel):
    job_id: int
    repo_ids: List[int]

class RepoContribution(BaseModel):
    repo_id: int
    repo_full_name: str
    skills_met: int
    skills_partial: int
    score_percentage: float

class AssessmentSummary(BaseModel):
    total_skills: int
    met: int
    partial: int
    unmet: int
    needs_review: int = 0
    overall_match_percentage: float
    weighted_score: float

class AssessmentResponse(BaseModel):
    job_id: int
    job_title: str
    repo_id: int
    repo_full_name: str
    evaluated_at: datetime
    summary: AssessmentSummary
    skill_assessments: List[SkillAssessmentResult]
    repos: Optional[List[str]] = None
    repo_contributions: Optional[List[RepoContribution]] = None
