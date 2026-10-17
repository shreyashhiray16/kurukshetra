from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.entities import Job, Requirement
from app.schemas.job import JobImportRequest, JobResponse
from app.services.job_fetcher import JobFetcherService
from app.services.job_extractor import JobExtractorService

router = APIRouter()

@router.post("/import", response_model=JobResponse)
async def import_job(payload: JobImportRequest, session: Session = Depends(get_session)):
    """Import a job listing from either a source URL (using direct scraper/Jina Reader) or raw text."""
    if not payload.source_url and not payload.raw_text:
        raise HTTPException(status_code=400, detail="Either source_url or raw_text must be provided.")

    raw_text = payload.raw_text
    
    # If source_url provided and no raw_text, fetch it
    if payload.source_url and not raw_text:
        try:
            raw_text = await JobFetcherService.fetch_url_content(payload.source_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch content from URL: {str(e)}")

    if not raw_text or len(raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="The job listing text is too short or empty.")

    from app.services.job_importer import persist_job_and_requirements
    return persist_job_and_requirements(
        session=session,
        raw_text=raw_text,
        source_url=payload.source_url,
        source="manual",
        external_id=None,
        apply_url=payload.source_url
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
