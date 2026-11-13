# Deep Dive: Backend Core, Configuration & Data Models

This document breaks down every file and line of code in the backend infrastructure layer.

---

## 1. `backend/app/main.py`

This file is the main entry point for the FastAPI application.

```python
1: from contextlib import asynccontextmanager
2: from fastapi import FastAPI
3: from fastapi.middleware.cors import CORSMiddleware
4: from app.core.config import settings
5: from app.core.db import init_db
6: from app.api.health import router as health_router
7: from app.api.jobs import router as jobs_router
8: from app.api.repos import router as repos_router
9: from app.api.assessments import router as assessments_router
10: from app.api.webhooks import router as webhooks_router
```
* **Lines 1–3**: Imports asynchronous context manager tooling from standard library and core FastAPI constructs (`FastAPI` app class and `CORSMiddleware`).
* **Lines 4–5**: Imports the global application configuration (`settings`) and database initializer (`init_db`).
* **Lines 6–10**: Imports the route handlers from each domain module in `app/api/` (`health`, `jobs`, `repos`, `assessments`, `webhooks`).

```python
12: @asynccontextmanager
13: async def lifespan(app: FastAPI):
14:     # Initialize DB tables on startup
15:     init_db()
16:     yield
```
* **Lines 12–16**: Declares FastAPI's modern `lifespan` handler. Upon startup, it runs `init_db()` to configure SQLite WAL mode, create SQLModel tables, and execute column migrations before yielding control to handle HTTP requests.

```python
18: app = FastAPI(
19:     title=settings.PROJECT_NAME,
20:     openapi_url=f"{settings.API_V1_STR}/openapi.json",
21:     lifespan=lifespan,
22:     docs_url="/docs",
23:     redoc_url="/redoc"
24: )
```
* **Lines 18–24**: Instantiates the FastAPI application using metadata from `settings`, assigning OpenAPI schema paths and enabling interactive documentation at `/docs` (Swagger UI) and `/redoc`.

```python
26: # Set up CORS directly (No Nginx proxy needed)
27: app.add_middleware(
28:     CORSMiddleware,
29:     allow_origins=settings.CORS_ORIGINS,
30:     allow_credentials=True,
31:     allow_methods=["*"],
32:     allow_headers=["*"],
33: )
```
* **Lines 26–33**: Adds Cross-Origin Resource Sharing (CORS) middleware. Permits frontend development ports (Vite at `localhost:5173`, etc.) to communicate directly with this backend API without needing a reverse proxy.

```python
35: # Include routes
36: app.include_router(health_router, prefix=settings.API_V1_STR, tags=["System"])
37: app.include_router(jobs_router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])
38: app.include_router(repos_router, prefix=f"{settings.API_V1_STR}/repos", tags=["Repositories"])
39: app.include_router(assessments_router, prefix=f"{settings.API_V1_STR}/assessments", tags=["Assessments"])
40: app.include_router(webhooks_router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["Webhooks"])
```
* **Lines 35–40**: Mounts the API sub-routers under the versioned `/api/v1` prefix and assigns OpenAPI tags for grouping documentation.

```python
42: @app.get("/")
43: def root():
44:     return {
45:         "message": "AI Career Coach API is running.",
46:         "docs": "/docs",
47:         "health": f"{settings.API_V1_STR}/health"
48:     }
```
* **Lines 42–48**: Defines the root `/` endpoint returning a JSON health message and links to API documentation.

---

## 2. `backend/app/core/config.py`

This module manages all configuration, API keys, and environment variables.

```python
1: from pathlib import Path
2: from pydantic_settings import BaseSettings, SettingsConfigDict
3: 
4: # backend/app/core/config.py -> project root is three levels up
5: _ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
6: _BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
```
* **Lines 1–6**: Determines filesystem paths to the root and backend `.env` files using `pathlib.Path`.

```python
8: class Settings(BaseSettings):
9:     PROJECT_NAME: str = "AI Career Coach"
10:     API_V1_STR: str = "/api/v1"
11:     DATABASE_URL: str = "sqlite:///./career_coach.db"
```
* **Lines 8–11**: Defines defaults for the project name, API version path (`/api/v1`), and SQLite database URL.

```python
13:     # API Keys & Webhook Secrets
14:     GEMINI_API_KEY: str = ""
15:     GROQ_API_KEY: str = ""
16:     LLM_PROVIDER: str = "auto"
17:     # Gemini models
18:     GEMINI_MODEL: str = "gemini-3.5-flash"
19:     GEMINI_FALLBACK_MODELS: str = "gemini-3-flash-preview,gemma-4-26b-a4b-it"
20:     # Groq models
21:     GROQ_MODEL: str = "openai/gpt-oss-120b"
22:     GROQ_FALLBACK_MODELS: str = "qwen/qwen3.8-27b,openai/gpt-oss-20b"
23:     LLM_MAX_RETRIES: int = 1
24:     GITHUB_TOKEN: str = ""
25:     GITHUB_WEBHOOK_SECRET: str = "test-webhook-secret-key-12345"
26:     YOUTUBE_API_KEY: str = ""
```
* **Lines 13–26**: Configures AI credentials, primary and fallback model sequences (e.g. `gemini-3.5-flash`, `qwen/qwen3.8-27b`), GitHub integration credentials, and YouTube API keys.

