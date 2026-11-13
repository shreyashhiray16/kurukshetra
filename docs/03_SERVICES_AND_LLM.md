# Deep Dive: Backend AI, Services & Domain Logic

This document details the core analytical engines, LLM integrations, GitHub scanners, scoring algorithms, and roadmap generation services located in `backend/app/services/`.

---

## 1. `backend/app/services/llm_provider.py` (147 lines)

Implements a unified, vendor-agnostic interface for Large Language Models.

### Key Logic & Flow:
- **Provider Abstraction**: Allows switching between Google Gemini and Groq API via configuration (`LLM_PROVIDER="auto" | "gemini" | "groq"`).
- **Fallback Chain**:
  - If the primary model fails or encounters rate limits (HTTP 429), it automatically iterates through secondary fallback models defined in `settings.GEMINI_FALLBACK_MODELS` and `settings.GROQ_FALLBACK_MODELS`.
- **Structured JSON Output**:
  - Enforces schema consistency by injecting system instructions demanding valid JSON output.
  - Sanitizes model output by stripping markdown code fences (` ```json ` ... ` ``` `) and extracting the innermost JSON payload.
  - Validates and deserializes into Python dictionaries, raising structured exceptions on malformed output.

---

## 2. `backend/app/services/gemini_service.py` (166 lines)

Low-level client wrapper for the Google GenAI SDK (`google-genai`).

### Key Capabilities:
- Initializes client using `settings.GEMINI_API_KEY`.
- Configures generation parameters:
  - `temperature`: Lower values (0.1–0.2) to maintain deterministic evaluation.
  - `response_mime_type`: Set to `application/json`.
- Wraps API calls in retry loops with exponential backoff for transient network issues.
- Logs token usage and model execution latency.

---

## 3. `backend/app/services/job_extractor.py` (136 lines)

Parses unstructured job descriptions into structured requirements.

### Workflow & Logic:
1. **Extraction Prompting**:
   - Instructs the LLM to identify explicit technical requirements and classify them into categories: `Languages`, `Frameworks`, `Databases`, `Cloud & DevOps`, `Architecture & System Design`, `Testing & Quality`, and `Tools`.
   - Assigns requirement types:
     - `required`: Mandatory qualifications ("must have", "5+ years", "essential").
     - `preferred`: Desired qualifications ("nice to have", "plus", "familiarity with").
     - `bonus`: Additional advantages.
   - Extracts exact `source_snippet` sentences from the original job posting as verifiable citations.
   - Generates technical synonyms and package aliases (e.g. `PostgreSQL` -> `["postgres", "psycopg2", "pg"]`).
2. **Deterministic Heuristic Fallback**:
   - If LLM services are offline or credentials are missing, triggers a regex and keyword extractor containing common technology keywords to ensure the application remains functional.

---

## 4. `backend/app/services/github_scanner.py` (249 lines)

Scans GitHub repositories, extracts dependency manifests, and analyzes code slices.

### Key Features:
- **Tree Exploration**:
  - Uses PyGithub to fetch Git trees recursively via Git Trees API (`recursive=1`).
  - Filters out binary files, images, locks, and dependency folders (`node_modules/`, `venv/`, `.git/`, `dist/`).
- **Manifest Parsing**:
  - Automatically identifies and reads package management files:
    - JavaScript/TypeScript: `package.json` (dependencies and devDependencies).
    - Python: `requirements.txt`, `Pipfile`, `pyproject.toml`.
    - Java/Kotlin: `pom.xml`, `build.gradle`.
    - Go: `go.mod`.
    - Rust: `Cargo.toml`.
- **Targeted Code Slicing**:
  - Identifies key architectural files (routes, controllers, models, configuration) and extracts line-numbered code snippets for evaluation.

---

## 5. `backend/app/services/assessment_engine.py` (515 lines)

The central evaluation engine that compares job requirements against repository evidence.

