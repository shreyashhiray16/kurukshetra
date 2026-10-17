import pytest
from app.models.entities import AssessmentStatus
from app.schemas.assessment import SkillAssessmentResult, CitationItem

STATUS_RANK = {
    AssessmentStatus.MET: 4,
    AssessmentStatus.PARTIAL: 3,
    AssessmentStatus.NEEDS_REVIEW: 2,
    AssessmentStatus.UNMET: 1
}

def test_multi_repo_merge_rule_best_status_and_citation_union():
    """
    Test deterministic merge rule:
    1. Status priority: MET > PARTIAL > NEEDS_REVIEW > UNMET
    2. Highest confidence wins
    3. Union of citations across all candidate repositories with repo tags
    """
    citation_repo1 = CitationItem(
        file_path="backend/app/main.py",
        start_line=10,
        end_line=20,
        commit_sha="c9f3e8b417a250d4f9b871c890a1b2c3d4e5f678",
        snippet_text="app = FastAPI()",
        github_url="https://github.com/org/repo-a/blob/main/backend/app/main.py#L10-L20",
        repo_full_name="org/repo-a"
    )

    citation_repo2 = CitationItem(
        file_path="Dockerfile",
        start_line=1,
        end_line=5,
        commit_sha="a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
        snippet_text="FROM python:3.12-slim",
        github_url="https://github.com/org/repo-b/blob/main/Dockerfile#L1-L5",
        repo_full_name="org/repo-b"
    )

    eval_repo_a = SkillAssessmentResult(
        requirement_id=1,
        requirement_title="FastAPI Microservices",
        category="Frameworks",
        requirement_type="required",
        weight=1.0,
        source_snippet="FastAPI backend experience",
        status=AssessmentStatus.MET,
        confidence_score=0.95,
        reason="Real code definitions found in app/main.py",
        citations=[citation_repo1]
    )

    eval_repo_b = SkillAssessmentResult(
        requirement_id=1,
        requirement_title="FastAPI Microservices",
        category="Frameworks",
        requirement_type="required",
        weight=1.0,
        source_snippet="FastAPI backend experience",
        status=AssessmentStatus.PARTIAL,
        confidence_score=0.60,
        reason="Found dependency in requirements.txt",
        citations=[citation_repo2]
    )

    candidates = [
        ("org/repo-b", eval_repo_b),
        ("org/repo-a", eval_repo_a)
    ]

    # Sort using status rank descending, then confidence descending
    candidates.sort(key=lambda item: (STATUS_RANK.get(item[1].status, 0), item[1].confidence_score), reverse=True)
    best_repo, best_eval = candidates[0]

    assert best_repo == "org/repo-a"
    assert best_eval.status == AssessmentStatus.MET
    assert best_eval.confidence_score == 0.95

    # Citation union
    all_citations = []
    seen = set()
    for repo_name, ev in candidates:
        for c in ev.citations:
            k = (repo_name, c.file_path, c.start_line, c.end_line)
            if k not in seen:
                seen.add(k)
                all_citations.append(c)

    assert len(all_citations) == 2
    repo_names = {c.repo_full_name for c in all_citations}
    assert "org/repo-a" in repo_names
    assert "org/repo-b" in repo_names
