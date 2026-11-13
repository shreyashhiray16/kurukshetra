const skillCatalog = {
  Python: ['Languages', 1.5],
  FastAPI: ['Frameworks', 1.4],
  PostgreSQL: ['Databases', 1.3],
  Docker: ['Cloud & DevOps', 1.1],
  Redis: ['Databases', 1],
  'CI/CD': ['Cloud & DevOps', 1],
  REST: ['Architecture', 1.2],
  pytest: ['Quality Assurance', 1],
  React: ['Frameworks', 1.2],
  TypeScript: ['Languages', 1.2],
  AWS: ['Cloud & DevOps', 1.1],
  Kubernetes: ['Cloud & DevOps', 1],
  SQL: ['Databases', 1],
  GraphQL: ['Architecture', 1],
  'Node.js': ['Frameworks', 1.2],
  Java: ['Languages', 1.2],
  Spring: ['Frameworks', 1.2],
  'Machine Learning': ['AI & Machine Learning', 1.2],
  TensorFlow: ['AI & Machine Learning', 1.1],
  'System Design': ['Architecture', 1.3],
};

function makeRequirements(skills, roleTitle) {
  return skills.map((title, index) => {
    const [category, weight] = skillCatalog[title] || ['Technical Skills', 1];
    return {
      id: index + 1,
      title,
      category,
      requirement_type: index < 5 ? 'required' : 'preferred',
      weight,
      source_snippet: `${roleTitle} candidates should have practical experience with ${title}.`,
    };
  });
}

function makeJob(id, title, company, location, experience, salary, description, skills) {
  return {
    id,
    title,
    company,
    location,
    experience,
    salary,
    description,
    required_skills: skills,
    requirements: makeRequirements(skills, title),
    source_url: null,
  };
}

export const DEMO_JOBS = [
  makeJob(1001, 'Staff Full-Stack AI Engineer', 'Apex Innovations', 'Bengaluru, India', '5–8 years', '₹32–44 LPA', 'Build and scale high-throughput APIs, relational storage, and polished product workflows for AI-powered tools.', ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'React', 'TypeScript', 'REST', 'CI/CD']),
  makeJob(1002, 'Senior Backend AI Engineer', 'CloudScale AI', 'Hyderabad, India', '4–6 years', '₹26–36 LPA', 'Develop reliable model-serving APIs and data services with strong testing and production operations.', ['Python', 'FastAPI', 'PostgreSQL', 'Machine Learning', 'Docker', 'Redis', 'pytest']),
  makeJob(1003, 'Senior Full-Stack Engineer', 'TechCorp', 'Remote (India)', '4–6 years', '₹24–34 LPA', 'Ship customer-facing features across a React and TypeScript frontend and Python services.', ['React', 'TypeScript', 'Python', 'FastAPI', 'PostgreSQL', 'REST', 'CI/CD']),
  makeJob(1004, 'Principal Backend Architect', 'NextGen Cloud Solutions', 'Pune, India', '8+ years', '₹42–58 LPA', 'Lead service architecture, data strategy, and engineering standards for a distributed cloud platform.', ['Python', 'PostgreSQL', 'System Design', 'Docker', 'Kubernetes', 'AWS', 'CI/CD']),
  makeJob(1005, 'Staff Platform Engineer', 'Acme Cloud', 'Bengaluru, India', '7–10 years', '₹38–52 LPA', 'Improve developer infrastructure with container orchestration, observability, and automated delivery pipelines.', ['Python', 'Docker', 'Kubernetes', 'AWS', 'CI/CD', 'System Design']),
  makeJob(1006, 'Lead Web Services Engineer', 'Northwind Systems', 'Chennai, India', '6–9 years', '₹34–46 LPA', 'Design maintainable web services and database-backed APIs for enterprise customers.', ['Java', 'Spring', 'PostgreSQL', 'REST', 'Docker', 'pytest']),
  makeJob(1007, 'Backend Engineer Intern', 'Apex Innovations', 'Mumbai, India', '0–1 years', '₹6–10 LPA', 'Contribute to well-scoped API and data tasks with mentorship from the platform engineering team.', ['Python', 'FastAPI', 'PostgreSQL', 'REST', 'pytest']),
  makeJob(1008, 'Data Platform Engineer', 'Fieldnote AI', 'Remote (India)', '3–6 years', '₹22–32 LPA', 'Build dependable ingestion and data-processing services for analytics and applied AI products.', ['Python', 'PostgreSQL', 'SQL', 'AWS', 'Docker', 'CI/CD']),
];

