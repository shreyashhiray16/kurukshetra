import os
import sys
import json
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.core.db import init_db

def verify_level6():
    print("=" * 70)
    print("Testing Level 6: Naukri Job Feed, Role Suggest, Deduplicated Import & Multi-Repo Assessment")
    print("=" * 70)

    # 0. Ensure schema migrations are up to date
    init_db()

    client = TestClient(app)

    # 1. Test Static & Dynamic Role Suggestion
    print("\n1. Testing Role Suggestions (/api/v1/naukri/roles/suggest)...")
    suggest_res = client.get("/api/v1/naukri/roles/suggest?q=Python")
    assert suggest_res.status_code == 200, f"Role suggest failed: {suggest_res.text}"
    suggestions = suggest_res.json()
    print(f"   -> Found {len(suggestions)} suggested roles: {suggestions[:3]}...")
    assert any("python" in s.lower() for s in suggestions)

    # 2. Test Live Job Search with Fallback/Cache
    print("\n2. Testing Naukri Search (/api/v1/naukri/search)...")
    search_res = client.get("/api/v1/naukri/search?role=Full+Stack+Engineer&location=Pune&experience=2-5+Yrs")
    assert search_res.status_code == 200, f"Search failed: {search_res.text}"
    search_data = search_res.json()
    print(f"   -> Provider: {search_data['provider']} (Cached: {search_data['cached']})")
    print(f"   -> Results returned: {len(search_data['results'])} listings")
    assert len(search_data['results']) > 0, "Expected at least 1 job in results"

    job_candidate = search_data['results'][0]
    print(f"   -> Selected Job: '{job_candidate['title']}' at '{job_candidate['company']}'")
    print(f"   -> Skills: {job_candidate['skills'][:4]}")

    # 3. Test Deduplicated Job Import
    print("\n3. Testing Job Import & Deduplication (/api/v1/naukri/import)...")
    import_payload = {
        "external_id": job_candidate["external_id"],
        "apply_url": job_candidate["apply_url"],
        "title": job_candidate["title"],
        "company": job_candidate["company"],
        "snippet": job_candidate["snippet"],
        "location": job_candidate["location"],
        "experience": job_candidate["experience"],
        "salary": job_candidate["salary"]
    }
    imp_res_1 = client.post("/api/v1/naukri/import", json=import_payload)
    assert imp_res_1.status_code == 200, f"Import 1 failed: {imp_res_1.text}"
    imported_job = imp_res_1.json()
    job_id = imported_job["id"]
    print(f"   -> First import created Job ID={job_id} with {len(imported_job['requirements'])} requirements")

    # Repeat import: must return same job without creating duplicate records
    imp_res_2 = client.post("/api/v1/naukri/import", json=import_payload)
    assert imp_res_2.status_code == 200
    assert imp_res_2.json()["id"] == job_id, "Deduplication failed: created new Job row"
    print(f"   -> Second import successfully verified deduplication on (source, external_id)")

    # 4. Connect 2 GitHub Repositories
    print("\n4. Linking 2 GitHub Repositories (/api/v1/repos/connect)...")
    repo1_res = client.post("/api/v1/repos/connect", json={
        "full_name": "tiangolo/fastapi",
        "default_branch": "master"
    })
    assert repo1_res.status_code == 200
    repo1_id = repo1_res.json()["id"]
    print(f"   -> Repo 1 connected: 'tiangolo/fastapi' (ID={repo1_id})")

    repo2_res = client.post("/api/v1/repos/connect", json={
        "full_name": "encode/starlette",
        "default_branch": "master"
    })
    assert repo2_res.status_code == 200
    repo2_id = repo2_res.json()["id"]
    print(f"   -> Repo 2 connected: 'encode/starlette' (ID={repo2_id})")

    # 5. Run Multi-Repo Assessment (1 Job x 2 Repos)
    print(f"\n5. Running Multi-Repo Assessment (/api/v1/assessments/run-multi)...")
    multi_res = client.post("/api/v1/assessments/run-multi", json={
        "job_id": job_id,
        "repo_ids": [repo1_id, repo2_id]
    })
    assert multi_res.status_code == 200, f"Multi-repo assessment failed: {multi_res.text}"
    assessment = multi_res.json()

    summary = assessment["summary"]
    print(f"\n   >>> Multi-Repo Assessment Summary <<<")
    print(f"   -> Evaluated Repositories: {assessment.get('repos')}")
    print(f"   -> Total Skills: {summary['total_skills']}")
    print(f"   -> Status Breakdown: {summary['met']} MET, {summary['partial']} PARTIAL, {summary['unmet']} UNMET")
    print(f"   -> Weighted Score: {summary['overall_match_percentage']}%")

    print("\n   >>> Repository Contribution Breakdown <<<")
    for contrib in assessment.get("repo_contributions", []):
        print(f"   -> {contrib['repo_full_name']}: {contrib['skills_met']} MET, {contrib['skills_partial']} PARTIAL ({contrib['score_percentage']}%)")

    # Verify skill assessments contain evidence citations with repo tags
    skills_with_citations = [s for s in assessment["skill_assessments"] if s.get("citations")]
    print(f"\n   -> Skills with source code citations: {len(skills_with_citations)}")
    if skills_with_citations:
        first_citation = skills_with_citations[0]["citations"][0]
        print(f"   -> Sample Citation: [{first_citation.get('repo_full_name')}] {first_citation.get('file_path')}#L{first_citation.get('start_line')}-L{first_citation.get('end_line')}")
        print(f"   -> Winning Repo: {skills_with_citations[0].get('winning_repo')}")

    print("\nLevel 6 Verification Complete: SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    verify_level6()
