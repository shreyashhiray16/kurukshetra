# AI Career Coach (Kurukshetra)

Deterministic Skill Verification, Live Naukri Job Feed & Multi-Repository Assessment.

---

## Quickstart

### 1. Backend Setup (FastAPI + SQLModel)
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r ../requirements.txt
```

Run database initialization & schema migrations:
```bash
python -c "from app.core.db import init_db; init_db()"
```

Start the backend API server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation is accessible at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup (React 19 + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Verification & Automated Tests

Run backend unit and integration test suite:
```bash
cd backend
python -m pytest tests
```

Run Level 6 end-to-end verification (Naukri feed, role suggestions, deduplicated import, and multi-repo assessment):
```bash
cd backend
python verify_level6.py
```

Run frontend lint & build:
```bash
cd frontend
npm run lint
npm run build
```

---

## Configuration & Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `JOB_SOURCE` | `naukri` | Primary job feed provider (`naukri` or `fallback`) |
| `NAUKRI_BASE_URL` | `https://www.naukri.com` | Base URL for Naukri search endpoints |
| `NAUKRI_APP_ID` | `109` | Naukri application identifier header |
| `NAUKRI_SYSTEM_ID` | `109` | Naukri system identifier header |
| `JOB_SEARCH_CACHE_TTL` | `600` | In-memory search results cache duration in seconds |
| `JSEARCH_API_KEY` | `""` | Optional RapidAPI JSearch key for enhanced fallback feed |
| `GITHUB_TOKEN` | `""` | Optional GitHub personal access token for higher API rate limits |
| `GROQ_API_KEY` / `GEMINI_API_KEY` | `""` | LLM keys for requirement extraction and evaluations |
