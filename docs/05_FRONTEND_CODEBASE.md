# Deep Dive: Frontend Client Architecture & Implementation

This document covers all files in the frontend application (`frontend/src/`), detailing component logic, state management, PDF generation, and client-side utilities.

---

## 1. `frontend/src/App.jsx` (1,693 lines)

The central React component and application orchestrator.

### Core Architecture & State Management:
- **Application Views**:
  - `hero`: Landing screen with product value proposition and quick-start actions.
  - `job_input`: Dual-mode input screen (pasting raw text or fetching via remote URL). Includes quick pre-fill buttons for demo roles (Senior Full Stack, DevOps Engineer, Backend Engineer, AI/ML Specialist).
  - `repo_select`: GitHub repository connection screen using `RepoCombobox.jsx`.
  - `evaluating`: Real-time evaluation progress screen with step indicators (parsing job -> scanning repo -> evaluating code -> computing readiness).
  - `dashboard`: Primary results dashboard showing readiness gauge, category progress bars, and requirement breakdown cards.
  - `roadmap`: Interactive learning plan organized by milestone phases.
- **State Hooks**:
  - `job`: Active job description and extracted requirement data.
  - `repo`: Selected repository metadata, default branch, and commit hash.
  - `assessment`: Detailed evaluation results, requirement statuses, and code citations.
  - `roadmapData`: Sequential milestones and associated learning resources.
  - `filterCategory` / `filterStatus`: Interactive filters for sorting requirement cards.
- **Key Interactions**:
  - Seamless fallback to `demoData.js` when the backend is offline, enabling presentations and testing without live server dependencies.
  - Collapsible citation cards showing syntax-highlighted code evidence and line numbers.
  - Direct PDF export trigger calling `pdfGenerator.js`.

---

## 2. `frontend/src/components/RepoCombobox.jsx` (529 lines)

A search-enabled combobox component for repository selection.

### Key Features:
- **Interactive Autocomplete**:
  - Filters connected and suggested GitHub repositories in real time.
- **Keyboard Navigation**:
  - Full keyboard support: Arrow Up/Down to navigate items, Enter to select, Escape to dismiss dropdown.
- **Input Sanitization**:
  - Connects to `parseGithubRepo.js` to normalize repository inputs on every keystroke.
  - Displays validation feedback for invalid URLs.
- **Accessibility (a11y)**:
  - Adheres to ARIA combobox specifications with appropriate `aria-expanded`, `aria-activedescendant`, and `role="listbox"` attributes.

---

## 3. `frontend/src/utils/pdfGenerator.js` (479 lines)

Client-side PDF report generator.

### Design & Layout Features:
- **Document Header**:
  - Candidate and role title, target company, evaluation timestamp, and repository commit SHA.
- **Executive Summary & Visual Gauges**:
  - Draws readiness score dials and categorical bar charts directly onto the document canvas.
- **Detailed Requirement Matrix**:
  - Generates multi-column tables showing requirement title, category, weight, and status (`MET`, `PARTIAL`, `UNMET`).
- **Verifiable Code Citations**:
  - Renders code snippet blocks complete with relative file paths, line ranges, and explanation summaries.
- **Personalized Learning Action Plan**:
  - Appends the sequential milestone roadmap with curated links and project recommendations.

---

## 4. `frontend/src/utils/parseGithubRepo.js` (75 lines) & `parseGithubRepo.test.js`

Client-side GitHub repository identifier parser.

### Supported Input Formats:
- Standard web URLs: `https://github.com/owner/repo`
- SSH clone URLs: `git@github.com:owner/repo.git`
- URLs with subpaths or query parameters: `https://github.com/owner/repo/tree/main/src`
- Shorthand notations: `owner/repo`
- UI decorator strings: `owner/repo (main) - SHA: 8a3f12c`

The test file (`parseGithubRepo.test.js`) verifies all edge cases, valid formats, and malformed inputs to ensure consistent behavior across both frontend and backend.

---

## 5. `frontend/src/data/demoData.js` (374 lines) & `demoData.test.js`

Comprehensive offline demonstration dataset.

### Included Pre-configured Roles:
1. **Full-Stack Engineer** (React, Node.js, TypeScript, PostgreSQL, Docker, AWS).
2. **Backend / Platform Engineer** (Python, FastAPI, Redis, Distributed Systems, CI/CD).
3. **DevOps & Cloud Engineer** (Kubernetes, Terraform, GitHub Actions, Prometheus).
4. **AI & Machine Learning Engineer** (PyTorch, LLMs, Vector Databases, Retrieval-Augmented Generation).

Includes full mock assessment results, citations, and roadmaps to allow exploration of all UI views without requiring live API keys or backend servers.

---

## 6. Styling: `App.css` (158 lines) & `index.css` (192 lines)

Implements the application styling system.

- Responsive layouts using CSS grid and flexbox.
- Modern dark/light theme CSS custom properties.
- Glassmorphic card styling with subtle drop shadows and border highlights.
- Status badges:
  - `MET`: Emerald green palette.
  - `PARTIAL`: Amber/gold palette.
  - `UNMET`: Rose/red palette.
  - `NEEDS_REVIEW`: Blue palette.
- Smooth transitions for tab switches, collapsible citation cards, and progress meters.

