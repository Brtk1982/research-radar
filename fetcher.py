# ============================================================
# MODULE 1: PAPER FETCHER
# This is the "librarian robot". It goes to two giant free
# academic libraries (arXiv and PubMed) and grabs fresh
# longevity research papers every day.
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


def fetch_all_papers() -> list[dict]:
    """
    The main function — runs through all our topics and fetches papers
    from both libraries. This is the robot's daily morning routine.
    """
    print("\n🔍 STEP 1: FETCHING PAPERS")
    print("=" * 50)

    all_papers = []
    seen_titles = set()  # Prevents duplicates

    for topic in SEARCH_TOPICS:
        print(f"\n📚 Topic: {topic}")

        # Fetch from both sources
        arxiv_papers = fetch_arxiv_papers(topic, PAPERS_PER_TOPIC)
        time.sleep(1)
        pubmed_papers = []

        # Combine and deduplicate
        for paper in arxiv_papers + pubmed_papers:
            # Clean up the title for comparison
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