### Multi-Stage Evaluation Pipeline:
1. **Stage 1: Manifest Pre-filtering**:
   - Checks if a required technology appears directly in package manifests.
   - Example: If the job requires `Redis` and `redis` is listed in `package.json`, flags preliminary evidence.
2. **Stage 2: Static Code Pattern Search**:
   - Searches repository files for imports, function calls, class decorators, or configuration settings matching the requirement and its aliases.
   - Locates exact line numbers (`start_line` to `end_line`) where patterns occur.
3. **Stage 3: LLM Contextual Evaluation**:
   - Prompts the LLM with the candidate code snippets and requirement description.
   - Asks: Does this code demonstrate practical competence, or is it a trivial stub/boilerplate?
   - LLM returns:
     - `status`: `met`, `partial`, `unmet`, or `needs_review`.
     - `confidence_score`: 0.0 to 1.0.
     - `reason`: A concise explanation supporting the decision.
4. **Citation Assembly**:
   - Bundles matching code slices into `Citation` models with full repository URLs, commit SHAs, file paths, and line ranges.

---

## 6. `backend/app/services/readiness_calculator.py` (168 lines)

Computes normalized readiness scores (0–100%) using weighted algorithms.

### Mathematical Formulation:
Each requirement status is assigned a status multiplier:
- $\text{MET} = 1.0$
- $\text{PARTIAL} = 0.5$
- $\text{NEEDS\_REVIEW} = 0.25$
- $\text{UNMET} = 0.0$

Each requirement type has a baseline weight:
- $\text{REQUIRED} = 1.0$ (or custom weight $w_i \ge 1.0$)
- $\text{PREFERRED} = 0.6$
- $\text{BONUS} = 0.3$

The overall score is computed as:
$$\text{Readiness Score} = \left( \frac{\sum_{i=1}^{N} (\text{weight}_i \times \text{status\_multiplier}_i)}{\sum_{i=1}^{N} \text{weight}_i} \right) \times 100$$

Also computes category-level breakdowns (e.g., Databases: 80%, Architecture: 45%) to pinpoint exact candidate strengths and gaps.

---

## 7. `backend/app/services/roadmap_generator.py` (201 lines)

Generates structured learning roadmaps targeting unmet and partial skills.

### Key Logic:
- Analyzes missing skills and classifies them into a Directed Acyclic Graph (DAG) of sequential milestones:
  - **Phase 1: Foundations** (Syntax, core paradigms, language fundamentals).
  - **Phase 2: Core Implementation** (Frameworks, ORMs, RESTful API design, database schemas).
  - **Phase 3: Production Engineering** (Architecture, CI/CD, testing, caching, system design).
- Each milestone provides:
  - Milestone title and objective.
  - Practical hands-on task with suggested portfolio projects.
  - Direct links to curated learning materials.

---

## 8. `backend/app/services/resource_finder.py` (236 lines) & `resources_seed.json`

Discovers educational content for missing technical requirements.

### Search Strategy:
- **YouTube Data API v3**:
  - Searches for high-relevance video courses, crash courses, and tutorials for the specific skill.
  - Extracts title, channel name, video URL, thumbnail, and view counts.
- **Curated Catalog Fallback (`resources_seed.json`)**:
  - Comprehensive static database covering 100+ technologies.
  - Categorized into official documentation, books, and courses.
  - Ensures reliable recommendations even when running offline or without YouTube API credentials.

---

## 9. `backend/app/services/change_detector.py` (206 lines)

Implements continuous incremental assessment updates triggered by GitHub push webhooks.

### Incremental Diff Pipeline:
1. Parses the incoming GitHub push payload for modified and added file paths.
2. Identifies which requirements map to the changed files by checking file extensions, directory paths, and imported packages.
3. Selectively re-runs the assessment engine *only* for the affected requirements rather than re-evaluating the entire codebase.
4. Updates the `Assessment` records and writes an entry to `AuditHistory` documenting the status transition (e.g. from `UNMET` to `MET`) and triggering commit SHA.

