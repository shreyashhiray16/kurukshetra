import json
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.entities import Job, Repository, Requirement, Assessment, Citation, AuditHistory, AssessmentStatus
from app.schemas.assessment import (
    AssessmentRunRequest,
    AssessmentResponse,
    AssessmentSummary,
    SkillAssessmentResult,
    CitationItem
)
from app.services.github_scanner import GitHubScannerService
from app.services.assessment_engine import AssessmentEngineService

router = APIRouter()

@router.post("/run", response_model=AssessmentResponse)
async def run_assessment(payload: AssessmentRunRequest, session: Session = Depends(get_session)):
    """
    Run an end-to-end skill assessment and gap analysis for a Job and connected Repository:
    1. Fetches job requirements and repo file tree.
    2. Runs deterministic evidence extraction and citation validation.
    3. Persists Assessment, Citation, and AuditHistory records.
    4. Computes weighted match score and actionable next steps for skill gaps.
    """
    job = session.exec(select(Job).where(Job.id == payload.job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    repo = session.exec(select(Repository).where(Repository.id == payload.repo_id)).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    requirements = session.exec(select(Requirement).where(Requirement.job_id == job.id)).all()
    if not requirements:
        raise HTTPException(status_code=400, detail="Job has no extracted requirements.")

    # Get repository file tree
    tree = await GitHubScannerService.get_repo_tree(repo.full_name, repo.latest_commit_sha or "main")
    tree_paths = [item["path"] for item in tree]
    content_cache: dict = {}

    skill_results: List[SkillAssessmentResult] = []

    for req in requirements:
        eval_result = await AssessmentEngineService.evaluate_requirement(req, repo, tree_paths, content_cache)
        skill_results.append(eval_result)

        # Check existing assessment record for this requirement and repo
        existing_assessment = session.exec(
            select(Assessment).where(
                Assessment.requirement_id == req.id,
                Assessment.repo_id == repo.id
            )
        ).first()

        prev_status = existing_assessment.status.value if existing_assessment else None

        if existing_assessment:
            existing_assessment.status = eval_result.status
            existing_assessment.confidence_score = eval_result.confidence_score
            existing_assessment.reason = eval_result.reason
            existing_assessment.llm_model = eval_result.llm_model
            existing_assessment.llm_raw_response = json.dumps(eval_result.llm_response) if eval_result.llm_response else None
            existing_assessment.evaluated_at = datetime.now(timezone.utc)
            session.add(existing_assessment)
            session.flush()
            assessment_record = existing_assessment

            # Delete old citations
            old_citations = session.exec(select(Citation).where(Citation.assessment_id == assessment_record.id)).all()
            for old_c in old_citations:
                session.delete(old_c)
        else:
            assessment_record = Assessment(
                requirement_id=req.id,
                repo_id=repo.id,
                status=eval_result.status,
                confidence_score=eval_result.confidence_score,
                reason=eval_result.reason,
                llm_model=eval_result.llm_model,
                llm_raw_response=json.dumps(eval_result.llm_response) if eval_result.llm_response else None,
            )
            session.add(assessment_record)
            session.flush()

        # Persist citations
        for cit in eval_result.citations:
            citation_entity = Citation(
                assessment_id=assessment_record.id,
                file_path=cit.file_path,
                start_line=cit.start_line,
                end_line=cit.end_line,
                commit_sha=cit.commit_sha,
                snippet_text=cit.snippet_text,
                github_url=cit.github_url
            )
            session.add(citation_entity)

        # Record audit history on status changes
        if prev_status != eval_result.status.value:
            audit = AuditHistory(
                requirement_id=req.id,
                previous_status=prev_status,
                new_status=eval_result.status.value,
                trigger_event="manual_assessment_run",
                commit_sha=repo.latest_commit_sha
            )
            session.add(audit)

    session.commit()

    summary = AssessmentEngineService.calculate_summary(skill_results)

    return AssessmentResponse(
        job_id=job.id,
        job_title=job.title,
        repo_id=repo.id,
        repo_full_name=repo.full_name,
        evaluated_at=datetime.now(timezone.utc),
        summary=summary,
        skill_assessments=skill_results
    )

@router.get("/job/{job_id}", response_model=List[AssessmentResponse])
def get_assessments_for_job(job_id: int, session: Session = Depends(get_session)):
    """Fetch existing assessments grouped by repository for a job."""
    job = session.exec(select(Job).where(Job.id == job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    repos = session.exec(select(Repository)).all()
    results = []

    for repo in repos:
        assessments = session.exec(
            select(Assessment).where(
                Assessment.repo_id == repo.id,
                Assessment.requirement_id.in_([r.id for r in job.requirements])
            )
        ).all()

        if assessments:
            skill_results = []
            for a in assessments:
                req = a.requirement
                citations = [
                    CitationItem(
                        file_path=c.file_path,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        commit_sha=c.commit_sha,
                        snippet_text=c.snippet_text,
                        github_url=c.github_url
                    ) for c in a.citations
                ]
                skill_results.append(
                    SkillAssessmentResult(
                        requirement_id=req.id,
                        requirement_title=req.title,
                        category=req.category,
                        requirement_type=req.requirement_type.value,
                        weight=req.weight,
                        source_snippet=req.source_snippet,
                        status=a.status,
                        confidence_score=a.confidence_score,
                        reason=a.reason,
                        limitations=[],
                        next_step=None,
                        citations=citations,
                        llm_used=bool(a.llm_model),
                        llm_model=a.llm_model,
                        llm_response=json.loads(a.llm_raw_response) if a.llm_raw_response else None,
                    )
                )

            summary = AssessmentEngineService.calculate_summary(skill_results)
            results.append(
                AssessmentResponse(
                    job_id=job.id,
                    job_title=job.title,
                    repo_id=repo.id,
                    repo_full_name=repo.full_name,
                    evaluated_at=assessments[0].evaluated_at,
                    summary=summary,
                    skill_assessments=skill_results
                )
            )

    return results

@router.get("/history")
def assessment_history(session: Session = Depends(get_session)):
    """Timeline of status transitions (architecture: Change History)."""
    rows = session.exec(select(AuditHistory).order_by(AuditHistory.created_at.desc())).all()
    return [
        {
            "id": r.id,
            "requirement_id": r.requirement_id,
            "previous_status": r.previous_status,
            "new_status": r.new_status,
            "trigger_event": r.trigger_event,
            "commit_sha": r.commit_sha,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/audit/{requirement_id}", response_model=List[AuditHistory])
def get_audit_history(requirement_id: int, session: Session = Depends(get_session)):
    """Fetch timeline of status transitions for a specific job requirement."""
    return session.exec(
        select(AuditHistory).where(AuditHistory.requirement_id == requirement_id).order_by(AuditHistory.created_at.desc())
    ).all()
