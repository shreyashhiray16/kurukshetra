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

    # Extract structured requirements using Gemini (with fallback)
    extracted = JobExtractorService.extract_requirements(raw_text, payload.source_url)

    # Persist Job record
    import json
    role_profile_str = json.dumps(extracted.role_profile) if extracted.role_profile else None

    job = Job(
        title=extracted.title,
        company=extracted.company,
        source_url=payload.source_url,
        raw_text=raw_text,
        role_profile=role_profile_str
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

    role_prof_dict = json.loads(job.role_profile) if job.role_profile else None
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        source_url=job.source_url,
        raw_text=job.raw_text,
        role_profile=role_prof_dict,
        created_at=job.created_at,
        requirements=req_dicts,
        extraction_source=JobExtractorService.last_source,
        llm_model=JobExtractorService.last_model,
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, session: Session = Depends(get_session)):
    """Fetch job details and its associated structured requirements."""
    import json
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
    role_prof_dict = json.loads(job.role_profile) if job.role_profile else None

    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        source_url=job.source_url,
        raw_text=job.raw_text,
        role_profile=role_prof_dict,
        created_at=job.created_at,
        requirements=req_dicts
    )

@router.get("/", response_model=List[JobResponse])
def list_jobs(session: Session = Depends(get_session)):
    """List all imported jobs."""
    import json
    jobs = session.exec(select(Job)).all()
    results = []
    for j in jobs:
        reqs = session.exec(select(Requirement).where(Requirement.job_id == j.id)).all()
        role_prof_dict = json.loads(j.role_profile) if j.role_profile else None
        results.append(
            JobResponse(
                id=j.id,
                title=j.title,
                company=j.company,
                source_url=j.source_url,
                raw_text=j.raw_text,
                role_profile=role_prof_dict,
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
