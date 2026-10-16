import re
import httpx
from bs4 import BeautifulSoup

class JobFetcherService:
    @staticmethod
    async def fetch_url_content(url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Strategy 1: Direct fetch with standard HTTP client
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200 and len(resp.text.strip()) > 300:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Remove scripts, styles, navigation, footer
                    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                        tag.decompose()
                    
                    text = soup.get_text(separator="\n")
                    # Clean up empty lines
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    cleaned_text = "\n".join(lines)
                    if len(cleaned_text) > 200:
                        return cleaned_text
        except Exception as e:
            print(f"Direct fetch failed: {e}. Trying Jina Reader...")

        # Strategy 2: Fallback to Jina Reader (handles SPAs, JS rendering, clean markdown)
        try:
            jina_url = f"https://r.jina.ai/{url}"
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(jina_url, headers=headers)
                if resp.status_code == 200 and len(resp.text.strip()) > 100:
                    return resp.text.strip()
        except Exception as e:
            print(f"Jina Reader fetch failed: {e}")

        raise ValueError(f"Could not extract meaningful content from the provided URL: {url}")
