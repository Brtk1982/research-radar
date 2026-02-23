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
        "search_query": f"all:{topic} AND (cat:q-bio OR cat:cs.AI OR cat:stat.ML)",
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


def fetch_pubmed_papers(topic: str, max_results: int = 3) -> list[dict]:
    """
    Fetches papers from PubMed — the world's biggest medical research library.
    Run by the US National Library of Medicine. Completely free.
    """
    print(f"  📡 PubMed: searching for '{topic}'...")

    # Step 1: Search for paper IDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": f"{topic}[Title/Abstract] AND (\"last 30 days\"[PDat])",
        "retmax": max_results,
        "sort": "pub+date",
        "retmode": "json",
    }

    try:
        search_response = requests.get(search_url, params=search_params, timeout=15)
        search_response.raise_for_status()
        search_data = search_response.json()

        ids = search_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            print(f"     ℹ️  No recent PubMed papers for '{topic}'")
            return []

        # Step 2: Fetch details for those paper IDs
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
        }

        # Be polite to PubMed's servers — wait a moment between requests
        time.sleep(0.5)

        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=15)
        fetch_response.raise_for_status()

        root = ET.fromstring(fetch_response.content)
        papers = []

        for article in root.findall(".//PubmedArticle"):
            # Get the title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title"

            # Get the abstract (summary of the paper)
            abstract_texts = article.findall(".//AbstractText")
            abstract = " ".join([
                (t.text or "") for t in abstract_texts
            ]).strip()

            if not abstract:
                continue  # Skip papers with no abstract — not useful for us

            # Get the authors
            authors = []
            for author in article.findall(".//Author")[:3]:
                last = author.find("LastName")
                first = author.find("ForeName")
                if last is not None:
                    name = last.text
                    if first is not None:
                        name = f"{first.text} {name}"
                    authors.append(name)

            # Get the publication date
            pub_date = article.find(".//PubDate")
            year = pub_date.find("Year") if pub_date is not None else None
            month = pub_date.find("Month") if pub_date is not None else None
            date_str = ""
            if year is not None:
                date_str = year.text
                if month is not None:
                    date_str = f"{date_str}-{month.text}"

            # Get the PubMed link
            pmid = article.find(".//PMID")
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid.text}/" if pmid is not None else ""

            papers.append({
                "title": str(title).replace("\n", " "),
                "abstract": abstract[:2000],  # Cap at 2000 chars to save AI costs
                "authors": authors,
                "published": date_str,
                "url": url,
                "source": "PubMed",
                "topic": topic,
            })

        print(f"     ✅ Found {len(papers)} papers")
        return papers

    except Exception as e:
        print(f"     ⚠️  PubMed error for '{topic}': {e}")
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
        time.sleep(1)  # Be polite, don't hammer the servers
        pubmed_papers = fetch_pubmed_papers(topic, PAPERS_PER_TOPIC)
        time.sleep(1)

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
