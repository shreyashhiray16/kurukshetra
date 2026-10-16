import os
import re
from typing import List, Dict, Any, Optional
from app.models.entities import Requirement, Repository, AssessmentStatus
from app.schemas.assessment import CitationItem, SkillAssessmentResult, AssessmentSummary
from app.services.github_scanner import GitHubScannerService

class AssessmentEngineService:
    """
    Deterministic Assessment & Gap Analysis Engine.
    Evaluates repository code snapshots against job requirements with deterministic validation:
    - Code vs README / Dependency declaration separation
    - 1-indexed line-range citation validation
    - Commit SHA binding
    - Actionable next steps for skill gaps
    - Weighted match percentage calculation
    """

    DEPENDENCY_DOC_FILES = (
        "requirements.txt", "package.json", "setup.py", "pyproject.toml",
        "gemfile", "go.mod", "pom.xml", "cargo.toml", "readme.md", "readme"
    )

    @classmethod
    def is_dependency_or_doc_file(cls, path: str) -> bool:
        norm = path.lower()
        base = os.path.basename(norm)
        return any(base == doc or base.startswith("readme") for doc in cls.DEPENDENCY_DOC_FILES)

    @classmethod
    def validate_citation(
        cls,
        citation: CitationItem,
        tree_paths: List[str],
        file_content: Optional[str] = None,
    ) -> bool:
        # Rule 1: Path must exist in repository snapshot
        if citation.file_path not in tree_paths and not any(p.endswith(citation.file_path) for p in tree_paths):
            return False
        # Rule 2: Line numbers must be 1-indexed and valid
        if citation.start_line < 1 or citation.end_line < citation.start_line:
            return False
        # Rule 3: Commit SHA must be valid
        if not citation.commit_sha or len(citation.commit_sha) < 7:
            return False
        # Rule 4: Excerpt must be the real file text at those lines (architecture §7)
        if file_content is not None:
            lines = file_content.splitlines()
            if citation.end_line > len(lines):
                return False
            actual = "\n".join(lines[citation.start_line - 1:citation.end_line])
            if citation.snippet_text.strip() != actual.strip():
                return False
        return True

    @classmethod
    async def evaluate_requirement(
        cls,
        requirement: Requirement,
        repo: Repository,
        tree_paths: List[str],
        content_cache: Optional[Dict[str, Optional[str]]] = None
    ) -> SkillAssessmentResult:
        """
        Evaluate a single job requirement against repository code.
        Extracts evidence and determines status: MET, PARTIAL, or UNMET.
        """
        if content_cache is None:
            content_cache = {}

        keywords_to_check = [requirement.title]
        # Clean title for keyword search (e.g., 'FastAPI Backend Development' -> ['FastAPI', 'Backend'])
        clean_words = re.findall(r'[A-Za-z0-9+#]+', requirement.title)
        primary_term = clean_words[0] if clean_words else requirement.title

        # Search for evidence across candidate files
        candidate_extensions = (
            ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
            ".sql", ".yml", ".yaml", "Dockerfile", "requirements.txt", "package.json"
        )

        all_snippets = []
        code_snippets = []
        doc_dep_snippets = []

        for path in tree_paths:
            if any(path.endswith(ext) or path == ext for ext in candidate_extensions):
                if path not in content_cache:
                    content_cache[path] = await GitHubScannerService.fetch_file_content(
                        repo.full_name, path, repo.latest_commit_sha or "main"
                    )
                content = content_cache[path]
                if content:
                    found = GitHubScannerService.extract_line_range_snippets(
                        code_text=content,
                        keyword=primary_term,
                        file_path=path,
                        commit_sha=repo.latest_commit_sha or "HEAD",
                        owner_repo=repo.full_name
                    )
                    for item in found:
                        is_dep_doc = cls.is_dependency_or_doc_file(item.file_path)
                        cit = CitationItem(
                            file_path=item.file_path,
                            start_line=item.start_line,
                            end_line=item.end_line,
                            commit_sha=item.commit_sha,
                            snippet_text=item.snippet_text,
                            github_url=item.github_url,
                            is_dependency_or_doc_only=is_dep_doc
                        )
                        if cls.validate_citation(cit, tree_paths, content):
                            all_snippets.append(cit)
                            if is_dep_doc:
                                doc_dep_snippets.append(cit)
                            else:
                                code_snippets.append(cit)

        # Primary: Gemini LLM Decision Evaluation
        from app.services.gemini_service import GeminiService
        llm_eval = await GeminiService.evaluate_skill_with_llm(
            requirement_title=requirement.title,
            category=requirement.category,
            requirement_type=requirement.requirement_type.value,
            job_source_snippet=requirement.source_snippet,
            code_snippets=[
                {"file": c.file_path, "lines": f"{c.start_line}-{c.end_line}", "code": c.snippet_text}
                for c in code_snippets[:5]
            ],
            doc_dep_snippets=[
                {"file": c.file_path, "lines": f"{c.start_line}-{c.end_line}", "text": c.snippet_text}
                for c in doc_dep_snippets[:5]
            ]
        )

        llm_used = False
        llm_model = None
        llm_error = llm_eval.get("error") if llm_eval and "error" in llm_eval else None
        if llm_eval and not llm_error:
            llm_used = True
            llm_model = llm_eval.get("model")
            status = AssessmentStatus(llm_eval["status"])
            confidence = llm_eval["confidence_score"]
            reason = llm_eval["reason"]
            limitations = llm_eval.get("limitations", [])
            next_step = llm_eval.get("next_step")
            shown_code = code_snippets[:5]
            cited = [shown_code[i] for i in llm_eval.get("cited_code_ids", []) if i < len(shown_code)]
            # Deterministic validation of the LLM verdict (architecture §5/§7)
            if status == AssessmentStatus.MET and not cited:
                status = AssessmentStatus.NEEDS_REVIEW
                limitations = limitations + ["Validation: 'met' claimed without valid executable-code citations"]
            elif status == AssessmentStatus.MET and not code_snippets:
                status = AssessmentStatus.NEEDS_REVIEW
            elif status == AssessmentStatus.UNMET and code_snippets:
                status = AssessmentStatus.NEEDS_REVIEW
                limitations = limitations + ["Validation: 'unmet' claimed but code evidence exists"]
            if cited:
                code_snippets = cited + [c for c in code_snippets if c not in cited]
        else:
            if llm_error:
                logger_msg = f"LLM unavailable ({llm_error[:120]}); deterministic fallback used"
                print(logger_msg)
            # Deterministic Fallback Rules
            if len(code_snippets) >= 2:
                status = AssessmentStatus.MET
                confidence = 0.95
                reason = f"Substantial code implementation found demonstrating '{requirement.title}' across {len(code_snippets)} code citations."
                limitations = []
                next_step = None
            elif len(code_snippets) == 1:
                status = AssessmentStatus.PARTIAL
                confidence = 0.70
                reason = f"Minimal implementation found for '{requirement.title}' (1 citation in code)."
                limitations = ["Limited depth of usage in source files"]
                next_step = f"Expand implementation of {requirement.title} with additional endpoints, modules, or tests."
            elif len(doc_dep_snippets) > 0:
                status = AssessmentStatus.PARTIAL
                confidence = 0.40
                reason = f"Found '{requirement.title}' declared in dependency/docs, but no actual substantive usage detected in executable code."
                limitations = ["Declared in manifest/documentation only, missing functional implementation"]
                next_step = f"Implement functional code utilizing {requirement.title} instead of only manifest declarations."
            else:
                status = AssessmentStatus.UNMET
                confidence = 0.0
                reason = f"No evidence of '{requirement.title}' found in inspected repository files."
                limitations = ["Skill not demonstrated in repository"]
                next_step = f"Build a feature or service showcasing {requirement.title} to address this gap."

        # Keep primary citations up to 5
        selected_citations = (code_snippets if code_snippets else doc_dep_snippets)[:5]

        return SkillAssessmentResult(
            requirement_id=requirement.id or 0,
            requirement_title=requirement.title,
            category=requirement.category,
            requirement_type=requirement.requirement_type.value,
            weight=requirement.weight,
            source_snippet=requirement.source_snippet,
            status=status,
            confidence_score=confidence,
            reason=reason,
            limitations=limitations,
            next_step=next_step,
            citations=selected_citations,
            llm_used=llm_used,
            llm_model=llm_model,
            llm_response=llm_eval if llm_used else None,
        )

    @classmethod
    def calculate_summary(cls, skill_results: List[SkillAssessmentResult]) -> AssessmentSummary:
        total = len(skill_results)
        if total == 0:
            return AssessmentSummary(
                total_skills=0,
                met=0,
                partial=0,
                unmet=0,
                overall_match_percentage=0.0,
                weighted_score=0.0
            )

        met_count = sum(1 for s in skill_results if s.status == AssessmentStatus.MET)
        partial_count = sum(1 for s in skill_results if s.status == AssessmentStatus.PARTIAL)
        unmet_count = sum(1 for s in skill_results if s.status == AssessmentStatus.UNMET)

        # Calculate weighted scores
        total_possible_weight = sum(s.weight for s in skill_results)
        earned_weight = 0.0

        for s in skill_results:
            if s.status == AssessmentStatus.MET:
                earned_weight += s.weight * 1.0
            elif s.status == AssessmentStatus.PARTIAL:
                earned_weight += s.weight * 0.5

        weighted_score = round(earned_weight, 2)
        match_percentage = round((earned_weight / total_possible_weight * 100), 1) if total_possible_weight > 0 else 0.0

        return AssessmentSummary(
            total_skills=total,
            met=met_count,
            partial=partial_count,
            unmet=unmet_count,
            needs_review=sum(1 for s in skill_results if s.status == AssessmentStatus.NEEDS_REVIEW),
            overall_match_percentage=match_percentage,
            weighted_score=weighted_score
        )