export const DEMO_REPOSITORIES = [
  {
    id: 9001,
    full_name: 'candidate/portfolio-api',
    owner: 'candidate',
    language: 'Python',
    languages: ['Python', 'SQL'],
    default_branch: 'main',
    description: 'Restored sample portfolio API profile with illustrative authentication, data access, and test coverage.',
    demonstratedSkills: ['Python', 'FastAPI', 'PostgreSQL', 'REST', 'pytest', 'SQL'],
    partialSkills: ['Docker', 'React'],
  },
  {
    id: 9002,
    full_name: 'acme/platform-core',
    owner: 'acme',
    language: 'TypeScript',
    languages: ['TypeScript', 'React'],
    default_branch: 'main',
    description: 'Restored sample platform repository profile with illustrative service components and typed API clients.',
    demonstratedSkills: ['React', 'TypeScript', 'REST', 'pytest'],
    partialSkills: ['PostgreSQL', 'CI/CD'],
  },
  {
    id: 9003,
    full_name: 'fastapi/fastapi',
    owner: 'demo-candidate',
    language: 'Python',
    languages: ['Python', 'SQL'],
    default_branch: 'develop',
    description: 'Illustrative marketplace backend covering catalog and checkout service boundaries.',
    demonstratedSkills: ['Python', 'FastAPI', 'PostgreSQL', 'REST', 'Redis'],
    partialSkills: ['Docker', 'pytest'],
  },
  {
    id: 9004,
    full_name: 'demo-candidate/pulse-analytics',
    owner: 'demo-candidate',
    language: 'Python',
    languages: ['Python', 'SQL'],
    default_branch: 'main',
    description: 'Illustrative data pipeline with validation and scheduled aggregation jobs.',
    demonstratedSkills: ['Python', 'PostgreSQL', 'SQL', 'pytest'],
    partialSkills: ['AWS', 'Docker'],
  },
  {
    id: 9005,
    full_name: 'demo-candidate/ops-blueprint',
    owner: 'demo-candidate',
    language: 'HCL',
    languages: ['HCL', 'YAML', 'Python'],
    default_branch: 'main',
    description: 'Illustrative infrastructure configuration and deployment workflow examples.',
    demonstratedSkills: ['Docker', 'Kubernetes', 'AWS', 'CI/CD'],
    partialSkills: ['Python', 'System Design'],
  },
  {
    id: 9006,
    full_name: 'demo-candidate/model-evaluation-kit',
    owner: 'demo-candidate',
    language: 'Python',
    languages: ['Python'],
    default_branch: 'main',
    description: 'Illustrative model evaluation utilities, reproducible experiments, and API wrappers.',
    demonstratedSkills: ['Python', 'Machine Learning', 'TensorFlow', 'pytest'],
    partialSkills: ['FastAPI', 'Docker'],
  },
  {
    id: 9007,
    full_name: 'demo-candidate/order-orchestrator',
    owner: 'demo-candidate',
    language: 'Java',
    languages: ['Java', 'SQL'],
    default_branch: 'main',
    description: 'Illustrative Java service demonstrating order workflows and persistence patterns.',
    demonstratedSkills: ['Java', 'Spring', 'PostgreSQL', 'REST', 'Docker'],
    partialSkills: ['CI/CD', 'Redis'],
  },
  {
    id: 9008,
    full_name: 'demo-candidate/design-notes',
    owner: 'demo-candidate',
    language: 'Markdown',
    languages: ['Markdown', 'Mermaid'],
    default_branch: 'main',
    description: 'Illustrative architecture notes and system-design decision records.',
    demonstratedSkills: ['System Design'],
    partialSkills: ['AWS', 'PostgreSQL'],
  },
].map((repo) => ({ ...repo, latest_commit_sha: null, demo_only: true, connected: false }));

