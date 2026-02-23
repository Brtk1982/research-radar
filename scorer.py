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

    prompt = f"""You are a longevity biotech analyst advising venture capital investors.
    
Evaluate this academic paper for COMMERCIAL POTENTIAL. Be ruthlessly selective.

PAPER:
Title: {paper['title']}
Abstract: {paper['abstract']}
Source: {paper['source']}

Score this paper from 1-10 on commercial potential using these criteria:
- 8-10: Breakthrough finding with clear near-term product pathway, large market
- 6-7: Interesting finding, possible commercial angle but less direct
- 4-5: Scientifically valid but limited commercial relevance
- 1-3: Purely academic, no commercial angle

Respond ONLY with valid JSON in this exact format:
{{
  "score": <number 1-10>,
  "commercial_angle": "<one sentence on what the product/application could be>",
  "target_market": "<who would pay for this>",
  "urgency": "<why now — what makes this timely>",
  "flag": "<breakthrough|incremental|basic_science>"
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

    prompt = f"""You are writing for Research Radar, a premium intelligence digest read by longevity-focused VCs and angel investors. 

Write a sharp, insightful opportunity brief for this paper. Your readers are smart, time-poor investors who need signal, not noise.

PAPER DATA:
Title: {paper['title']}
Abstract: {paper['abstract']}
Authors: {', '.join(paper.get('authors', []))}
Published: {paper.get('published', 'Recent')}
Source: {paper['source']}
Commercial Angle: {paper['commercial_angle']}
Target Market: {paper['target_market']}
Urgency: {paper['urgency']}

Write the brief in this EXACT structure (use these exact headers):

**THE FINDING**
[2-3 sentences. What did they discover? Write as if explaining to a smart non-scientist. No jargon.]

**WHY IT MATTERS COMMERCIALLY**
[2-3 sentences. What product or service could this enable? What industry does it disrupt or create?]

**THE OPPORTUNITY WINDOW**
[1-2 sentences. Why is now the time? What's the competitive landscape?]

**WHO'S WATCHING**
[1-2 sentences. Which type of investors or corporates should pay attention?]

**SIGNAL STRENGTH:** {paper['flag'].upper().replace('_', ' ')} | Score: {paper['score']}/10

Keep the entire brief under 250 words. Be direct. No fluff. Sound like an insider, not a press release."""

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
