# ============================================================
# RESEARCH RADAR — CONFIG FILE
# This is where you put your secret keys and preferences.
# Think of it like a settings menu for the whole system.
# ============================================================

import os

# --- YOUR API KEYS ---
# Get these from the websites mentioned in setup.
# Never share this file with anyone!

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-key-here")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "your-resend-key-here")

# --- EMAIL SETTINGS ---
# The "from" address for your weekly digest
FROM_EMAIL = "Research Radar <onboarding@resend.dev>"
FROM_NAME = "Research Radar"

# --- YOUR SUBSCRIBER LIST ---
# Add email addresses of your subscribers here.
# Later we'll connect this to a proper database, but this works to start.
SUBSCRIBERS = [
    "wartek69@gmail.com",
    # Add more emails below this line, same format
]

# --- WHAT WE'RE HUNTING FOR ---
# These are the search terms we use to find longevity papers.
# Think of these as the words we type into the academic search engine.
SEARCH_TOPICS = [
    "longevity",
    "aging reversal",
    "senolytics",
    "telomere extension",
    "NAD+ metabolism",
    "epigenetic reprogramming",
    "mTOR inhibition aging",
    "autophagy aging",
    "healthspan extension",
    "lifespan biomarkers",
]

# --- HOW MANY PAPERS TO FETCH ---
# Each day, how many papers should we pull in per search topic?
# Start small (3) and increase once everything is working.
PAPERS_PER_TOPIC = 3

# --- SCORING THRESHOLD ---
# Papers get scored 1-10 for commercial potential.
# Only papers scoring ABOVE this number make it into the digest.
# 7 = high bar (fewer papers, higher quality)
MIN_SCORE = 7

# --- DIGEST SETTINGS ---
DIGEST_SUBJECT = "Research Radar: This Week's Longevity Opportunities 🧬"
MAX_PAPERS_IN_DIGEST = 5  # Maximum papers per weekly email
