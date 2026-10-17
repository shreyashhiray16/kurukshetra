import pytest
from app.services.job_sources.naukri_provider import _normalize
from app.schemas.job import JobListing

def test_normalize_valid_naukri_payload():
    raw_payload = {
        "jobId": "12345678",
        "title": "Senior Python Backend Developer",
        "companyName": "Acme Technologies",
        "placeholders": [
            {"type": "location", "label": "Pune / Remote"},
            {"type": "experience", "label": "3-6 Yrs"},
            {"type": "salary", "label": "₹ 18 - 28 Lacs P.A."}
        ],
        "footerPlaceholderLabel": "Just now",
        "tagsAndSkills": [
            {"label": "Python"},
            {"label": "FastAPI"},
            {"label": "Docker"},
            {"label": "PostgreSQL"}
        ],
        "jobDescription": "<p>We are seeking a <b>Senior Python Developer</b> with FastAPI experience.</p>",
        "jdURL": "/job-listings-senior-python-12345678"
    }

    normalized = _normalize(raw_payload)
    assert normalized is not None
    assert isinstance(normalized, JobListing)
    assert normalized.external_id == "12345678"
    assert normalized.source == "naukri"
    assert normalized.title == "Senior Python Backend Developer"
    assert normalized.company == "Acme Technologies"
    assert normalized.location == "Pune / Remote"
    assert normalized.experience == "3-6 Yrs"
    assert normalized.salary == "₹ 18 - 28 Lacs P.A."
    assert "FastAPI" in normalized.skills
    assert "We are seeking a Senior Python Developer" in normalized.snippet
    assert normalized.apply_url.startswith("https://www.naukri.com")

def test_normalize_empty_or_malformed_returns_none():
    assert _normalize({}) is None
    assert _normalize(None) is None
    assert _normalize({"companyName": "Acme Only"}) is None

def test_normalize_alternative_keys():
    raw_payload = {
        "id": "alt_999",
        "jobTitle": "DevOps Engineer",
        "company": {"name": "CloudWorks Inc"},
        "location": "Bengaluru",
        "experience": "2-4 Yrs",
        "salary": "Not Disclosed",
        "tags": ["Kubernetes", "AWS", "Terraform"],
        "snippet": "Design and manage CI/CD pipelines.",
        "url": "https://www.naukri.com/custom-job-alt_999"
    }

    normalized = _normalize(raw_payload)
    assert normalized is not None
    assert normalized.external_id == "alt_999"
    assert normalized.title == "DevOps Engineer"
    assert normalized.company == "CloudWorks Inc"
    assert normalized.location == "Bengaluru"
    assert "Kubernetes" in normalized.skills
    assert normalized.apply_url == "https://www.naukri.com/custom-job-alt_999"