export const DEMO_CANDIDATE = {
  name: 'Aarav Mehta',
  headline: 'Backend Engineer · 4 years experience',
  location: 'Bengaluru, India',
  target_role: DEMO_JOBS[0].title,
  summary: 'Builds Python APIs and data-backed product features; currently strengthening production operations and delivery skills.',
  skill_scores: [
    { skill: 'Python', score: 88 },
    { skill: 'FastAPI', score: 82 },
    { skill: 'PostgreSQL', score: 78 },
    { skill: 'REST APIs', score: 84 },
    { skill: 'Docker', score: 56 },
    { skill: 'CI/CD', score: 42 },
  ],
  projects: [
    { name: 'Portfolio API', repository: 'candidate/portfolio-api', focus: 'Python API design and relational data access' },
    { name: 'Campus Connect', repository: 'acme/platform-core', focus: 'Typed user-facing workflows and integration patterns' },
    { name: 'Operations Blueprint', repository: 'demo-candidate/ops-blueprint', focus: 'Containers, cloud infrastructure, and delivery automation' },
    { name: 'Model Evaluation Kit', repository: 'demo-candidate/model-evaluation-kit', focus: 'Reproducible model evaluation and service integration' },
  ],
  project_count: 4,
  completed_assessments: 3,
};

const evidenceExamples = {
  Python: ['app/services/profile_service.py', 'def build_profile(payload):\n    return Profile(**payload)'],
  FastAPI: ['app/api/profiles.py', '@router.get("/profiles/{profile_id}")\ndef get_profile(profile_id: int):\n    return service.fetch(profile_id)'],
  PostgreSQL: ['app/core/database.py', 'engine = create_engine(settings.database_url)\nSessionLocal = sessionmaker(bind=engine)'],
  REST: ['app/api/profiles.py', '@router.post("/profiles")\ndef create_profile(payload: ProfileCreate):\n    return service.create(payload)'],
  pytest: ['tests/test_profiles.py', 'def test_profile_requires_email(client):\n    response = client.post("/profiles", json={"name": "Aarav"})\n    assert response.status_code == 422'],
  React: ['src/components/ProfileCard.tsx', 'export function ProfileCard({ name }: Props) {\n  return <article aria-label={name}>{name}</article>;\n}'],
  TypeScript: ['src/api/client.ts', 'export type Profile = {\n  id: string;\n  displayName: string;\n};'],
  Docker: ['Dockerfile', 'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .'],
  Redis: ['app/cache/client.py', 'cache = Redis.from_url(settings.redis_url)'],
  'CI/CD': ['.github/workflows/ci.yml', 'name: checks\non: [push, pull_request]\njobs:\n  test:'],
  'Machine Learning': ['ml/evaluate.py', 'metrics = evaluate_predictions(labels, predictions)'],
  TensorFlow: ['ml/model.py', 'model = tf.keras.Sequential(layers)'],
  AWS: ['infra/storage.tf', 'resource "aws_s3_bucket" "artifacts" {'],
  Kubernetes: ['deploy/app.yaml', 'kind: Deployment\nmetadata:\n  name: sample-api'],
  SQL: ['app/repositories/profiles.py', 'statement = select(Profile).where(Profile.active.is_(True))'],
  'Node.js': ['src/server.ts', 'const app = express();\napp.use(express.json());'],
  Java: ['src/main/java/demo/OrderService.java', 'public Order create(OrderRequest request) {\n    return repository.save(map(request));\n}'],
  Spring: ['src/main/java/demo/OrderController.java', '@RestController\n@RequestMapping("/orders")\nclass OrderController {'],
  'System Design': ['docs/architecture.md', '## Request flow\nAPI gateway → service → durable event queue'],
};

