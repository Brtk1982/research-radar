# ============================================================
# MODULE 2 & 3: AI SCORING ENGINE + BRIEF WRITER
# This is where I (Claude AI) actually read each paper and decide:
# 1. Is this commercially interesting? (Score 1-10)
# 2. If yes — write a clean investor brief about it
#
# Think of this as having a really smart analyst who reads
# thousands of papers and only surfaces the gold.
# ============================================================

import anthropic
import json
import time

from config import ANTHROPIC_API_KEY, MIN_SCORE

# Connect to the Anthropic API (this is how we talk to Claude)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def score_paper(paper: dict) -> dict:
    """
    Asks Claude to read a paper's title and abstract and score it
    for commercial potential in longevity/biotech.
    Returns the paper with a score and reasoning added.
    """

    prompt = f"""You are my personal AI research filter. From everything you see, surface ONLY what meets these bars:

1. "Actually New" — novel research directions, new architectures, first-of-kind approaches. Must show hard evidence or genuine buzz. NOT incremental improvements on known methods.
2. "Solo-Buildable" — projects one person built, or techniques a solo developer could realistically implement. Cite the builder by name if known. Must show real traction: GitHub stars, users, community response.
3. "Fringe/Weird" — unconventional, strange, possibly impractical but genuinely original. Low metrics are fine here — originality beats popularity. The stuff nobody else is covering yet.

REJECT without mercy: incremental updates, big company PR, papers without code, anything requiring team-scale resources, anything already mainstream or widely covered.

NOVELTY TEST: Ask yourself — would a well-read AI practitioner already know this? If yes, reject it.

ITEM:
Title: {paper['title']}
Abstract: {paper['abstract']}
Source: {paper['source']}

Score this item from 1-10 using the bars above. Be ruthlessly selective.

Respond ONLY with valid JSON in this exact format:
{{
  "score": <number 1-10>,
  "commercial_angle": "<one sentence on what makes this genuinely interesting or important>",
  "target_market": "<what field or problem does this touch>",
  "urgency": "<why is this worth paying attention to now>",
  "flag": "<breakthrough|interesting|incremental>"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Clean up in case Claude adds markdown formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        scoring = json.loads(response_text)
        paper["score"] = scoring.get("score", 0)
        paper["commercial_angle"] = scoring.get("commercial_angle", "")
        paper["target_market"] = scoring.get("target_market", "")
        paper["urgency"] = scoring.get("urgency", "")
        paper["flag"] = scoring.get("flag", "incremental")

        return paper

    except Exception as e:
        print(f"     ⚠️  Scoring error: {e}")
        paper["score"] = 0
        return paper


def write_investor_brief(paper: dict) -> str:
    """
    For papers that scored above our threshold, write a polished
    investor-ready opportunity brief. This is the actual product
    our subscribers receive.
    """

    prompt = f"""You are my personal AI research filter writing a weekly digest. Your reader is a solo builder who wants to know about the coolest new things happening in AI — tools, projects, research, and solo builds worth paying attention to. He builds things. He doesn't care about theory for its own sake.

ITEM DATA:
Title: {paper['title']}
Description: {paper['abstract']}
Builders: {', '.join(paper.get('authors', []))}
Published: {paper.get('published', 'Recent')}
Source: {paper['source']}
Why interesting: {paper['commercial_angle']}
Field/problem: {paper['target_market']}
Why now: {paper['urgency']}

Write the brief in this EXACT structure (use these exact headers):

**WHAT IT IS**
[2-3 sentences. What did someone build, ship, or discover? Plain language. What does it actually do or show?]

**WHY IT'S INTERESTING**
[2-3 sentences. What's genuinely new or surprising? What does it change or make possible?]

**WORTH WATCHING BECAUSE**
[1-2 sentences. What's the signal — traction, novelty, strangeness — that makes this stand out from the noise?]

**SIGNAL STRENGTH:** {paper['flag'].upper().replace('_', ' ')} | Score: {paper['score']}/10

Keep the entire brief under 200 words. Write like you're telling a builder friend about something cool you found. Honest and direct — if it's only mildly interesting, say so."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text.strip()

    except Exception as e:
        print(f"     ⚠️  Brief writing error: {e}")
        return f"Brief unavailable for: {paper['title']}"


def score_and_brief_papers(papers: list[dict]) -> list[dict]:
    """
    The full pipeline: score every paper, then write briefs for the winners.
    """
    print("\n🧠 STEP 2: AI SCORING ENGINE")
    print("=" * 50)
    print(f"Reading and scoring {len(papers)} papers...\n")

    scored_papers = []

    for i, paper in enumerate(papers):
        print(f"  [{i+1}/{len(papers)}] {paper['title'][:60]}...")

        # Score this paper
        paper = score_paper(paper)
        score = paper.get("score", 0)

        if score >= MIN_SCORE:
            print(f"     🌟 Score: {score}/10 — SELECTED!")
        else:
            print(f"     Score: {score}/10 — filtered out")

        scored_papers.append(paper)
        time.sleep(0.5)  # Small pause to be kind to the API

    # Filter to only high-scoring papers
    winners = [p for p in scored_papers if p.get("score", 0) >= MIN_SCORE]
    winners.sort(key=lambda x: x.get("score", 0), reverse=True)  # Best first

    print(f"\n✅ {len(winners)} papers made the cut (scored {MIN_SCORE}+/10)")

    # Now write investor briefs for the winners
    print("\n✍️  STEP 3: WRITING INVESTOR BRIEFS")
    print("=" * 50)

    for i, paper in enumerate(winners):
        print(f"  Writing brief {i+1}/{len(winners)}: {paper['title'][:50]}...")
        paper["brief"] = write_investor_brief(paper)
        time.sleep(1)  # Pause between API calls

    return winners


if __name__ == "__main__":
    # Test with a fake paper to make sure everything connects
    test_paper = {
        "title": "Partial epigenetic reprogramming extends healthspan in aged mice",
        "abstract": "We demonstrate that transient expression of Yamanaka factors using a controlled delivery system reverses epigenetic aging markers in aged mouse tissue, resulting in 25% extension of remaining healthspan without tumor formation. The approach uses a novel lipid nanoparticle delivery mechanism compatible with systemic administration.",
        "source": "arXiv",
        "authors": ["J. Smith", "A. Johnson"],
        "published": "2024-01",
        "url": "https://arxiv.org/example",
        "topic": "epigenetic reprogramming",
    }

    result = score_paper(test_paper)
    print(f"\nTest Score: {result['score']}/10")
    print(f"Commercial Angle: {result['commercial_angle']}")

    if result["score"] >= MIN_SCORE:
        brief = write_investor_brief(result)
        print(f"\nInvestor Brief:\n{brief}")