```python
28:     # CORS
29:     CORS_ORIGINS: list[str] = [
30:         "http://localhost:1200",
31:         "http://127.0.0.1:1200",
32:         "http://localhost:3000",
33:         "http://localhost:5173",
34:         "http://127.0.0.1:3000",
35:         "http://127.0.0.1:5173",
36:         "http://localhost:8000",
37:     ]
```
* **Lines 28–37**: Explicit list of allowed origin URLs for CORS security.

```python
39:     # Root .env is listed last so the key you edit there wins over backend/.env
40:     model_config = SettingsConfigDict(
41:         env_file=(str(_BACKEND_ENV), str(_ROOT_ENV)),
42:         extra="allow",
43:     )
44: 
45: settings = Settings()
```
* **Lines 39–45**: Configures Pydantic to read both `.env` locations and instantiates the singleton `settings` object.

---

## 3. `backend/app/core/db.py`

This module initializes database engines, handles migrations, and delivers database sessions.

```python
1: from sqlmodel import create_engine, SQLModel, Session
2: from app.core.config import settings
3: 
4: # connect_args with timeout to prevent SQLite database lock errors
5: engine = create_engine(
6:     settings.DATABASE_URL,
7:     echo=False,
8:     connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in settings.DATABASE_URL else {}
9: )
```
* **Lines 1–9**: Creates the SQLModel database engine. If SQLite is detected, configures `check_same_thread=False` and a 30-second busy timeout to prevent database lock issues under concurrent access.

```python
11: def init_db():
12:     from app.models.entities import Job, Requirement, Repository, Assessment, Citation, AuditHistory, WebhookEvent, LearningResourceCache
13:     # Enable WAL mode for high concurrency in SQLite
14:     if "sqlite" in settings.DATABASE_URL:
15:         with engine.connect() as conn:
16:             conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
17:             conn.exec_driver_sql("PRAGMA busy_timeout=30000;")
18:     SQLModel.metadata.create_all(engine)
```
* **Lines 11–18**: Imports entities, turns on SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), sets a busy timeout, and creates missing tables with `create_all()`.

```python
19:     # create_all does not add columns to tables that already exist
20:     if "sqlite" in settings.DATABASE_URL:
21:         with engine.connect() as conn:
22:             # Migration for assessment
23:             cols_assessment = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(assessment)").fetchall()]
24:             if cols_assessment:
25:                 if "llm_model" not in cols_assessment:
26:                     conn.exec_driver_sql("ALTER TABLE assessment ADD COLUMN llm_model VARCHAR")
27:                 if "llm_raw_response" not in cols_assessment:
28:                     conn.exec_driver_sql("ALTER TABLE assessment ADD COLUMN llm_raw_response TEXT")
29: 
30:             # Migration for job
31:             cols_job = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(job)").fetchall()]
32:             if cols_job and "role_profile" not in cols_job:
33:                 conn.exec_driver_sql("ALTER TABLE job ADD COLUMN role_profile TEXT")
34: 
35:             # Migration for requirement
36:             cols_req = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(requirement)").fetchall()]
37:             if cols_req and "aliases" not in cols_req:
38:                 conn.exec_driver_sql("ALTER TABLE requirement ADD COLUMN aliases TEXT")
39: 
40:             conn.commit()
```
* **Lines 19–40**: Inspects SQLite table schemas via `PRAGMA table_info` and dynamically runs `ALTER TABLE ADD COLUMN` for columns added in newer revisions, preventing schema incompatibility crashes without heavy Alembic dependencies.

```python
42: def get_session():
43:     with Session(engine) as session:
44:         yield session
```
* **Lines 42–44**: FastAPI dependency injection generator yielding an active database session that closes automatically after the request.

---

## 4. `backend/app/core/repo_parser.py`

This module parses arbitrary user-provided GitHub repository identifiers into standardized `(owner, repo, full_name)` triplets.

```python
1: import re
2: from typing import Optional, Tuple
3: from urllib.parse import urlparse
4: 
5: REPO_NAME_REGEX = re.compile(r"^[A-Za-z0-9_.-]+$")
```
* **Lines 1–5**: Pre-compiles regular expression ensuring GitHub user and repository names only contain alphanumeric characters, underscores, dots, and hyphens.

```python
7: def parse_github_repo(input_str: Optional[str]) -> Optional[Tuple[str, str, str]]:
...
17:     if not input_str or not isinstance(input_str, str):
18:         return None
19:     raw = input_str.strip()
20:     if not raw:
21:         return None
```
* **Lines 7–21**: Validates non-empty input strings.

