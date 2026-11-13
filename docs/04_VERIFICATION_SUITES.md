# Deep Dive: Backend Verification Suites

This document provides a breakdown of the automated test and verification scripts located in `backend/`. These scripts test the system across five architectural levels.

---

## 1. `backend/verify_level1.py` (114 lines)
**Objective**: Validates Core Database Architecture, Tables, Pragmas & Migrations.

### What it tests:
1. **Database Initialization**: Runs `init_db()` and confirms the SQLite file is created.
2. **SQLite Pragmas**: Verifies `journal_mode=WAL` and `busy_timeout=30000` to ensure concurrent write performance without table lockups.
3. **Table Existence**: Verifies that all SQLModel tables exist: `job`, `requirement`, `repository`, `assessment`, `citation`, `audithistory`, `webhookevent`, and `learningresourcecache`.
4. **Column Migration Check**: Tests that dynamic schema migration logic successfully adds missing columns (`llm_model`, `role_profile`, `aliases`) without data loss.
5. **CRUD Integrity**: Inserts sample jobs and requirements and confirms foreign key relationships.

---

## 2. `backend/verify_level2.py` (51 lines)
**Objective**: Validates Job Requirement Extraction & Repository Scanning.

### What it tests:
1. **Job Parsing**: Tests `job_extractor.extract_requirements()` with sample job text. Confirms requirement categorization, type assignments (`required`/`preferred`), and weight calculations.
2. **Repository Parser**: Runs unit tests against `repo_parser.parse_github_repo()` with edge-case strings (HTTPS URLs, SSH format, decorator strings, invalid inputs).
3. **Manifest Scanner**: Tests `github_scanner.py` using mock repository trees to ensure package manifests (`package.json`, `requirements.txt`) are accurately detected.

---

## 3. `backend/verify_level3.py` (38 lines)
**Objective**: Validates End-to-End Assessment Engine & Citation Generation.

### What it tests:
1. **Evaluation Pipeline**: Tests `assessment_engine.evaluate_repository()` against mock repository files.
2. **Citation Verification**: Verifies that generated citations include valid line number ranges (`start_line` to `end_line`), non-empty code snippets, and valid file paths.
3. **Readiness Calculation**: Tests `readiness_calculator.calculate_readiness_score()` against known evaluation states to verify mathematical scoring accuracy.

---

## 4. `backend/verify_level4.py` (93 lines)
**Objective**: Validates GitHub Webhook Security & Incremental Change Detection.

### What it tests:
1. **HMAC Signature Generation**: Computes valid HMAC-SHA256 signatures for a mock GitHub push payload using a test secret.
2. **Signature Rejection**: Sends invalid signatures and verifies HTTP 401 Unauthorized responses.
3. **Delivery Deduplication**: Submits identical `X-GitHub-Delivery` IDs and verifies that second attempts are recognized as duplicates and ignored.
4. **Incremental Diff Trigger**: Verifies that file modifications trigger targeted requirement re-evaluations and create records in `AuditHistory`.

---

## 5. `backend/verify_level5.py` (136 lines)
**Objective**: Validates Learning Roadmap Generation & Resource Discovery.

### What it tests:
1. **Roadmap Milestone Generation**: Verifies that `roadmap_generator.py` correctly converts unmet requirements into ordered milestones.
2. **Phase Sequencing**: Checks that foundational milestones precede advanced architecture tasks.
3. **Resource Finder Integration**: Tests `resource_finder.py` fallback to `resources_seed.json` when YouTube API keys are absent, ensuring valid documentation links are always returned.

---

## 6. `backend/verify_llm.py` (21 lines)
**Objective**: Direct Connectivity & JSON Schema Verification for LLM Providers.

### What it tests:
1. **LLM Handshake**: Sends a structured prompt to the configured LLM provider (`Gemini` or `Groq`).
2. **JSON Compliance**: Validates that the response parses cleanly into a valid JSON dictionary conforming to the required schema.
3. **Error Reporting**: Returns actionable troubleshooting instructions if an API key is invalid or quota limits are reached.

