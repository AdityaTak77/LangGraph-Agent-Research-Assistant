# ==========================================
# utils/web_search.py
# ==========================================
"""
Provides a lightweight mock or real web search utility for the SearchAgent.

⚙️ Features:
- Simple "mock" dataset for offline use
- Optional live web search using requests + BeautifulSoup (no API key required)
- Returns list[dict]: {"title", "source", "text"}

Dependencies:
    pip install requests beautifulsoup4
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def simple_web_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Perform a minimal live web search using DuckDuckGo HTML results
    (No API key required, purely scraping public results).
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchAssistant/1.0)"}
    url = f"https://duckduckgo.com/html/?q={query}"
    docs = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.find_all("a", {"class": "result__a"}, limit=max_results)
        for i, link in enumerate(results):
            title = link.get_text(strip=True)
            href = link["href"]
            text = fetch_page_text(href)
            docs.append({
                "title": title or f"Result {i+1}",
                "source": href,
                "text": text,
            })
    except Exception as e:
        docs.append({
            "title": "Search error",
            "source": "DuckDuckGo",
            "text": f"[Search error: {e}]"
        })
    return docs


def fetch_page_text(url: str, max_chars: int = 2000) -> str:
    """
    Fetch the visible text from a webpage (basic HTML cleaning).
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchAssistant/1.0)"}
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")

        # remove unwanted tags
        for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())[:max_chars]
    except Exception:
        return "[Could not fetch page text]"