```python
23:     # Strip decorator suffix if present (e.g. " (main) - SHA: 1234567")
24:     raw = re.sub(r"\s*\([^)]*\)\s*-\s*SHA:.*$", "", raw, flags=re.IGNORECASE).strip()
25:     if not raw:
26:         return None
```
* **Lines 23–26**: Strips UI decorators appended to repository labels (e.g. branch names and commit hashes).

```python
28:     # SSH format: git@github.com:owner/repo(.git)?
29:     ssh_match = re.match(r"^git@github\.com:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$", raw, re.IGNORECASE)
30:     if ssh_match:
31:         owner, repo = ssh_match.group(1), ssh_match.group(2)
32:         if REPO_NAME_REGEX.match(owner) and REPO_NAME_REGEX.match(repo):
33:             return owner, repo, f"{owner}/{repo}"
34:         return None
```
* **Lines 28–34**: Matches SSH clone strings like `git@github.com:torvalds/linux.git` and extracts `owner` and `repo`.

```python
36:     # URL format
37:     if re.match(r"^(https?:)?//", raw, re.IGNORECASE) or raw.lower().startswith("www.github.com") or raw.lower().startswith("github.com"):
38:         normalized = raw
39:         if not re.match(r"^[a-zA-Z]+://", normalized):
40:             normalized = "https://" + re.sub(r"^//", "", normalized)
41:         try:
42:             parsed = urlparse(normalized)
43:             hostname = (parsed.hostname or "").lower()
44:             if hostname not in ("github.com", "www.github.com"):
45:                 return None
46:             parts = [p for p in parsed.path.split("/") if p]
47:             if len(parts) < 2:
48:                 return None
49:             owner = parts[0]
50:             repo = re.sub(r"\.git$", "", parts[1], flags=re.IGNORECASE)
51:             if REPO_NAME_REGEX.match(owner) and REPO_NAME_REGEX.match(repo):
52:                 return owner, repo, f"{owner}/{repo}"
53:             return None
54:         except Exception:
55:             return None
```
* **Lines 36–55**: Handles full HTTP/HTTPS web links (`https://github.com/facebook/react/tree/main`), normalizes protocols, extracts first two path tokens, and strips `.git` suffixes.

```python
57:     # Direct owner/repo
58:     cleaned = raw.rstrip("/")
59:     parts = cleaned.split("/")
60:     if len(parts) >= 2:
61:         owner = parts[0]
62:         repo = re.sub(r"\.git$", "", parts[1], flags=re.IGNORECASE)
63:         if REPO_NAME_REGEX.match(owner) and REPO_NAME_REGEX.match(repo):
64:             return owner, repo, f"{owner}/{repo}"
65: 
66:     return None
```
* **Lines 57–66**: Handles simple `owner/repo` strings and returns the sanitized components.

---

## 5. `backend/app/models/entities.py`

Defines the core relational database entities via SQLModel.

* **Lines 7–22**:
  - `get_utc_now()`: Utility returning current UTC datetime.
  - `RequirementType`: Enum (`REQUIRED`, `PREFERRED`, `BONUS`).
  - `AssessmentStatus`: Enum (`MET`, `PARTIAL`, `UNMET`, `NEEDS_REVIEW`).
* **Lines 24–38 (`Job`)**:
  - Contains `title`, `company`, `source_url`, `raw_text`, and `role_profile` (storing JSON seniority and skill depths).
  - Establishes one-to-many relationship with `Requirement`.
* **Lines 40–58 (`Requirement`)**:
  - Represents an extracted technical criterion with `title`, `category` (Languages, Frameworks, Architecture, Databases), `weight`, and `source_snippet` (exact sentence citation from job description).
  - Includes `aliases` (JSON array of synonyms) and relationships to `Job`, `Assessment`, and `AuditHistory`.
* **Lines 61–69 (`LearningResourceCache`)**:
  - Caches YouTube and web learning materials by `cache_key` (`normalized_skill:level`) with expiration timestamps.
* **Lines 71–84 (`Repository`)**:
  - Records connected GitHub repositories: `full_name` (`owner/repo`), `clone_url`, `default_branch`, and `latest_commit_sha`.
* **Lines 86–104 (`Assessment`)**:
  - Stores overall requirement evaluation outcome: `status`, `confidence_score` (0.0 to 1.0), `reason`, `llm_model` used, and `llm_raw_response`.
  - Links to `Requirement` and `Repository`, with a one-to-many relationship to `Citation`.
* **Lines 106–121 (`Citation`)**:
  - Stores concrete code evidence: `file_path`, `start_line`, `end_line`, `commit_sha`, `snippet_text`, and GitHub web URL.
* **Lines 123–134 (`AuditHistory`)**:
  - Audit trail of status transitions (e.g. from `UNMET` to `MET`) triggered by webhook push events.
* **Lines 136–148 (`WebhookEvent`)**:
  - Records GitHub push delivery IDs for idempotency/deduplication, sender login, commit SHA, and pipeline processing status.

