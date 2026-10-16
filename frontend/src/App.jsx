import React, { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { 
  Briefcase, 
  GitBranch, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  ExternalLink, 
  RefreshCw, 
  Upload, 
  Terminal, 
  ShieldCheck, 
  Zap,
  TrendingUp,
  FileCode,
  Layers,
  ChevronRight,
  Code,
  Key,
  Sparkles,
  Globe,
  Loader2,
  Trash2,
  Plus
} from 'lucide-react';

import RepoCombobox from './components/RepoCombobox.jsx';

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [repos, setRepos] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [isRepoValid, setIsRepoValid] = useState(true);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [events, setEvents] = useState([]);
  const [history, setHistory] = useState([]);
  const [llmTest, setLlmTest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [multiRepoInput, setMultiRepoInput] = useState("");
  const [multiRepoLoading, setMultiRepoLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const page = ({
    '/': 'dashboard',
    '/jobs': 'jobs',
    '/repos': 'repos',
    '/gap': 'gap',
    '/evidence': 'evidence',
    '/history': 'history',
    '/settings': 'settings',
  })[location.pathname] || 'dashboard';
  const [error, setError] = useState(null);

  // Gemini state
  const [geminiConfigured, setGeminiConfigured] = useState(false);
  const [maskedKey, setMaskedKey] = useState(null);
  const [inputGeminiKey, setInputGeminiKey] = useState("");

  // Form states
  const [rawJobText, setRawJobText] = useState(`Job Title: Staff Full-Stack AI Engineer
Company: Apex Innovations
Responsibilities:
- Build and scale high throughput REST APIs using FastAPI and Python.
- Architect schema migrations and relational storage in PostgreSQL.
- Package container images with Docker and orchestrate workloads.
- Write robust integration test suites and CI pipelines.`);
  const [sourceUrl, setSourceUrl] = useState("https://example.com/careers/staff-ai-engineer");
  const [fetchingUrl, setFetchingUrl] = useState(false);
  const [newRepoFullName, setNewRepoFullName] = useState("tiangolo/fastapi");

  const [feedback, setFeedback] = useState(null); // { type: 'success' | 'error', message: string }

  async function handleFetchJobFromUrl(e) {
    if (e && e.preventDefault) e.preventDefault();
    const url = (sourceUrl || '').trim();
    if (!url || (!url.startsWith('http://') && !url.startsWith('https://'))) {
      setFeedback({ type: 'error', message: "Please enter a valid HTTP or HTTPS job URL (e.g. from Greenhouse, Lever, Workday, LinkedIn, or any company careers page)." });
      return;
    }

    try {
      setFetchingUrl(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/jobs/fetch-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, summarize: true })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to fetch job content from URL.");
      }

      if (data.raw_text) {
        setRawJobText(data.raw_text);
        const titleStr = data.title ? ` "${data.title}"` : '';
        const companyStr = data.company ? ` at ${data.company}` : '';
        const summaryBadge = data.summarized ? ` (Cleaned & Summarized by Groq ${data.summary_model || ''})` : '';
        setFeedback({ 
          type: 'success', 
          message: `Fetched job description${titleStr}${companyStr}${summaryBadge} via ${data.strategy} (${data.raw_text.length} chars). Only important necessary requirements are displayed below.` 
        });
      } else {
        throw new Error("No readable job text could be found at this URL.");
      }
    } catch (err) {
      setFeedback({ type: 'error', message: `URL Fetch failed: ${err.message}` });
    } finally {
      setFetchingUrl(false);
    }
  }

  useEffect(() => {
    loadInitialData();
    checkGeminiConfig();
  }, []);

  async function checkGeminiConfig() {
    try {
      const res = await fetch(`${API_BASE}/config`).then(r => r.json());
      setGeminiConfigured(res.gemini_configured);
      setMaskedKey(res.masked_key);
    } catch (e) {
      console.warn("Could not check Gemini config:", e);
    }
  }

  async function handleSaveGeminiKey(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!inputGeminiKey.trim()) {
      setFeedback({ type: 'error', message: "Please provide a valid Gemini API Key." });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/config/gemini-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gemini_api_key: inputGeminiKey.trim() })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update Gemini API Key");
      setFeedback({ type: 'success', message: "Gemini API Key configured successfully! Assessments will now use Gemini LLM." });
      setInputGeminiKey("");
      checkGeminiConfig();
    } catch (err) {
      setFeedback({ type: 'error', message: `Error setting Gemini key: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }

  async function loadInitialData() {
    try {
      setLoading(true);
      setError(null);
      const [jobsRes, reposRes, eventsRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/jobs/`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/repos/`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/webhooks/events`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/assessments/history`).then(r => r.json()).catch(() => []),
      ]);

      setJobs(Array.isArray(jobsRes) ? jobsRes : []);
      setRepos(Array.isArray(reposRes) ? reposRes : []);
      setEvents(Array.isArray(eventsRes) ? eventsRes : []);
      setHistory(Array.isArray(historyRes) ? historyRes : []);

      if (jobsRes.length > 0) setSelectedJob(jobsRes[0]);
      if (reposRes.length > 0) setSelectedRepo(reposRes[0]);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch initial backend state. Ensure FastAPI server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  async function handleConnectRepo(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!newRepoFullName.trim()) {
      setFeedback({ type: 'error', message: "Please provide a valid repository name in 'owner/repo' format or full GitHub URL." });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/repos/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: newRepoFullName.trim() })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || await res.text());
      }
      const data = await res.json();
      setRepos(prev => [data, ...prev.filter(r => r.id !== data.id)]);
      setSelectedRepo(data);
      setNewRepoFullName("");
      setFeedback({ type: 'success', message: `Repository connected: ${data.full_name} (${data.default_branch}) - SHA: ${data.latest_commit_sha ? data.latest_commit_sha.slice(0, 8) : 'HEAD'}` });
    } catch (err) {
      setFeedback({ type: 'error', message: `Error connecting repository: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleConnectMultiRepos(e) {
    if (e && e.preventDefault) e.preventDefault();
    const raw = (multiRepoInput || "").trim();
    if (!raw) {
      setFeedback({ type: 'error', message: "Please enter at least one GitHub repository link or owner/repo format." });
      return;
    }
    try {
      setMultiRepoLoading(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/repos/connect-multi`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: raw })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to batch connect repositories.");
      }
      const connectedList = await res.json();
      if (!connectedList || connectedList.length === 0) {
        throw new Error("No valid GitHub repositories found in the input. Please enter valid URLs or owner/repo strings.");
      }
      // Update repos
      setRepos(prev => {
        const ids = new Set(connectedList.map(c => c.id));
        return [...connectedList, ...prev.filter(r => !ids.has(r.id))];
      });
      setSelectedRepo(connectedList[0]);
      setMultiRepoInput("");
      setFeedback({
        type: 'success',
        message: `Successfully connected ${connectedList.length} repositories! Selected "${connectedList[0].full_name}" for evaluation.`
      });
    } catch (err) {
      setFeedback({ type: 'error', message: `Multi-Repo connection error: ${err.message}` });
    } finally {
      setMultiRepoLoading(false);
    }
  }

  async function handleDeleteRepo(repoId) {
    if (!window.confirm("Are you sure you want to remove this connected repository?")) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/repos/${repoId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete repository.");
      setRepos(prev => {
        const next = prev.filter(r => r.id !== repoId);
        if (selectedRepo && selectedRepo.id === repoId) {
          setSelectedRepo(next[0] || null);
        }
        return next;
      });
      setFeedback({ type: 'success', message: "Repository removed." });
    } catch (err) {
      setFeedback({ type: 'error', message: `Delete failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleImportJob(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!rawJobText.trim()) {
      setFeedback({ type: 'error', message: "Please enter or paste job description text." });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/jobs/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: rawJobText.trim(), source_url: sourceUrl.trim() || undefined })
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText);
      }
      const data = await res.json();
      setJobs(prev => [data, ...prev.filter(j => j.id !== data.id)]);
      setSelectedJob(data);
      setFeedback({ type: 'success', message: `Job parsed by ${data.llm_model || data.extraction_source || 'extractor'}. Extracted ${data.requirements?.length || 0} requirements.` });
      // Switch back to assessment tab so user immediately sees imported job selected
      navigate('/jobs');
    } catch (err) {
      setFeedback({ type: 'error', message: `Error parsing job requirements: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleRunAssessment() {
    if (!selectedJob || !selectedRepo) {
      setFeedback({ type: 'error', message: "Please select both a Target Job and a Connected Repository from the dropdowns above." });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/assessments/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: selectedJob.id, repo_id: selectedRepo.id })
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText);
      }
      const data = await res.json();
      setAssessmentResult(data);
      setFeedback({ type: 'success', message: `Assessment complete: ${data.summary?.overall_match_percentage}% Match (${data.summary?.met} Met, ${data.summary?.partial} Partial, ${data.summary?.unmet} Unmet, ${data.summary?.needs_review || 0} Needs Review)` });
    } catch (err) {
      setFeedback({ type: 'error', message: `Assessment failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleTriggerPoll() {
    if (!selectedRepo) {
      setFeedback({ type: 'error', message: "Please select a repository to poll." });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setFeedback(null);
      const res = await fetch(`${API_BASE}/webhooks/poll/${selectedRepo.id}`, { method: "POST" });
      const data = await res.json();
      setFeedback({ type: 'success', message: `Polled repository '${selectedRepo.full_name}': ${data.message || (data.changed ? 'New commits detected & reassessed' : 'Already at latest commit')}` });
      loadInitialData();
    } catch (err) {
      setFeedback({ type: 'error', message: `Polling check failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <header style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '14px 32px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 38,
              height: 38,
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, #e11d48, #be123c)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(225, 29, 72, 0.35)'
            }}>
              <Zap size={22} color="#fff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.2rem', lineHeight: 1.2 }}>AI Career Coach</h1>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Deterministic Skill Verification & Gap Analysis</p>
            </div>
          </div>

          <nav style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
            <NavLink to="/" end className="nav-link"><Layers size={15} /> Dashboard</NavLink>
            <NavLink to="/jobs" className="nav-link"><Briefcase size={15} /> Jobs</NavLink>
            <NavLink to="/repos" className="nav-link"><GitBranch size={15} /> Repositories</NavLink>
            <NavLink to="/gap" className="nav-link"><TrendingUp size={15} /> Skill Gap</NavLink>
            <NavLink to="/evidence" className="nav-link"><FileCode size={15} /> Evidence</NavLink>
            <NavLink to="/history" className="nav-link"><Terminal size={15} /> History</NavLink>
            <NavLink to="/settings" className="nav-link"><Sparkles size={15} /> Settings {geminiConfigured ? "✓" : ""}</NavLink>
            <button id="refresh-btn" onClick={() => { loadInitialData(); checkGeminiConfig(); }} className="btn btn-secondary" title="Refresh Data">
              <RefreshCw size={16} className={loading ? "pulse" : ""} />
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '28px 32px', width: '100%', flex: 1 }}>
        
        {/* Selection Bar */}
        <section className="glass-panel" style={{ padding: '18px 24px', marginBottom: 28, display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 260 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 700 }}>
              1. Target Job Profile
            </label>
            <select 
              id="select-job"
              value={selectedJob ? selectedJob.id : ''} 
              onChange={e => setSelectedJob(jobs.find(j => j.id === parseInt(e.target.value)))}
              style={{
                width: '100%',
                padding: '9px 12px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-main)',
                fontFamily: 'inherit',
                fontSize: '0.9rem'
              }}
            >
              {jobs.map(j => (
                <option key={j.id} value={j.id}>
                  #{j.id} - {j.title} ({j.company || 'Direct Posting'})
                </option>
              ))}
              {jobs.length === 0 && <option value="">No jobs imported yet</option>}
            </select>
          </div>

          <div style={{ flex: 1, minWidth: 260 }}>
            <label htmlFor="select-repo-combobox" style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 700 }}>
              2. Connected GitHub Repository
            </label>
            <RepoCombobox
              repos={repos}
              selectedRepo={selectedRepo}
              onChange={repo => setSelectedRepo(repo)}
              onValidationChange={isValid => setIsRepoValid(isValid)}
              apiBase={API_BASE}
            />
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', paddingTop: 18 }}>
            <button 
              id="run-assessment-btn"
              onClick={handleRunAssessment}
              disabled={loading || !selectedJob || !selectedRepo || !isRepoValid}
              className="btn btn-primary"
            >
              <Zap size={16} /> Run Full Assessment
            </button>
            <button 
              id="poll-repo-btn"
              onClick={handleTriggerPoll}
              disabled={loading || !selectedRepo || !isRepoValid}
              className="btn btn-secondary"
              title="Poll GitHub for latest commit changes"
            >
              <RefreshCw size={15} /> Poll Repo
            </button>
          </div>
        </section>

        {feedback && (
          <div style={{
            background: feedback.type === 'success' ? 'var(--status-met-bg)' : 'var(--status-unmet-bg)',
            border: `1px solid ${feedback.type === 'success' ? 'var(--status-met-border)' : 'var(--status-unmet-border)'}`,
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            marginBottom: 24,
            color: feedback.type === 'success' ? 'var(--status-met)' : 'var(--status-unmet)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 500 }}>
              {feedback.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
              <span>{feedback.message}</span>
            </div>
            <button 
              onClick={() => setFeedback(null)} 
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 700 }}
            >
              ✕
            </button>
          </div>
        )}

        {error && (
          <div style={{
            background: 'var(--status-unmet-bg)',
            border: '1px solid var(--status-unmet-border)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            marginBottom: 24,
            color: 'var(--status-unmet)',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* TAB 1: ASSESSMENT & GAP ANALYSIS */}
        {page === 'dashboard' && (
          <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 18 }}>
            {[
              ['Jobs imported', jobs.length],
              ['Repositories', repos.length],
              ['Webhook events', events.length],
              ['Status changes', history.length],
            ].map(([label, value]) => (
              <div key={label} className="glass-panel" style={{ padding: 22 }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{label}</div>
                <div style={{ fontSize: '2.2rem', fontWeight: 800 }}>{value}</div>
              </div>
            ))}
            <div className="glass-panel" style={{ padding: 22, gridColumn: '1 / -1' }}>
              <h2 style={{ fontSize: '1.1rem', marginBottom: 8 }}>Latest assessment</h2>
              {assessmentResult ? (
                <p>{assessmentResult.job_title} against {assessmentResult.repo_full_name}: {assessmentResult.summary?.overall_match_percentage}% match. {assessmentResult.skill_assessments?.filter(s => s.llm_used).length || 0} skills decided by Gemini.</p>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>No assessment yet. Import a job, connect a repository, then open Skill Gap.</p>
              )}
              <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                <button className="btn btn-primary" onClick={() => navigate('/gap')}><Zap size={15} /> Skill Gap</button>
                <button className="btn btn-secondary" onClick={() => navigate('/settings')}><Sparkles size={15} /> Gemini settings</button>
              </div>
            </div>
          </div>
        )}

        {page === 'gap' && (
          <div className="animate-fade-in">
            {assessmentResult ? (
              <div>
                {/* Summary Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 18, marginBottom: 28 }}>
                  <div className="glass-panel" style={{ padding: '20px 24px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
                      Match Score
                    </div>
                    <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
                      {assessmentResult.summary?.overall_match_percentage}%
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 4 }}>
                      Weighted: {assessmentResult.summary?.weighted_score} pts
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '20px 24px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
                      Demonstrated (Met)
                    </div>
                    <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--status-met)' }}>
                      {assessmentResult.summary?.met}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 4 }}>
                      Verified in executable code
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '20px 24px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
                      Partial Skills
                    </div>
                    <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--status-partial)' }}>
                      {assessmentResult.summary?.partial}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 4 }}>
                      Manifest / shallow references
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '20px 24px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
                      Gaps (Unmet)
                    </div>
                    <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--status-unmet)' }}>
                      {assessmentResult.summary?.unmet}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 4 }}>
                      Target areas for project work
                    </div>
                  </div>
                </div>

                {/* Skill Assessments List */}
                <h2 style={{ fontSize: '1.25rem', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Layers size={20} color="var(--accent-primary)" /> Skill Breakdown & Verified Citations
                </h2>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {assessmentResult.skill_assessments?.map(skill => {
                    const isMet = skill.status === 'met';
                    const isPartial = skill.status === 'partial';
                    const isUnmet = skill.status === 'unmet';

                    return (
                      <div 
                        key={skill.requirement_id} 
                        className="glass-panel" 
                        style={{ 
                          padding: 22,
                          borderLeft: `4px solid ${isMet ? 'var(--status-met)' : isPartial ? 'var(--status-partial)' : 'var(--status-unmet)'}`
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12, marginBottom: 12 }}>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                              <h3 style={{ fontSize: '1.1rem' }}>{skill.requirement_title}</h3>
                              <span className="badge badge-cyan">{skill.category}</span>
                              <span className={`badge ${isMet ? 'badge-met' : isPartial ? 'badge-partial' : 'badge-unmet'}`}>
                                {isMet && <CheckCircle2 size={13} />}
                                {isPartial && <AlertCircle size={13} />}
                                {isUnmet && <XCircle size={13} />}
                                {skill.status === 'needs_review' && <AlertCircle size={13} />}
                                {skill.status.replace('_', ' ')}
                              </span>
                              <span className={`badge ${skill.llm_used ? 'badge-cyan' : 'badge-partial'}`} title={skill.llm_used ? 'Verdict produced by a real Gemini response' : 'LLM unavailable: deterministic fallback rules used'}>
                                <Sparkles size={12} /> {skill.llm_used ? (skill.llm_model || 'Gemini') : 'rule-based fallback'}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                              Job Excerpt: "{skill.source_snippet}"
                            </div>
                          </div>

                          <div style={{ textAlign: 'right' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'block' }}>Weight: {skill.weight}x</span>
                            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: isMet ? 'var(--status-met)' : isPartial ? 'var(--status-partial)' : 'var(--text-muted)' }}>
                              Confidence: {Math.round(skill.confidence_score * 100)}%
                            </span>
                          </div>
                        </div>

                        <p style={{ fontSize: '0.92rem', color: 'var(--text-main)', marginBottom: 14 }}>
                          {skill.reason}
                        </p>

                        {/* Citations section */}
                        {skill.citations && skill.citations.length > 0 && (
                          <div style={{ marginTop: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: 14, border: '1px solid var(--border-subtle)' }}>
                            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              <Code size={14} /> Deterministic Code Citations ({skill.citations.length})
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {skill.citations.map((c, idx) => (
                                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <FileCode size={16} color="var(--accent-primary)" />
                                    <span className="mono" style={{ fontSize: '0.85rem' }}>
                                      {c.file_path}<span style={{ color: '#d97706', fontWeight: 600 }}>#L{c.start_line}-L{c.end_line}</span>
                                    </span>
                                  </div>
                                  <a 
                                    href={c.github_url} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none', fontSize: '0.8rem', fontWeight: 600 }}
                                  >
                                    View on GitHub <ExternalLink size={13} />
                                  </a>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Next Step / Action Plan */}
                        {skill.next_step && (
                          <div style={{
                            marginTop: 14,
                            padding: '10px 14px',
                            background: '#fff1f2',
                            borderLeft: '3px solid var(--accent-primary)',
                            borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                            fontSize: '0.88rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10
                          }}>
                            <Zap size={16} color="var(--accent-primary)" />
                            <span><strong>Actionable Next Step:</strong> {skill.next_step}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="glass-panel" style={{ padding: 48, textAlign: 'center' }}>
                <Briefcase size={44} color="var(--accent-primary)" style={{ margin: '0 auto 16px auto', display: 'block' }} />
                <h3 style={{ fontSize: '1.25rem', marginBottom: 8 }}>Ready for Skill Verification</h3>
                <p style={{ color: 'var(--text-muted)', maxWidth: 500, margin: '0 auto 20px auto', fontSize: '0.92rem' }}>
                  Select your target Job and connected Repository above, then click <strong>"Run Full Assessment"</strong> to run deterministic citation extraction and gap analysis.
                </p>
                <button onClick={handleRunAssessment} className="btn btn-primary">
                  <Zap size={16} /> Run Assessment Now
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: IMPORT FORM */}
        {page === 'jobs' && (
          <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 24 }}>
            {/* Import Job */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Briefcase size={20} color="var(--accent-primary)" /> Import New Job Description
              </h3>
              <form onSubmit={handleImportJob}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      Job Source URL (Any Company Careers / ATS URL)
                    </label>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      Supports Greenhouse, Lever, Workday, LinkedIn & any careers page
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input 
                      id="job-source-url-input"
                      type="url" 
                      placeholder="e.g. https://jobs.lever.co/spotify/... or https://job-boards.greenhouse.io/stripe/jobs/..."
                      value={sourceUrl} 
                      onChange={e => setSourceUrl(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleFetchJobFromUrl();
                        }
                      }}
                      style={{
                        flex: 1,
                        padding: '9px 12px',
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--text-main)',
                        fontSize: '0.9rem'
                      }}
                    />
                    <button
                      id="fetch-job-url-btn"
                      type="button"
                      onClick={handleFetchJobFromUrl}
                      disabled={fetchingUrl || loading || !sourceUrl.trim()}
                      className="btn"
                      style={{
                        background: 'var(--accent-primary)',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        whiteSpace: 'nowrap',
                        padding: '0 16px',
                        fontWeight: 600
                      }}
                      title="Fetch complete job description text directly from this URL"
                    >
                      {fetchingUrl ? (
                        <>
                          <Loader2 size={15} className="spin" /> Fetching...
                        </>
                      ) : (
                        <>
                          <Globe size={15} /> Fetch from URL
                        </>
                      )}
                    </button>
                  </div>
                </div>
                <div style={{ marginBottom: 18 }}>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                    Raw Job Description Text
                  </label>
                  <textarea 
                    id="job-raw-text-input"
                    rows={8}
                    value={rawJobText} 
                    onChange={e => setRawJobText(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-main)',
                      fontSize: '0.9rem',
                      fontFamily: 'inherit',
                      resize: 'vertical'
                    }}
                  />
                </div>
                <button id="submit-import-job-btn" type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%' }}>
                  <Upload size={16} /> Parse & Extract Structured Requirements
                </button>
              </form>
            </div>

            {/* Connect Repository */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <GitBranch size={20} color="var(--accent-primary)" /> Connect GitHub Repository
              </h3>

              {/* Single Repo Quick Connect */}
              <form onSubmit={handleConnectRepo} style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                  Quick Connect (owner/repo or GitHub URL)
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input 
                    id="repo-name-input"
                    type="text" 
                    placeholder="e.g. tiangolo/fastapi or https://github.com/..."
                    value={newRepoFullName} 
                    onChange={e => setNewRepoFullName(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '9px 12px',
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-main)',
                      fontSize: '0.9rem'
                    }}
                  />
                  <button id="submit-connect-repo-btn" type="submit" disabled={loading || !newRepoFullName.trim()} className="btn btn-primary" style={{ whiteSpace: 'nowrap' }}>
                    <ShieldCheck size={16} /> Connect & Scan
                  </button>
                </div>
              </form>

              {/* Multiple Repositories Batch Connect */}
              <div style={{ background: 'rgba(225, 29, 72, 0.03)', border: '1px dashed var(--accent-primary)', borderRadius: 'var(--radius-md)', padding: 16, marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, fontWeight: 600, fontSize: '0.9rem' }}>
                  <Plus size={16} color="var(--accent-primary)" /> Add Multiple GitHub Repositories
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 10 }}>
                  Paste multiple repository links or names separated by commas or new lines. We will scan all of them:
                </p>
                <textarea
                  id="multi-repo-input"
                  rows={3}
                  placeholder={`https://github.com/user/portfolio-api\nhttps://github.com/user/machine-learning\noctocat/Hello-World`}
                  value={multiRepoInput}
                  onChange={e => setMultiRepoInput(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-main)',
                    fontSize: '0.85rem',
                    fontFamily: 'inherit',
                    marginBottom: 10
                  }}
                />
                <button
                  id="submit-multi-repo-btn"
                  type="button"
                  onClick={handleConnectMultiRepos}
                  disabled={multiRepoLoading || !multiRepoInput.trim()}
                  className="btn"
                  style={{
                    background: 'var(--accent-primary)',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: '0.85rem',
                    fontWeight: 600
                  }}
                >
                  {multiRepoLoading ? <Loader2 size={15} className="spin" /> : <ShieldCheck size={15} />}
                  Connect All Repositories
                </button>
              </div>

              <h4 style={{ fontSize: '0.9rem', marginBottom: 10, color: 'var(--text-muted)' }}>Connected Repositories ({repos.length})</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 320, overflowY: 'auto' }}>
                {repos.map(r => (
                  <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {r.full_name}
                        {selectedRepo?.id === r.id && <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>Selected</span>}
                      </div>
                      <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                        Branch: {r.default_branch || 'main'} · SHA: {r.latest_commit_sha ? r.latest_commit_sha.slice(0, 10) : 'HEAD'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <button
                        type="button"
                        onClick={() => { setSelectedRepo(r); navigate('/'); }}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                      >
                        Assess
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteRepo(r.id)}
                        className="btn"
                        title="Remove repository"
                        style={{ background: 'transparent', color: 'var(--text-muted)', border: 'none', padding: '6px', cursor: 'pointer' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
                {repos.length === 0 && (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: 12, textAlign: 'center' }}>
                    No repositories connected yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: REPOSITORIES VIEW */}
        {page === 'repos' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="glass-panel" style={{ padding: 24, maxWidth: 840 }}>
              <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <GitBranch size={20} color="var(--accent-primary)" /> Connect Multiple GitHub Repositories
              </h3>

              <div style={{ marginBottom: 18 }}>
                <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                  Repository Links / Names (Insert single or multiple links)
                </label>
                <textarea
                  id="tab-multi-repo-input"
                  rows={4}
                  placeholder={`https://github.com/tiangolo/fastapi\nhttps://github.com/pallets/flask\noctocat/Hello-World`}
                  value={multiRepoInput}
                  onChange={e => setMultiRepoInput(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: 12,
                    fontSize: '0.9rem',
                    fontFamily: 'inherit'
                  }}
                />
                <button
                  id="submit-tab-multi-repo-btn"
                  type="button"
                  onClick={handleConnectMultiRepos}
                  disabled={multiRepoLoading || !multiRepoInput.trim()}
                  className="btn btn-primary"
                >
                  {multiRepoLoading ? <Loader2 size={16} className="spin" /> : <ShieldCheck size={16} />}
                  Connect & Scan Repositories
                </button>
              </div>

              <h4 style={{ fontSize: '0.95rem', margin: '20px 0 10px', color: 'var(--text-muted)' }}>
                Active Connected Repositories ({repos.length})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {repos.map(r => (
                  <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
                    <div>
                      <strong style={{ fontSize: '0.95rem' }}>{r.full_name}</strong>
                      <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: 2 }}>
                        Branch: {r.default_branch || 'main'} · Commit: {r.latest_commit_sha ? r.latest_commit_sha.slice(0, 10) : 'HEAD'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <button
                        type="button"
                        onClick={() => { setSelectedRepo(r); navigate('/'); }}
                        className="btn btn-primary"
                        style={{ padding: '6px 12px', fontSize: '0.82rem' }}
                      >
                        Select & Assess
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteRepo(r.id)}
                        className="btn"
                        title="Remove repository"
                        style={{ background: 'transparent', color: 'var(--status-unmet)', border: 'none', padding: '6px', cursor: 'pointer' }}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {page === 'evidence' && (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <h2 style={{ fontSize: '1.2rem' }}>Evidence Explorer</h2>
            {(assessmentResult?.skill_assessments || []).flatMap(skill => (skill.citations || []).map((c, i) => ({ skill, c, i }))).map(({ skill, c, i }) => (
              <div key={`${skill.requirement_id}-${i}`} className="glass-panel" style={{ padding: 18 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 8 }}>
                  <strong>{skill.requirement_title}</strong>
                  <a href={c.github_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)', fontSize: '0.82rem' }}>{c.file_path}#L{c.start_line}-L{c.end_line}</a>
                </div>
                <pre className="mono" style={{ whiteSpace: 'pre-wrap', background: '#0f172a', color: '#e2e8f0', padding: 12, borderRadius: 8, fontSize: '0.8rem' }}>{c.snippet_text}</pre>
                <div style={{ marginTop: 8, fontSize: '0.8rem', color: 'var(--text-dim)' }}>Commit {c.commit_sha?.slice(0, 10)} · validated against file content</div>
              </div>
            ))}
            {!(assessmentResult?.skill_assessments || []).some(s => s.citations?.length) && (
              <div className="glass-panel" style={{ padding: 32, color: 'var(--text-muted)' }}>Run a skill-gap assessment to see cited excerpts.</div>
            )}
          </div>
        )}

        {page === 'history' && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Terminal size={20} color="var(--accent-primary)" /> GitHub Webhook Deliveries & Audit Trail
              </h2>
              <button onClick={loadInitialData} className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                <RefreshCw size={14} /> Refresh Log
              </button>
            </div>

            <div className="glass-panel" style={{ overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '12px 18px' }}>Delivery ID</th>
                    <th style={{ padding: '12px 18px' }}>Repository</th>
                    <th style={{ padding: '12px 18px' }}>Event</th>
                    <th style={{ padding: '12px 18px' }}>Commit SHA</th>
                    <th style={{ padding: '12px 18px' }}>Status</th>
                    <th style={{ padding: '12px 18px' }}>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((ev, i) => (
                    <tr key={ev.id || i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td className="mono" style={{ padding: '12px 18px', color: 'var(--accent-primary)', fontWeight: 600 }}>
                        {ev.delivery_id}
                      </td>
                      <td style={{ padding: '12px 18px', fontWeight: 600 }}>
                        {ev.repository_full_name}
                      </td>
                      <td style={{ padding: '12px 18px' }}>
                        <span className="badge badge-cyan">{ev.event_type}</span>
                      </td>
                      <td className="mono" style={{ padding: '12px 18px', color: 'var(--text-dim)' }}>
                        {ev.commit_sha ? ev.commit_sha.slice(0, 8) : '—'}
                      </td>
                      <td style={{ padding: '12px 18px' }}>
                        <span className={`badge ${ev.status === 'completed' ? 'badge-met' : ev.status === 'processing' ? 'badge-partial' : 'badge-unmet'}`}>
                          {ev.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 18px', color: 'var(--text-dim)', fontSize: '0.82rem' }}>
                        {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : 'Just now'}
                      </td>
                    </tr>
                  ))}
                  {events.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--text-dim)' }}>
                        No webhook delivery events recorded yet. Deliveries will appear here as commits are pushed.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <h3 style={{ margin: '22px 0 10px' }}>Skill status changes</h3>
            <div className="glass-panel" style={{ overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', color: 'var(--text-muted)' }}>
                    <th style={{ padding: 12, textAlign: 'left' }}>Requirement</th>
                    <th style={{ padding: 12, textAlign: 'left' }}>From</th>
                    <th style={{ padding: 12, textAlign: 'left' }}>To</th>
                    <th style={{ padding: 12, textAlign: 'left' }}>Trigger</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(h => (
                    <tr key={h.id} style={{ borderTop: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: 12 }}>#{h.requirement_id}</td>
                      <td style={{ padding: 12 }}>{h.previous_status || '—'}</td>
                      <td style={{ padding: 12 }}>{h.new_status}</td>
                      <td style={{ padding: 12 }}>{h.trigger_event}</td>
                    </tr>
                  ))}
                  {history.length === 0 && <tr><td colSpan={4} style={{ padding: 24, color: 'var(--text-dim)' }}>No status transitions yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: GEMINI AI CONFIGURATION */}
        {page === 'settings' && (
          <div className="animate-fade-in" style={{ maxWidth: 800, margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: 32 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 'var(--radius-md)',
                  background: 'linear-gradient(135deg, #e11d48, #be123c)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 14px rgba(225, 29, 72, 0.3)'
                }}>
                  <Sparkles size={24} color="#fff" />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.3rem' }}>Gemini LLM Assessment Engine</h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Skill verdicts come from a live Google model response. Gemini Flash is tried first; Gemma is used when Flash is over quota.
                  </p>
                </div>
              </div>

              {/* Status Indicator */}
              <div style={{
                background: geminiConfigured ? 'var(--status-met-bg)' : 'var(--status-partial-bg)',
                border: `1px solid ${geminiConfigured ? 'var(--status-met-border)' : 'var(--status-partial-border)'}`,
                borderRadius: 'var(--radius-md)',
                padding: '16px 20px',
                marginBottom: 24,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: geminiConfigured ? 'var(--status-met)' : 'var(--status-partial)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    {geminiConfigured ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                    {geminiConfigured ? "Gemini LLM Active & Connected" : "Gemini API Key Required"}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginTop: 4 }}>
                    {geminiConfigured 
                      ? `Key configured (${maskedKey}). All skill assessments will be decided by Gemini model.`
                      : "Currently falling back to deterministic line-range rules until key is supplied."
                    }
                  </div>
                </div>
                <span className={`badge ${geminiConfigured ? 'badge-met' : 'badge-partial'}`}>
                  {geminiConfigured ? "Live LLM Mode" : "Fallback Mode"}
                </span>
              </div>

              {/* API Key Form */}
              <form onSubmit={handleSaveGeminiKey}>
                <div style={{ marginBottom: 20 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 8 }}>
                    Enter Gemini API Key
                  </label>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <div style={{ position: 'relative', flex: 1 }}>
                      <input 
                        id="gemini-api-key-input"
                        type="password"
                        placeholder={geminiConfigured ? "Enter new key to update..." : "AIzaSy..."}
                        value={inputGeminiKey}
                        onChange={e => setInputGeminiKey(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '11px 14px',
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          color: 'var(--text-main)',
                          fontSize: '0.95rem',
                          fontFamily: 'monospace'
                        }}
                      />
                    </div>
                    <button 
                      id="save-gemini-key-btn"
                      type="submit" 
                      disabled={loading || !inputGeminiKey.trim()} 
                      className="btn btn-primary"
                    >
                      <Key size={16} /> Save & Activate Key
                    </button>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 8 }}>
                    You can obtain a free Gemini API key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>Google AI Studio</a>.
                  </p>
                  <button type="button" className="btn btn-secondary" disabled={loading} onClick={async () => {
                    setLoading(true);
                    setLlmTest(null);
                    try {
                      const res = await fetch(`${API_BASE}/config/test-llm`, { method: 'POST' });
                      setLlmTest(await res.json());
                    } catch (err) {
                      setLlmTest({ success: false, error: err.message });
                    } finally { setLoading(false); }
                  }}>
                    <Sparkles size={15} /> Send a live test prompt
                  </button>
                  {llmTest && (
                    <pre className="mono" style={{ marginTop: 12, whiteSpace: 'pre-wrap', background: '#0f172a', color: '#e2e8f0', padding: 12, borderRadius: 8, fontSize: '0.8rem' }}>
                      {JSON.stringify(llmTest, null, 2)}
                    </pre>
                  )}
                </div>
              </form>

              {/* Explanatory Cards */}
              <div style={{ marginTop: 28, borderTop: '1px solid var(--border-subtle)', paddingTop: 20 }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: 12, color: 'var(--text-muted)' }}>How LLM-Based Evaluation Works:</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
                  <div style={{ background: 'var(--bg-secondary)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>1. Code Inspection</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                      Extracts exact line-range code snippets & manifest files from connected GitHub commit.
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-secondary)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>2. Gemini Reasoning</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                      Evaluates depth of real implementation vs shallow manifest mentions using structured schema.
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-secondary)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>3. Gap Next Steps</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                      Generates bespoke next steps, identifying exact architectural areas candidate needs to expand.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border-subtle)', padding: '18px 32px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.82rem' }}>
        AI Career Coach — Deterministic Evidence-Based Verification Pipeline • SQLite/PostgreSQL • FastAPI • React
      </footer>
    </div>
  );
}
