from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.entities import Job, Requirement
from app.schemas.job import JobImportRequest, JobResponse, JobFetchUrlRequest, JobFetchUrlResponse
from app.services.job_fetcher import JobFetcherService
from app.services.job_extractor import JobExtractorService

router = APIRouter()

@router.post("/fetch-url", response_model=JobFetchUrlResponse)
async def fetch_job_url(payload: JobFetchUrlRequest):
    """Quickly fetch job description content and metadata from any company career page URL."""
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL must be provided.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    try:
        details = await JobFetcherService.fetch_job_details(url, summarize=payload.summarize)
        return JobFetchUrlResponse(
            url=url,
            title=details.get("title"),
            company=details.get("company"),
            raw_text=details.get("raw_text", ""),
            strategy=details.get("strategy", "generic"),
            summarized=details.get("summarized", False),
            summary_model=details.get("summary_model")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch content from URL: {str(e)}")

@router.post("/import", response_model=JobResponse)
async def import_job(payload: JobImportRequest, session: Session = Depends(get_session)):
    """Import a job listing from either a source URL (using ATS API, JSON-LD, Trafilatura, or Jina) or raw text."""
    if not payload.source_url and not payload.raw_text:
        raise HTTPException(status_code=400, detail="Either source_url or raw_text must be provided.")

    raw_text = payload.raw_text
    meta_title = None
    meta_company = None
    
    # If source_url provided and no raw_text, fetch it
    if payload.source_url and not raw_text:
        try:
            details = await JobFetcherService.fetch_job_details(payload.source_url)
            raw_text = details.get("raw_text")
            meta_title = details.get("title")
            meta_company = details.get("company")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch content from URL: {str(e)}")

    if not raw_text or len(raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="The job listing text is too short or empty.")

    # Extract structured requirements using Gemini (with fallback)
    extracted = JobExtractorService.extract_requirements(raw_text, payload.source_url)

    job_title = (meta_title or extracted.title or "Software Engineer").strip()
    job_company = (meta_company or extracted.company or "Technology Company").strip()

    # Persist Job record
    job = Job(
        title=job_title,
        company=job_company,
        source_url=payload.source_url,
        raw_text=raw_text
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # Persist Requirements
    req_dicts = []
    for req in extracted.requirements:
        db_req = Requirement(
            job_id=job.id,
            title=req.title,
            category=req.category,
            requirement_type=req.requirement_type,
            weight=req.weight,
            source_snippet=req.source_snippet
        )
        session.add(db_req)
        session.commit()
        session.refresh(db_req)
        req_dicts.append({
            "id": db_req.id,
            "title": db_req.title,
            "category": db_req.category,
            "requirement_type": db_req.requirement_type.value,
            "weight": db_req.weight,
            "source_snippet": db_req.source_snippet
        })

    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        source_url=job.source_url,
        raw_text=job.raw_text,
        created_at=job.created_at,
        requirements=req_dicts,
        extraction_source=JobExtractorService.last_source,
        llm_model=JobExtractorService.last_model,
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, session: Session = Depends(get_session)):
    """Fetch job details and its associated structured requirements."""
    job = session.exec(select(Job).where(Job.id == job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    reqs = session.exec(select(Requirement).where(Requirement.job_id == job.id)).all()
    req_dicts = [
        {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "requirement_type": r.requirement_type.value,
            "weight": r.weight,
            "source_snippet": r.source_snippet
        }
        for r in reqs
    ]

    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        source_url=job.source_url,
        raw_text=job.raw_text,
        created_at=job.created_at,
        requirements=req_dicts
    )

@router.get("/", response_model=List[JobResponse])
def list_jobs(session: Session = Depends(get_session)):
    """List all imported jobs."""
    jobs = session.exec(select(Job)).all()
    results = []
    for j in jobs:
        reqs = session.exec(select(Requirement).where(Requirement.job_id == j.id)).all()
        results.append(
            JobResponse(
                id=j.id,
                title=j.title,
                company=j.company,
                source_url=j.source_url,
                raw_text=j.raw_text,
                created_at=j.created_at,
                requirements=[
                    {
                        "id": r.id,
                        "title": r.title,
                        "category": r.category,
                        "requirement_type": r.requirement_type.value,
                        "weight": r.weight,
                        "source_snippet": r.source_snippet
                    }
                    for r in reqs
                ]
            )
        )
    return results
