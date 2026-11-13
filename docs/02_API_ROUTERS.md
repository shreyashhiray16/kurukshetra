# Deep Dive: Backend REST API Routers

This document details all API controllers in `backend/app/api/` and their respective request schemas in `backend/app/schemas/`.

---

## 1. `backend/app/api/health.py` (81 lines)

Exposes liveness, readiness, and comprehensive health monitoring endpoints.

- **`GET /api/v1/health`**:
  - Validates basic API responsiveness.
  - Returns timestamp, process status, and loaded LLM provider name.
- **`GET /api/v1/health/ready`**:
  - Readiness probe used by container orchestrators or health checks.
  - Performs active database query (`SELECT 1;`) to confirm the connection pool is functional.
  - Checks if LLM API keys are populated.
  - Returns HTTP 200 with readiness details, or HTTP 503 if the database is unreachable.
- **`GET /api/v1/health/live`**:
  - Liveness probe confirming that the FastAPI event loop is actively accepting connections.

---

## 2. `backend/app/api/jobs.py` (136 lines)

Manages job posting intake, remote URL scraping, and structured requirement extraction.

- **`POST /api/v1/jobs/parse`**:
  - Request Body: `JobCreate` schema containing `raw_text`, optional `title`, `company`, or `source_url`.
  - Workflow:
    1. If `source_url` is supplied without `raw_text`, calls `job_fetcher.fetch_job_description(url)` to scrape web content.
    2. Sends the raw text to `job_extractor.extract_requirements(raw_text)`.
    3. Persists the `Job` entity and all extracted `Requirement` child records within an atomic transaction.
    4. Serializes `role_profile` (seniority, domain, technical stack) into JSON.
    5. Returns the created `JobRead` model with its associated requirements.
- **`GET /api/v1/jobs`**:
  - Lists all stored jobs ordered by creation date, including requirement counts.
- **`GET /api/v1/jobs/{job_id}`**:
  - Retrieves a specific job by ID, returning all requirements, categories, types, and source citations.
- **`DELETE /api/v1/jobs/{job_id}`**:
  - Cascades deletion of a job posting and its child requirements from the database.

---

## 3. `backend/app/api/repos.py` (132 lines)

Handles GitHub repository connections, authentication, tree traversal, and commit validation.

- **`POST /api/v1/repos/connect`**:
  - Request Body: `RepoConnectRequest` (accepts URLs, SSH strings, or `owner/repo`).
  - Workflow:
    1. Parses repository string with `repo_parser.parse_github_repo()`. Returns HTTP 400 if invalid.
    2. Queries GitHub API (via `github_scanner.py`) to confirm repository existence, public visibility, or token access.
    3. Fetches default branch (e.g. `main`) and latest commit SHA.
    4. Upserts the `Repository` entity in the database to prevent duplicate entries.
- **`GET /api/v1/repos`**:
  - Lists all connected repositories with branch names and latest commit hashes.
- **`GET /api/v1/repos/{repo_id}`**:
  - Retrieves metadata for a specific repository.
- **`GET /api/v1/repos/{repo_id}/tree`**:
  - Inspects file structure and returns tree metadata, including file paths, sizes, and detected manifest files (`package.json`, `requirements.txt`, etc.).

---

## 4. `backend/app/api/assessments.py` (277 lines)

The central evaluation controller that pairs job requirements against repository code.

- **`POST /api/v1/assessments/run`**:
  - Request Body: `AssessmentRunRequest` containing `job_id`, `repo_id`, and optional `reassess` flag.
  - Workflow:
    1. Retrieves `Job` requirements and `Repository` commit information from the database.
    2. Calls `assessment_engine.evaluate_repository(job, repo)`:
       - Runs manifest dependency scanning.
       - Runs static pattern/code snippet matching.
       - Calls LLM provider for contextual understanding and reasoning.
    3. Generates `Citation` entries mapping back to specific repository files and line numbers.
    4. Calls `readiness_calculator.calculate_readiness_score(assessments)`:
       - Produces overall readiness score (0-100%).
       - Calculates category scores (e.g., Languages: 85%, Architecture: 40%).
    5. Stores `Assessment` and `Citation` records in the database.
    6. Returns `AssessmentResponse` containing readiness scores, requirement outcomes, and code citations.
- **`GET /api/v1/assessments/{assessment_id}`**:
  - Retrieves past assessment results.
- **`GET /api/v1/assessments/{assessment_id}/roadmap`**:
  - Generates a customized learning roadmap for unmet or partial requirements.
  - Queries `resource_finder.py` to retrieve YouTube tutorials and curated learning links.

---

## 5. `backend/app/api/webhooks.py` (95 lines)

Handles real-time GitHub push webhooks for continuous assessment updates.

- **`POST /api/v1/webhooks/github`**:
  - Headers: `X-GitHub-Event`, `X-Hub-Signature-256`, `X-GitHub-Delivery`.
  - Workflow:
    1. Validates that `X-GitHub-Event` is `push`.
    2. Computes HMAC-SHA256 signature over raw request body using `settings.GITHUB_WEBHOOK_SECRET`.
    3. Compares computed signature against `X-Hub-Signature-256` using constant-time comparison (`hmac.compare_digest`). Returns HTTP 401 if invalid.
    4. Checks `WebhookEvent` table for `delivery_id` to prevent duplicate processing.
    5. Extracts modified, added, and removed files from commit payload.
    6. Invokes `change_detector.process_github_push(...)` in the background:
       - Re-evaluates only requirements affected by changed files.
       - Updates `Assessment` states and records an entry in `AuditHistory`.
    7. Returns HTTP 200 with delivery status.

---

## 6. Schemas Directory (`backend/app/schemas/`)

- **`job.py`** (29 lines): Defines `JobCreate`, `JobRead`, and `RequirementRead` Pydantic models.
- **`repo.py`** (27 lines): Defines `RepoConnectRequest` and `RepoRead` schemas.
- **`assessment.py`** (104 lines): Defines `AssessmentRunRequest`, `CitationRead`, `AssessmentRead`, `ReadinessScore`, and `AssessmentResponse` schemas with strict type validation.

