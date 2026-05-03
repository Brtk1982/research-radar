# ============================================================
# MODULE 1: PAPER FETCHER
# Fetches recent AI/ML content from arXiv, GitHub Trending,
# and Hugging Face Spaces.
# ============================================================

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time

from config import SEARCH_TOPICS, PAPERS_PER_TOPIC


def fetch_arxiv_papers(topic: str, max_results: int = 3) -> list[dict]:
    """
    Fetches papers from arXiv — a free science library run by Cornell University.
    It's completely open, no account needed.
    """
    print(f"  📡 arXiv: searching for '{topic}'...")

    # Build the web address we're searching (like typing into a search bar)
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{topic} AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV)",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()

        # Parse the XML response (arXiv sends data in a special format called XML)
        root = ET.fromstring(response.content)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}

        papers = []
        for entry in root.findall("atom:entry", namespace):
            # Extract the important bits from each paper
            title = entry.find("atom:title", namespace)
            summary = entry.find("atom:summary", namespace)
            published = entry.find("atom:published", namespace)
            link = entry.find("atom:id", namespace)

            authors = []
            for author in entry.findall("atom:author", namespace):
                name = author.find("atom:name", namespace)
                if name is not None:
                    authors.append(name.text.strip())

            if title is not None and summary is not None:
                papers.append({
                    "title": title.text.strip().replace("\n", " "),
                    "abstract": summary.text.strip().replace("\n", " "),
                    "authors": authors[:3],  # First 3 authors
                    "published": published.text[:10] if published is not None else "Unknown",
                    "url": link.text.strip() if link is not None else "",
                    "source": "arXiv",
                    "topic": topic,
                })

        print(f"     ✅ Found {len(papers)} papers")
        return papers

    except Exception as e:
        print(f"     ⚠️  arXiv error for '{topic}': {e}")
        return []


def fetch_github_trending(topic: str, max_results: int = 3) -> list[dict]:
    """
    Fetches recently created AI/ML repositories from GitHub Search API,
    filtered to repos created in the last 7 days and sorted by stars.
    Uses unauthenticated API (60 req/hr limit — fine for weekly runs).
    """
    print(f"  📡 GitHub: searching for '{topic}'...")

    since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    query = f"{topic} in:name,description,topics created:>{since} stars:>1"

    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    }
    headers = {"Accept": "application/vnd.github+json"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for repo in data.get("items", [])[:max_results]:
            papers.append({
                "title": repo["full_name"],
                "abstract": repo.get("description") or "No description provided.",
                "authors": [repo["owner"]["login"]],
                "published": repo["created_at"][:10],
                "url": repo["html_url"],
                "source": "GitHub",
                "topic": topic,
            })

        print(f"     ✅ Found {len(papers)} repos")
        return papers

    except Exception as e:
        print(f"     ⚠️  GitHub error for '{topic}': {e}")
        return []


def fetch_huggingface_spaces(max_results: int = 5) -> list[dict]:
    """
    Fetches popular Hugging Face Spaces from the public HF API.
    Not topic-specific — returns the globally top spaces.
    Tries sort=likes first, falls back to sort=createdAt.
    """
    print(f"  📡 Hugging Face: fetching trending spaces...")

    url = "https://huggingface.co/api/spaces"
    base_params = {"limit": max_results, "full": "true"}

    spaces = None
    for sort_value in ("createdAt", "likes"):
        try:
            response = requests.get(url, params={**base_params, "sort": sort_value}, timeout=15)
            response.raise_for_status()
            spaces = response.json()
            break
        except Exception:
            continue

    if spaces is None:
        print(f"     ⚠️  Hugging Face error: all sort strategies failed")
        return []

    papers = []
    for space in spaces[:max_results]:
        space_id = space.get("id", "")
        card = space.get("cardData") or {}
        tags = space.get("tags") or []

        description = (
            card.get("short_description")
            or card.get("title")
            or (", ".join(tags[:5]) if tags else "No description.")
        )

        author = space_id.split("/")[0] if "/" in space_id else space_id
        created = (space.get("createdAt") or "")[:10] or datetime.utcnow().strftime("%Y-%m-%d")

        papers.append({
            "title": space_id,
            "abstract": description,
            "authors": [author],
            "published": created,
            "url": f"https://huggingface.co/spaces/{space_id}",
            "source": "Hugging Face",
            "topic": "AI Tools",
        })

    print(f"     ✅ Found {len(papers)} spaces")
    return papers


def fetch_all_papers() -> list[dict]:
    """
    The main function — runs through all topics fetching from arXiv and GitHub,
    then appends trending Hugging Face Spaces (fetched once, not per topic).
    """
    print("\n🔍 STEP 1: FETCHING PAPERS")
    print("=" * 50)

    all_papers = []
    seen_titles = set()  # Prevents duplicates

    for topic in SEARCH_TOPICS:
        print(f"\n📚 Topic: {topic}")

        arxiv_papers = fetch_arxiv_papers(topic, PAPERS_PER_TOPIC)
        time.sleep(1)
        github_papers = fetch_github_trending(topic, PAPERS_PER_TOPIC)
        time.sleep(6)

        for paper in arxiv_papers + github_papers:
            clean_title = paper["title"].lower()[:50]
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                all_papers.append(paper)

    print(f"\n📚 Hugging Face Spaces (trending)")
    hf_papers = fetch_huggingface_spaces(PAPERS_PER_TOPIC)
    for paper in hf_papers:
        clean_title = paper["title"].lower()[:50]
        if clean_title not in seen_titles:
            seen_titles.add(clean_title)
            all_papers.append(paper)

    print(f"\n✅ Total unique papers fetched: {len(all_papers)}")
    return all_papers


if __name__ == "__main__":
    # Run this file directly to test the fetcher on its own
    papers = fetch_all_papers()
    print(f"\nSample paper:")
    if papers:
        p = papers[0]
        print(f"Title: {p['title']}")
        print(f"Source: {p['source']}")
        print(f"URL: {p['url']}")