const roadmapDays = [
  ['Map the skill gaps', 'Review the role requirements and choose a measurable feature that exercises the highest-priority gap.', 'Write a short implementation plan and acceptance criteria for the selected feature.', 'Confirm each acceptance criterion can be checked with a test or command.'],
  ['Build the service boundary', 'Add a clean API or module boundary around the chosen feature.', 'Implement request/response schemas and separate routing from business logic.', 'Run the application and verify valid and invalid requests.'],
  ['Persist data safely', 'Connect the feature to a relational data model.', 'Add a migration, constraints, and repository methods for the new workflow.', 'Run migration up/down and verify persisted records.'],
  ['Add validation and errors', 'Make invalid input and expected failures explicit.', 'Add field validation, domain exceptions, and consistent error responses.', 'Exercise missing, malformed, and duplicate inputs.'],
  ['Write focused tests', 'Turn the new behavior into repeatable tests.', 'Add unit tests for business rules and API tests for the happy path.', 'Run the test suite and inspect failure output.'],
  ['Add cache or queue design', 'Explore when the feature needs caching or asynchronous work.', 'Document an invalidation or retry strategy and add a small isolated adapter.', 'Test cache misses, stale values, or retry behavior.'],
  ['Measure performance', 'Establish a baseline before optimizing the hot path.', 'Add a repeatable timing or query-count check for the primary endpoint.', 'Record baseline and optimized measurements with the same input.'],
  ['Harden integration tests', 'Verify the feature across API and persistence boundaries.', 'Create integration fixtures and cover transaction rollback behavior.', 'Run integration tests against a clean local database.'],
  ['Add a delivery workflow', 'Make checks run consistently on code changes.', 'Configure CI to install dependencies, lint, and run tests.', 'Verify the workflow configuration and a successful local equivalent.'],
  ['Containerize the service', 'Create a reproducible local runtime.', 'Add a small non-root container image and a health check.', 'Build and run the container, then call its health endpoint.'],
  ['Improve observability', 'Make important behavior diagnosable without exposing sensitive data.', 'Add structured logs and useful counters around the new workflow.', 'Trigger success and failure cases and inspect the resulting logs.'],
  ['Review security boundaries', 'Check trust boundaries, permissions, and input handling.', 'Document authorization assumptions and add boundary-focused tests.', 'Run dependency and static checks available in the project.'],
  ['Document the feature', 'Make setup and operational behavior clear to another engineer.', 'Update the README with configuration, examples, and known limitations.', 'Follow the documented steps in a fresh local environment.'],
  ['Refactor and review', 'Reduce complexity while keeping behavior covered.', 'Review naming, module boundaries, and migration rollback behavior.', 'Run formatting, lint, and the complete relevant test set.'],
  ['Reassess and plan next steps', 'Compare the finished work against the original skill gaps.', 'Summarize evidence, remaining gaps, and one follow-up improvement.', 'Re-run the assessment and confirm the evidence is reproducible.'],
];

