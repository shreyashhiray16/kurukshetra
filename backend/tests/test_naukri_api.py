import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.job_sources.registry import job_source_registry

@pytest.fixture
def client():
    return TestClient(app)

def test_naukri_roles_suggest(client):
    res = client.get("/api/v1/naukri/roles/suggest?q=python")
    assert res.status_code == 200
    roles = res.json()
    assert isinstance(roles, list)
    assert any("python" in r.lower() for r in roles)

def test_naukri_search_and_deduplicated_import(client):
    from unittest.mock import patch
    from app.schemas.job import JobExtractionResult, ExtractedRequirement
    from app.models.entities import RequirementType

    mock_extracted = JobExtractionResult(
        title="Senior Python Developer",
        company="Infosys Ltd",
        requirements=[
            ExtractedRequirement(
                title="FastAPI Web Framework",
                category="Frameworks",
                requirement_type=RequirementType.REQUIRED,
                weight=1.0,
                source_snippet="REST APIs with FastAPI"
            )
        ]
    )

    # 1. Search jobs
    res = client.get("/api/v1/naukri/search?role=Python+Developer&location=Pune")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "Python Developer"
    assert "results" in data
    assert len(data["results"]) > 0

    first_job = data["results"][0]
    ext_id = first_job["external_id"]

    # 2. First Import
    import_payload = {
        "external_id": ext_id,
        "apply_url": first_job["apply_url"],
        "title": first_job["title"],
        "company": first_job["company"],
        "snippet": first_job["snippet"],
        "location": first_job["location"]
    }
    with patch("app.services.job_extractor.JobExtractorService.extract_requirements", return_value=mock_extracted):
        imp_res1 = client.post("/api/v1/naukri/import", json=import_payload)
        assert imp_res1.status_code == 200
        job1_data = imp_res1.json()
        assert job1_data["id"] is not None
        assert job1_data["source"] == "naukri"
        assert job1_data["external_id"] == ext_id

        # 3. Second Import with same external_id -> must be deduplicated
        imp_res2 = client.post("/api/v1/naukri/import", json=import_payload)
        assert imp_res2.status_code == 200
        job2_data = imp_res2.json()
        assert job2_data["id"] == job1_data["id"]
        assert job2_data["extraction_source"] == "deduplicated_cache"

def test_job_source_fallback_on_403_or_blocked():
    """Verify registry automatically falls back to fallback provider if primary raises PermissionError (anti-bot 403)."""
    import asyncio
    async def _run():
        with patch.object(job_source_registry.naukri_provider, "search", side_effect=PermissionError("SOURCE_BLOCKED")):
            results, provider, cached = await job_source_registry.search_jobs("Data Analyst")
            assert len(results) > 0
            assert "fallback" in provider

    asyncio.run(_run())
