import re
import json
import html
import httpx
from typing import Optional, Dict, Any, Tuple
from bs4 import BeautifulSoup

try:
    import trafilatura
except ImportError:
    trafilatura = None

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
}

class JobFetcherService:
    @staticmethod
    def html_to_clean_text(html_content: str) -> str:
        """Converts raw HTML into clean, well-formatted plain text."""
        if not html_content:
            return ""
        
        # Unescape HTML entities first if escaped
        unescaped = html.unescape(html_content)
        
        soup = BeautifulSoup(unescaped, "html.parser")
        # Remove undesirable tags
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "button", "input", "form"]):
            tag.decompose()
        
        # Replace list items with clean bullet points
        for li in soup.find_all("li"):
            li.insert_before("\n• ")
            li.unwrap()
        
        # Replace paragraphs and headings with clean line breaks
        for block in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br"]):
            block.insert_before("\n")
        
        text = soup.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    @classmethod
    async def fetch_job_details(cls, url: str, summarize: bool = True) -> Dict[str, Any]:
        """
        Fetches job description and metadata quickly from any company career page URL.
        Optionally summarizes using Groq LLM to isolate important necessary details.
        Returns: {
            "title": Optional[str],
            "company": Optional[str],
            "raw_text": str,
            "strategy": str,
            "summarized": bool,
            "summary_model": Optional[str]
        }
        """
        clean_url = url.strip()
        if not clean_url:
            raise ValueError("URL cannot be empty")
        
        extracted_result = None

        # Strategy 1: Fast ATS API endpoints (Lever, Greenhouse) if URL matches
        ats_result = await cls._try_ats_apis(clean_url)
        if ats_result and ats_result.get("raw_text") and len(ats_result["raw_text"]) >= 100:
            extracted_result = ats_result

        # Strategy 2: Direct HTTP Fetch with Trafilatura + JSON-LD (fastest standard web page extraction)
        if not extracted_result:
            html_doc = await cls._fetch_html(clean_url)
            if html_doc:
                # 2a. Check for schema.org JobPosting JSON-LD (used by Workday, Greenhouse, Ashby, SmartRecruiters, Lever, corporate sites)
                ld_result = cls._extract_from_json_ld(html_doc)
                if ld_result and ld_result.get("raw_text") and len(ld_result["raw_text"]) >= 120:
                    extracted_result = ld_result

                # 2b. Trafilatura article / main body extractor (industry benchmark for web text extraction)
                if not extracted_result and trafilatura:
                    try:
                        traf_text = trafilatura.extract(
                            html_doc,
                            include_formatting=False,
                            include_links=False,
                            favor_precision=True
                        )
                        if traf_text and len(traf_text.strip()) >= 150:
                            title, company = cls._extract_meta_hints(html_doc)
                            extracted_result = {
                                "title": title,
                                "company": company,
                                "raw_text": traf_text.strip(),
                                "strategy": "trafilatura"
                            }
                    except Exception as e:
                        print(f"Trafilatura extraction failed: {e}")

                # 2c. BeautifulSoup fallback cleaner on direct HTML
                if not extracted_result:
                    bs_text = cls.html_to_clean_text(html_doc)
                    if bs_text and len(bs_text.strip()) >= 150:
                        title, company = cls._extract_meta_hints(html_doc)
                        extracted_result = {
                            "title": title,
                            "company": company,
                            "raw_text": bs_text.strip(),
                            "strategy": "direct_html_bs4"
                        }

        # Strategy 3: Jina Reader fallback (handles client-rendered SPAs, JS frameworks)
        if not extracted_result:
            jina_text = await cls._fetch_jina_reader(clean_url)
            if jina_text and len(jina_text.strip()) >= 100:
                extracted_result = {
                    "title": None,
                    "company": None,
                    "raw_text": jina_text.strip(),
                    "strategy": "jina_reader"
                }
        elif 'ats_result' in locals() and ats_result:
            extracted_result = ats_result
        else:
            raise ValueError(f"Could not extract meaningful job description from the provided URL: {clean_url}")

        # Post-process: summarize using Groq LLM to isolate important necessary requirements
        if summarize and extracted_result.get("raw_text"):
            summary, model = cls.summarize_job_description(
                extracted_result["raw_text"],
                title=extracted_result.get("title"),
                company=extracted_result.get("company")
            )
            extracted_result["raw_text"] = summary
            extracted_result["summarized"] = True
            extracted_result["summary_model"] = model

        return extracted_result

    @classmethod
    async def fetch_url_content(cls, url: str) -> str:
        """Backward-compatible helper returning just raw text."""
        details = await cls.fetch_job_details(url)
        return details.get("raw_text", "")

    @staticmethod
    async def _fetch_html(url: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=DEFAULT_HEADERS)
                if resp.status_code == 200 and len(resp.text.strip()) > 100:
                    return resp.text
        except Exception as e:
            print(f"Direct HTML fetch failed for {url}: {e}")
        return None

    @classmethod
    async def _try_ats_apis(cls, url: str) -> Optional[Dict[str, Any]]:
        """Direct JSON API fetch for popular ATS platforms (instant response)."""
        # Lever: e.g. https://jobs.lever.co/spotify/abc-123 or https://jobs.lever.co/company
        lever_match = re.search(r"jobs\.lever\.co/([^/]+)/([a-f0-9\-]+)", url, re.IGNORECASE)
        if lever_match:
            company, job_id = lever_match.group(1), lever_match.group(2)
            api_url = f"https://api.lever.co/v0/postings/{company}/{job_id}"
            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                    resp = await client.get(api_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        desc = data.get("descriptionPlain") or cls.html_to_clean_text(data.get("description", ""))
                        additional = data.get("additionalPlain") or cls.html_to_clean_text(data.get("additional", ""))
                        lists_text = ""
                        for li_group in data.get("lists", []):
                            lists_text += f"\n\n{li_group.get('text', '')}:\n" + cls.html_to_clean_text(li_group.get("content", ""))
                        
                        full_text = f"Job Title: {data.get('text', '')}\nCompany: {company.capitalize()}\n\n{desc}\n{lists_text}\n{additional}".strip()
                        return {
                            "title": data.get("text"),
                            "company": company.capitalize(),
                            "raw_text": full_text,
                            "strategy": "lever_api"
                        }
            except Exception as e:
                print(f"Lever API fetch failed: {e}")

        # Greenhouse: e.g. https://boards.greenhouse.io/stripe/jobs/8172508 or https://job-boards.greenhouse.io/stripe/jobs/8172508
        gh_match = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", url, re.IGNORECASE)
        if gh_match:
            board_token, job_id = gh_match.group(1), gh_match.group(2)
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"
            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                    resp = await client.get(api_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        title = data.get("title", "")
                        comp = data.get("company_name") or board_token.capitalize()
                        raw_desc = cls.html_to_clean_text(data.get("content", ""))
                        full_text = f"Job Title: {title}\nCompany: {comp}\n\n{raw_desc}".strip()
                        return {
                            "title": title,
                            "company": comp,
                            "raw_text": full_text,
                            "strategy": "greenhouse_api"
                        }
            except Exception as e:
                print(f"Greenhouse API fetch failed: {e}")

        return None

    @classmethod
    def _extract_from_json_ld(cls, html_doc: str) -> Optional[Dict[str, Any]]:
        """Parses Schema.org JobPosting JSON-LD if present."""
        try:
            soup = BeautifulSoup(html_doc, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                if not script.string:
                    continue
                try:
                    data = json.loads(script.string)
                except Exception:
                    continue

                candidates = []
                if isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        candidates.append(data)
                    elif "@graph" in data and isinstance(data["@graph"], list):
                        for item in data["@graph"]:
                            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                                candidates.append(item)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            candidates.append(item)

                for job in candidates:
                    title = job.get("title")
                    company = None
                    hiring_org = job.get("hiringOrganization")
                    if isinstance(hiring_org, dict):
                        company = hiring_org.get("name")
                    elif isinstance(hiring_org, str):
                        company = hiring_org
                    
                    raw_html = job.get("description", "")
                    clean_desc = cls.html_to_clean_text(raw_html) if raw_html else ""
                    
                    if clean_desc and len(clean_desc) > 100:
                        header_part = ""
                        if title:
                            header_part += f"Job Title: {title}\n"
                        if company:
                            header_part += f"Company: {company}\n\n"
                        full_text = (header_part + clean_desc).strip()
                        return {
                            "title": title,
                            "company": company,
                            "raw_text": full_text,
                            "strategy": "json_ld_schema"
                        }
        except Exception as e:
            print(f"JSON-LD extraction failed: {e}")
        return None

    @staticmethod
    def _extract_meta_hints(html_doc: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract title and company hints from meta tags and OpenGraph tags."""
        title, company = None, None
        try:
            soup = BeautifulSoup(html_doc, "html.parser")
            # Title
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()

            # Company / Site Name
            og_site = soup.find("meta", property="og:site_name")
            if og_site and og_site.get("content"):
                company = og_site["content"].strip()
        except Exception:
            pass
        return title, company

    @staticmethod
    async def _fetch_jina_reader(url: str) -> Optional[str]:
        try:
            jina_url = f"https://r.jina.ai/{url}"
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(jina_url, headers=DEFAULT_HEADERS)
                if resp.status_code == 200 and len(resp.text.strip()) > 100:
                    return resp.text.strip()
        except Exception as e:
            print(f"Jina Reader fetch failed: {e}")
        return None

    @classmethod
    def summarize_job_description(cls, raw_text: str, title: Optional[str] = None, company: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Summarizes any raw job description using Groq/LLM to only show the important,
        necessary description (Role Overview, Key Responsibilities, Core Technical Requirements,
        and Qualifications) while stripping boilerplates, legal disclaimers, and noise.
        Returns: (summarized_text, model_name)
        """
        from app.services.llm_provider import get_provider
        from app.services.gemini_service import sanitize

        header_hints = ""
        if title:
            header_hints += f"Job Title: {title}\n"
        if company:
            header_hints += f"Company: {company}\n"

        prompt = f"""You are an executive technical recruiter and job analyzer.
Analyze the following raw scraped job description and produce a structured, high-density summary containing ONLY the important, necessary details formatted with clear sections:

Role Overview:
(2-3 crisp sentences explaining what the role is and does)

Key Responsibilities:
• (Top 4-6 bullet points of actual work and technical duties)

Required Skills & Technologies:
• (Languages, frameworks, databases, tools, infrastructure)

Qualifications & Requirements:
• (Years of experience, core background, education/equivalent)

Exclude all generic corporate fluff, EEO/diversity legal statements, application instructions, and company perks.
Make it clean, clear, and focused on essential job duties and skills.

Return JSON in this exact structure:
{{
  "title": str or null,
  "company": str or null,
  "summary": str
}}

<DATA>
{header_hints}{sanitize(raw_text, 12000)}
</DATA>"""

        try:
            provider = get_provider()
            res = provider.generate_json(prompt)
            if res.data and res.data.get("summary"):
                summary_text = res.data["summary"].strip()
                # If title / company provided in JSON, ensure clean prefix
                parsed_title = res.data.get("title") or title
                parsed_comp = res.data.get("company") or company
                prefix = ""
                if parsed_title and not summary_text.lower().startswith("job title:"):
                    prefix += f"Job Title: {parsed_title}\n"
                if parsed_comp and "company:" not in summary_text.lower()[:100]:
                    prefix += f"Company: {parsed_comp}\n\n"
                
                final_text = (prefix + summary_text).strip()
                return final_text, res.model
        except Exception as e:
            print(f"LLM job summarization failed: {e}")

        # Fallback if LLM unavailable: clean up raw text
        return raw_text.strip(), None