function normalizeSkill(skill) {
  return skill.toLocaleLowerCase().replace(/[^a-z0-9+#]/g, '');
}

function getEvidence(skill) {
  const key = Object.keys(evidenceExamples).find((candidate) => normalizeSkill(candidate) === normalizeSkill(skill));
  return key ? evidenceExamples[key] : null;
}

function getResource(skill) {
  const normalized = normalizeSkill(skill);
  if (normalized.includes('python')) return ['Python Tutorial', 'https://docs.python.org/3/tutorial/'];
  if (normalized.includes('fastapi')) return ['FastAPI Tutorial', 'https://fastapi.tiangolo.com/tutorial/'];
  if (normalized.includes('postgres') || normalized === 'sql') return ['PostgreSQL Tutorial', 'https://www.postgresql.org/docs/current/tutorial.html'];
  if (normalized.includes('react')) return ['React Learn', 'https://react.dev/learn'];
  if (normalized.includes('typescript')) return ['TypeScript Handbook', 'https://www.typescriptlang.org/docs/handbook/intro.html'];
  if (normalized.includes('docker')) return ['Docker Get Started', 'https://docs.docker.com/get-started/'];
  if (normalized.includes('redis')) return ['Redis Get Started', 'https://redis.io/docs/latest/develop/get-started/'];
  if (normalized.includes('kubernetes')) return ['Kubernetes Tutorials', 'https://kubernetes.io/docs/tutorials/'];
  if (normalized.includes('pytest')) return ['pytest Getting Started', 'https://docs.pytest.org/en/stable/getting-started.html'];
  if (normalized.includes('ci/cd') || normalized.includes('cicd')) return ['GitHub Actions', 'https://docs.github.com/en/actions'];
  if (normalized.includes('tensorflow')) return ['TensorFlow Tutorials', 'https://www.tensorflow.org/tutorials'];
  if (normalized.includes('java') || normalized.includes('spring')) return ['Spring Guides', 'https://spring.io/guides'];
  return ['AWS Documentation', 'https://docs.aws.amazon.com/'];
}

function createRoadmap(job, repo, gaps) {
  const fallbackSkill = job.required_skills[0] || 'Software Engineering';
  const focusSkills = gaps.length ? gaps : job.required_skills;
  const tasks = roadmapDays.map(([topic, goal, codeTask, verification], index) => {
    const day = index + 1;
    const targetSkill = focusSkills[index % focusSkills.length] || fallbackSkill;
    const [resourceTitle, resourceUrl] = getResource(targetSkill);
    return {
      day,
      day_title: `Day ${day}: ${topic}`,
      target_skill: targetSkill,
      action_goal: `${goal} Apply the work to ${repo.full_name}.`,
      code_task: codeTask,
      verification_step: verification,
      recommended_resources: [{ title: resourceTitle, url: resourceUrl, type: 'docs', skill: targetSkill }],
    };
  });

  const phaseInfo = [
    ['Foundation and core implementation', 'Days 1-5', 'A scoped feature with clear contracts and focused tests.'],
    ['Integration and quality', 'Days 6-10', 'A tested workflow with repeatable local delivery checks.'],
    ['Production readiness and reflection', 'Days 11-15', 'Documented evidence and a prioritized follow-up plan.'],
  ];

  return {
    title: '15-Day Skill-Gap Learning Roadmap',
    target_role: job.title,
    target_repo: repo.full_name,
    duration_days: 15,
    summary: `A practical plan for ${job.title}, focused on ${[...new Set(gaps)].slice(0, 3).join(', ') || fallbackSkill}.`,
    expected_outcome: `A documented, tested feature in ${repo.full_name} that provides repeatable examples for the selected skill gaps.`,
    phases: phaseInfo.map(([title, day_range, milestone], index) => ({
      phase_number: index + 1,
      title,
      day_range,
      focus_skills: [...new Set(tasks.slice(index * 5, index * 5 + 5).map((task) => task.target_skill))],
      milestone,
      tasks: tasks.slice(index * 5, index * 5 + 5),
    })),
  };
}

export function createDemoAssessment(job, repo) {
  const demonstrated = new Set((repo.demonstratedSkills || []).map(normalizeSkill));
  const partial = new Set((repo.partialSkills || []).map(normalizeSkill));
  const skill_assessments = (job.requirements || []).map((requirement) => {
    const key = normalizeSkill(requirement.title);
    const status = demonstrated.has(key) ? 'met' : partial.has(key) ? 'partial' : 'unmet';
    const evidence = status === 'unmet' ? null : getEvidence(requirement.title);
    const citation = evidence ? [{
      file_path: evidence[0],
      start_line: 1,
      end_line: evidence[1].split('\n').length,
      commit_sha: 'demo-example-not-a-real-commit',
      snippet_text: evidence[1],
      github_url: null,
      is_dependency_or_doc_only: status === 'partial',
    }] : [];
    const [resourceTitle, resourceUrl] = getResource(requirement.title);

    return {
      requirement_id: requirement.id,
      requirement_title: requirement.title,
      category: requirement.category,
      requirement_type: requirement.requirement_type,
      weight: requirement.weight,
      source_snippet: requirement.source_snippet,
      status,
      confidence_score: status === 'met' ? 0.88 : status === 'partial' ? 0.62 : 0.4,
      reason: status === 'met'
        ? `Illustrative sample evidence is provided for ${requirement.title}; no GitHub repository was scanned.`
        : status === 'partial'
          ? `The demo profile includes a limited example for ${requirement.title}; this is not a live repository assessment.`
          : `No sample evidence is included for ${requirement.title}; this demo gap does not indicate the candidate lacks the skill.`,
      limitations: ['Demonstration data only; no code was fetched from or verified against GitHub.'],
      next_step: status === 'met' ? null : `Add a small, tested ${requirement.title} example to the portfolio project.`,
      citations: citation,
      resources: status === 'met' ? [] : [{
        skill: requirement.title,
        title: resourceTitle,
        url: resourceUrl,
        type: 'docs',
        channel_or_site: 'Official documentation',
        why_relevant: `Official learning material for ${requirement.title}.`,
      }],
      practice_task: `Implement a small, tested ${requirement.title} feature in the sample project.`,
      llm_used: false,
      llm_model: null,
    };
  });

  const counts = skill_assessments.reduce((result, skill) => {
    result[skill.status] += 1;
    return result;
  }, { met: 0, partial: 0, unmet: 0 });
  const total = skill_assessments.length;
  const score = total ? Math.round(((counts.met + counts.partial * 0.5) / total) * 100) : 0;
  const gaps = skill_assessments.filter((skill) => skill.status !== 'met').map((skill) => skill.requirement_title);

  return {
    job_id: job.id,
    job_title: job.title,
    repo_id: repo.id,
    repo_full_name: repo.full_name,
    evaluated_at: new Date().toISOString(),
    is_demo: true,
    summary: {
      total_skills: total,
      met: counts.met,
      partial: counts.partial,
      unmet: counts.unmet,
      needs_review: 0,
      overall_match_percentage: score,
      weighted_score: score,
    },
    readiness: {
      score,
      band: score >= 80 ? 'Strong' : score >= 65 ? 'Competitive' : score >= 45 ? 'Stretch' : 'Not ready',
      confidence: 'illustrative',
      rationale: 'This example score is generated from the demo evidence shown below. It is not a live repository scan or a hiring prediction.',
    },
    roadmap: createRoadmap(job, repo, gaps),
    skill_assessments,
  };
}

export function createDemoJobFromText(rawText, id) {
  const lines = rawText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const titleLine = lines.find((line) => /^job title\s*:/i.test(line));
  const companyLine = lines.find((line) => /^company\s*:/i.test(line));
  const title = titleLine ? titleLine.split(':').slice(1).join(':').trim() : 'Imported Demo Role';
  const company = companyLine ? companyLine.split(':').slice(1).join(':').trim() : 'Local demo';
  const detectedSkills = Object.keys(skillCatalog).filter((skill) => (
    skill === 'SQL'
      ? /\bSQL\b/i.test(rawText)
      : rawText.toLowerCase().includes(skill.toLowerCase())
  ));
  const skills = detectedSkills.length ? detectedSkills : ['Python', 'REST'];
  const job = makeJob(id, title, company, 'Not specified', 'Not specified', 'Not specified', rawText, skills);
  job.raw_text = rawText;
  job.demo_only = true;
  return job;
}

export const DEMO_INITIAL_ROADMAP_PROGRESS = {
  1: 'completed',
  2: 'in_progress',
};

export const DEMO_ROADMAP_STORAGE_KEY = 'career-coach-demo-roadmap-progress';
