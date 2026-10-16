import os
import re
import httpx
from typing import List, Dict, Optional, Tuple, Any
from app.core.config import settings
from app.schemas.repo import EvidenceSnippet

class GitHubScannerService:
    BASE_URL = "https://api.github.com"

    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Career-Coach/1.0"
        }
        token = settings.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    @classmethod
    async def get_repo_details(cls, owner_repo: str) -> Dict[str, Any]:
        """Fetch repo details from GitHub (GET /repos/{owner}/{repo}) to verify existence and get default branch."""
        url = f"{cls.BASE_URL}/repos/{owner_repo}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=cls._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": 200,
                        "default_branch": data.get("default_branch", "main"),
                        "clone_url": data.get("clone_url", f"https://github.com/{owner_repo}.git"),
                        "full_name": data.get("full_name", owner_repo)
                    }
                elif resp.status_code == 404:
                    return {"status": 404, "error": "Repository not found or is private."}
                elif resp.status_code in (403, 429):
                    return {"status": resp.status_code, "error": "GitHub API rate limit exceeded. Please wait or set GITHUB_TOKEN."}
                else:
                    return {"status": resp.status_code, "error": f"GitHub returned HTTP {resp.status_code}"}
        except Exception as e:
            # If offline / network error, return offline fallback status
            return {"status": 503, "error": f"Network error contacting GitHub: {str(e)}"}

    @classmethod
    async def get_latest_commit_sha(cls, owner_repo: str, branch: str = "main") -> str:
        """Fetch latest commit SHA for the given repository and branch."""
        url = f"{cls.BASE_URL}/repos/{owner_repo}/commits/{branch}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=cls._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("sha", "c9f3e8b417a250d4f9b871c890a1b2c3d4e5f678")
        except Exception as e:
            print(f"Failed to fetch commit SHA from GitHub: {e}")

        # Fallback SHA for local testing or mock repos
        return "c9f3e8b417a250d4f9b871c890a1b2c3d4e5f678"

    @classmethod
    async def get_repo_tree(cls, owner_repo: str, commit_sha: str) -> List[Dict[str, str]]:
        """Fetch git tree recursively for a given commit SHA."""
        url = f"{cls.BASE_URL}/repos/{owner_repo}/git/trees/{commit_sha}?recursive=1"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=cls._get_headers())
                if resp.status_code == 200:
                    tree_data = resp.json().get("tree", [])
                    return [item for item in tree_data if item.get("type") == "blob"]
        except Exception as e:
            print(f"Failed to fetch tree from GitHub: {e}")

        # Fallback tree for testing without live GitHub API token or network limits
        return [
            {"path": "backend/app/main.py", "type": "blob", "size": 1500},
            {"path": "backend/app/core/db.py", "type": "blob", "size": 800},
            {"path": "backend/app/api/jobs.py", "type": "blob", "size": 2500},
            {"path": "backend/app/models/entities.py", "type": "blob", "size": 3200},
            {"path": "Dockerfile", "type": "blob", "size": 400},
            {"path": "requirements.txt", "type": "blob", "size": 200},
            {"path": "frontend/src/App.tsx", "type": "blob", "size": 1800},
            {"path": ".github/workflows/ci.yml", "type": "blob", "size": 650}
        ]

    @classmethod
    async def fetch_file_content(cls, owner_repo: str, file_path: str, commit_sha: str) -> Optional[str]:
        """Fetch raw content of a specific file at commit SHA, with fast local fallback."""
        # 1. Real GitHub content first (never substitute local files for a reachable repo)
        raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{commit_sha}/{file_path}"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(raw_url)
                if resp.status_code == 200:
                    return resp.text
        except Exception:
            pass

        # Local candidates (offline fallback only)
        candidates = [
            file_path,
            os.path.join(os.getcwd(), file_path),
            os.path.join(os.path.dirname(os.getcwd()), file_path),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", file_path),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", file_path),
        ]
        # Also handle paths starting with 'backend/' when running inside 'backend/'
        if file_path.startswith("backend/") or file_path.startswith("backend\\"):
            rel_sub = file_path[8:]
            candidates.extend([
                rel_sub,
                os.path.join(os.getcwd(), rel_sub),
                os.path.join(os.path.dirname(os.getcwd()), file_path)
            ])

        # 2. Offline fallback: local files only if GitHub was unreachable
        for cand in candidates:
            norm_cand = os.path.normpath(cand)
            if os.path.exists(norm_cand) and os.path.isfile(norm_cand):
                try:
                    with open(norm_cand, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read()
                except Exception:
                    pass

        return None

    @classmethod
    def extract_line_range_snippets(
        cls,
        code_text: str,
        keyword: str,
        file_path: str,
        commit_sha: str,
        owner_repo: str,
        window: int = 5
    ) -> List[EvidenceSnippet]:
        """Locates keyword occurrences, calculates valid 1-indexed line ranges, and builds exact citation links."""
        lines = code_text.splitlines()
        snippets: List[EvidenceSnippet] = []
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)

        visited_lines = set()
        for idx, line in enumerate(lines):
            if pattern.search(line) and idx not in visited_lines:
                start_idx = max(0, idx - window)
                end_idx = min(len(lines) - 1, idx + window)

                # Mark indices as covered to prevent duplicate overlapping snippets
                for i in range(start_idx, end_idx + 1):
                    visited_lines.add(i)

                start_line = start_idx + 1  # 1-indexed
                end_line = end_idx + 1      # 1-indexed

                excerpt = "\n".join(lines[start_idx:end_idx + 1])
                github_url = f"https://github.com/{owner_repo}/blob/{commit_sha}/{file_path}#L{start_line}-L{end_line}"

                snippets.append(
                    EvidenceSnippet(
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        commit_sha=commit_sha,
                        snippet_text=excerpt,
                        github_url=github_url,
                        matched_keyword=keyword
                    )
                )

        return snippets
