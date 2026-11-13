import assert from 'node:assert/strict';
import {
  DEMO_JOBS,
  DEMO_REPOSITORIES,
  createDemoAssessment,
  createDemoJobFromText,
} from './demoData.js';

assert.equal(DEMO_JOBS.length, 8, 'the Naukri Hub demo catalog contains eight jobs');
assert.equal(DEMO_REPOSITORIES.length, 8, 'the repository demo catalog contains eight samples');
assert.ok(DEMO_JOBS.every(job => job.requirements.length > 0 && job.salary && job.location));
assert.ok(DEMO_REPOSITORIES.every(repo => repo.demo_only && !repo.connected && !repo.latest_commit_sha));

const assessment = createDemoAssessment(DEMO_JOBS[0], DEMO_REPOSITORIES[0]);
const roadmapTasks = assessment.roadmap.phases.flatMap(phase => phase.tasks);
assert.equal(roadmapTasks.length, 15, 'the roadmap contains one task for each day');
assert.deepEqual(roadmapTasks.map(task => task.day), Array.from({ length: 15 }, (_, index) => index + 1));
assert.ok(assessment.summary.met > 0);
assert.ok(assessment.summary.partial > 0);
assert.ok(assessment.summary.unmet > 0);
assert.equal(
  assessment.summary.met + assessment.summary.partial + assessment.summary.unmet,
  assessment.summary.total_skills,
);
assert.ok(assessment.skill_assessments.some(skill => skill.citations.length > 0));
assert.ok(assessment.skill_assessments.some(skill => skill.status === 'unmet' && skill.citations.length === 0));
assert.ok(assessment.skill_assessments.flatMap(skill => skill.citations).every(citation => !citation.github_url));
assert.equal(assessment.is_demo, true);

const imported = createDemoJobFromText(
  'Job Title: API Engineer\nCompany: Example Co\nBuild with Python, FastAPI, and PostgreSQL.',
  1010,
);
assert.equal(imported.id, 1010);
assert.equal(imported.title, 'API Engineer');
assert.equal(imported.company, 'Example Co');
assert.deepEqual(imported.required_skills, ['Python', 'FastAPI', 'PostgreSQL']);

console.log('Demo catalog, assessment, evidence, and roadmap checks passed.');
