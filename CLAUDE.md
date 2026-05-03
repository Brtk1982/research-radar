# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Research Radar is a weekly AI intelligence digest service. It fetches recent papers from arXiv, scores them using Claude, and sends a curated HTML digest email to subscribers via Resend. It runs as a scheduled service deployed on Railway.

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Start the weekly scheduler (runs every Monday at 07:00 UTC)
python research_radar.py

# Dry-run: fetch + score + save HTML preview, no email sent
python research_radar.py preview

# One-shot: run the full pipeline including email delivery
python research_radar.py send
```

Requires a `.env` file with `ANTHROPIC_API_KEY` and `RESEND_API_KEY`.

## Architecture

Five-module pipeline, all coordinated by `research_radar.py`:

| Module | Role |
|---|---|
| `fetcher.py` | Queries arXiv API by topic, filters to AI/ML categories (cs.AI, cs.LG, cs.CL, cs.CV) |
| `scorer.py` | Sends each paper to Claude (Sonnet 4.6) for a 1–10 score + JSON brief |
| `emailer.py` | Builds the HTML digest and sends it via Resend; also writes a local HTML preview |
| `config.py` | Single source of truth for API keys, subscriber list, search topics, thresholds |
| `research_radar.py` | Orchestrates the pipeline; exposes the three run modes above |

### Key Config Values (`config.py`)

- `PAPERS_PER_TOPIC`: 3 — papers fetched per search topic per run
- `MIN_SCORE`: 7 — papers below this are dropped before briefing
- `MAX_PAPERS_IN_DIGEST`: 5 — cap on papers included in the email
- `SUBSCRIBERS`: currently `[wartek69@gmail.com]`
- From address: `Research Radar <radar@vita.arcanaveritas.io>`

### Scoring Criteria (in `scorer.py`)

Claude evaluates each paper on three axes: *Actually New* (novelty), *Solo-Buildable* (can one person build this?), and *Fringe/Weird* (originality). It returns JSON with `score`, `commercial_angle`, `target_market`, `urgency`, and `flag` (`breakthrough` / `interesting` / `incremental`). Papers scoring 7+ get a polished investor brief written in a second prompt.

## Deployment

Deployed on Railway via `railway.toml`. Start command is `python research_radar.py` (scheduler mode). Restart policy is `ON_FAILURE` with 3 retries. The `.env` file must not be committed — only `.env` is in `.gitignore`.
