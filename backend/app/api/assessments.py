import json
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.entities import Job, Repository, Requirement, Assessment, Citation, AuditHistory, AssessmentStatus
from app.schemas.assessment import (
    AssessmentRunRequest,
    MultiRepoAssessmentRunRequest,
    RepoContribution,
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

    repo_id_val = repo.id
    repo_full_name_val = repo.full_name
    latest_commit_sha_val = repo.latest_commit_sha or "main"

    # Get repository file tree
    tree = await GitHubScannerService.get_repo_tree(repo_full_name_val, latest_commit_sha_val)
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
                Assessment.repo_id == repo_id_val
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
                repo_id=repo_id_val,
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
                commit_sha=latest_commit_sha_val
            )
            session.add(audit)

    session.commit()

    summary = AssessmentEngineService.calculate_summary(skill_results)

    return AssessmentResponse(
        job_id=job.id,
        job_title=job.title,
        repo_id=repo_id_val,
        repo_full_name=repo_full_name_val,
        evaluated_at=datetime.now(timezone.utc),
        summary=summary,
        skill_assessments=skill_results
    )

STATUS_RANK = {
    AssessmentStatus.MET: 4,
    AssessmentStatus.PARTIAL: 3,
    AssessmentStatus.NEEDS_REVIEW: 2,
    AssessmentStatus.UNMET: 1
}

@router.post("/run-multi", response_model=AssessmentResponse)
async def run_multi_assessment(payload: MultiRepoAssessmentRunRequest, session: Session = Depends(get_session)):
    """
    Run multi-repo skill assessment (1 Job x N Repos, 1-10 repos):
    1. Evaluates all requirements across all selected repositories concurrently (semaphore 3).
    2. Applies deterministic merge rule per requirement:
       - Best status wins: MET > PARTIAL > NEEDS_REVIEW > UNMET
       - Highest confidence score wins
       - Union of citations across all repos with repo_full_name tags
    3. Persists per-repo Assessment and Citation records.
    4. Computes overall weighted match score and per-repo contribution breakdown.
    """
    if not payload.repo_ids:
        raise HTTPException(status_code=400, detail="At least one repository must be selected.")
    if len(payload.repo_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 repositories can be evaluated in one pass.")

    job = session.exec(select(Job).where(Job.id == payload.job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    requirements = session.exec(select(Requirement).where(Requirement.job_id == job.id)).all()
    if not requirements:
        raise HTTPException(status_code=400, detail="Job has no extracted requirements.")

    # Load all selected repos
    repos = session.exec(select(Repository).where(Repository.id.in_(payload.repo_ids))).all()
    if not repos:
        raise HTTPException(status_code=404, detail="No matching repositories found for provided repo_ids.")

    repo_meta_map = {
        r.id: {
            "id": r.id,
            "full_name": r.full_name,
            "latest_commit_sha": r.latest_commit_sha or "main",
            "default_branch": r.default_branch or "main",
        }
        for r in repos
    }

    semaphore = asyncio.Semaphore(3)

    # Helper to evaluate one repo
    async def evaluate_single_repo(repo: Repository):
        async with semaphore:
            r_meta = repo_meta_map[repo.id]
            tree = await GitHubScannerService.get_repo_tree(r_meta["full_name"], r_meta["latest_commit_sha"])
            tree_paths = [item["path"] for item in tree]
            content_cache: dict = {}
            results = []
            for req in requirements:
                eval_res = await AssessmentEngineService.evaluate_requirement(req, repo, tree_paths, content_cache)
                # Tag citations with the repo_full_name
                for c in eval_res.citations:
                    c.repo_full_name = r_meta["full_name"]
                results.append((req, r_meta, eval_res))
            return r_meta, results

    # Run evaluations concurrently with semaphore
    eval_tasks = [evaluate_single_repo(r) for r in repos]
    all_repo_evals = await asyncio.gather(*eval_tasks)

    # Persist per-repo results and track per-repo metrics
    # repo_id -> {'met': count, 'partial': count}
    repo_stats = {r.id: {"met": 0, "partial": 0, "full_name": repo_meta_map[r.id]["full_name"]} for r in repos}

    # Group results by requirement_id: req_id -> list of (repo_meta, eval_result)
    req_evaluations: dict = {req.id: [] for req in requirements}

    for r_meta, evals in all_repo_evals:
        repo_id = r_meta["id"]
        for req, _, eval_result in evals:
            req_evaluations[req.id].append((r_meta, eval_result))

            if eval_result.status == AssessmentStatus.MET:
                repo_stats[repo_id]["met"] += 1
            elif eval_result.status == AssessmentStatus.PARTIAL:
                repo_stats[repo_id]["partial"] += 1

            # Persist per-repo Assessment record
            existing_assessment = session.exec(
                select(Assessment).where(
                    Assessment.requirement_id == req.id,
                    Assessment.repo_id == repo_id
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

                old_citations = session.exec(select(Citation).where(Citation.assessment_id == assessment_record.id)).all()
                for old_c in old_citations:
                    session.delete(old_c)
            else:
                assessment_record = Assessment(
                    requirement_id=req.id,
                    repo_id=repo_id,
                    status=eval_result.status,
                    confidence_score=eval_result.confidence_score,
                    reason=eval_result.reason,
                    llm_model=eval_result.llm_model,
                    llm_raw_response=json.dumps(eval_result.llm_response) if eval_result.llm_response else None,
                )
                session.add(assessment_record)
                session.flush()

            for cit in eval_result.citations:
                session.add(Citation(
                    assessment_id=assessment_record.id,
                    file_path=cit.file_path,
                    start_line=cit.start_line,
                    end_line=cit.end_line,
                    commit_sha=cit.commit_sha,
                    snippet_text=cit.snippet_text,
                    github_url=cit.github_url
                ))

            if prev_status != eval_result.status.value:
                session.add(AuditHistory(
                    requirement_id=req.id,
                    previous_status=prev_status,
                    new_status=eval_result.status.value,
                    trigger_event="multi_repo_assessment_run",
                    commit_sha=r_meta["latest_commit_sha"]
                ))

    session.commit()

    # Now apply Merge Rules across repos for each requirement
    merged_skill_results: List[SkillAssessmentResult] = []

    for req in requirements:
        candidates = req_evaluations[req.id]  # list of (r_meta, eval_result)
        if not candidates:
            continue

        # Sort candidates by status rank descending, then confidence_score descending
        candidates.sort(key=lambda item: (STATUS_RANK.get(item[1].status, 0), item[1].confidence_score), reverse=True)
        best_repo_meta, best_eval = candidates[0]

        # Union of citations across all repos that found evidence
        all_citations: List[CitationItem] = []
        evidence_repos_set = set()
        seen_citation_keys = set()

        for c_repo_meta, c_eval in candidates:
            if c_eval.citations:
                evidence_repos_set.add(c_repo_meta["full_name"])
                for cit in c_eval.citations:
                    cit_key = (c_repo_meta["full_name"], cit.file_path, cit.start_line, cit.end_line)
                    if cit_key not in seen_citation_keys:
                        seen_citation_keys.add(cit_key)
                        all_citations.append(cit)

        winning_repo_name = best_repo_meta["full_name"] if best_eval.status in (AssessmentStatus.MET, AssessmentStatus.PARTIAL) else None

        merged_skill_results.append(SkillAssessmentResult(
            requirement_id=req.id,
            requirement_title=req.title,
            category=req.category,
            requirement_type=req.requirement_type.value,
            weight=req.weight,
            source_snippet=req.source_snippet,
            status=best_eval.status,
            confidence_score=best_eval.confidence_score,
            reason=best_eval.reason,
            limitations=best_eval.limitations,
            next_step=best_eval.next_step,
            citations=all_citations,
            llm_used=best_eval.llm_used,
            llm_model=best_eval.llm_model,
            llm_response=best_eval.llm_response,
            winning_repo=winning_repo_name,
            evidence_repos=sorted(list(evidence_repos_set))
        ))

    # Calculate overall aggregated summary
    summary = AssessmentEngineService.calculate_summary(merged_skill_results)

    # Calculate per-repo contribution breakdown
    contributions: List[RepoContribution] = []
    total_reqs = len(requirements) or 1
    for r in repos:
        st = repo_stats[r.id]
        score_pct = round(((st["met"] * 1.0 + st["partial"] * 0.5) / total_reqs) * 100, 1)
        contributions.append(RepoContribution(
            repo_id=r.id,
            repo_full_name=r.full_name,
            skills_met=st["met"],
            skills_partial=st["partial"],
            score_percentage=score_pct
        ))

    return AssessmentResponse(
        job_id=job.id,
        job_title=job.title,
        repo_id=repos[0].id,
        repo_full_name=", ".join([r.full_name for r in repos]),
        evaluated_at=datetime.now(timezone.utc),
        summary=summary,
        skill_assessments=merged_skill_results,
        repos=[r.full_name for r in repos],
        repo_contributions=contributions
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
