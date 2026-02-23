# ============================================================
# MAIN ORCHESTRATOR — research_radar.py
# This is the conductor. It coordinates all the other modules.
# Run this file manually to trigger a full cycle,
# OR let Railway.app run it automatically every week.
#
# The whole pipeline in plain English:
# 1. Wake up every Monday morning
# 2. Fetch fresh longevity papers
# 3. Score each paper with AI
# 4. Write investor briefs for the best ones
# 5. Email digest to subscribers
# 6. Go back to sleep
# ============================================================

import schedule
import time
import logging
from datetime import datetime

from fetcher import fetch_all_papers
from scorer import score_and_brief_papers
from emailer import send_digest, save_digest_locally
from config import MAX_PAPERS_IN_DIGEST

# Set up logging — this creates a log file so you can see what happened
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(message)s",
    handlers=[
        logging.FileHandler("research_radar.log"),
        logging.StreamHandler()  # Also print to screen
    ]
)


def run_full_pipeline(preview_only: bool = False):
    """
    Runs the complete Research Radar pipeline from start to finish.
    
    preview_only=True : fetches and scores papers, saves HTML, but DOESN'T email
    preview_only=False : full run including sending to subscribers
    """
    
    print("\n" + "🧬" * 25)
    print("  RESEARCH RADAR — STARTING PIPELINE")
    print(f"  {datetime.now().strftime('%A, %B %d %Y at %H:%M')}")
    print("🧬" * 25 + "\n")
    
    start_time = datetime.now()
    
    try:
        # ── STEP 1: FETCH PAPERS ──────────────────────────────
        papers = fetch_all_papers()
        
        if not papers:
            print("⚠️  No papers fetched. Check internet connection.")
            return
        
        # ── STEP 2 & 3: SCORE + WRITE BRIEFS ─────────────────
        winning_papers = score_and_brief_papers(papers)
        
        if not winning_papers:
            print("⚠️  No papers passed the scoring threshold this week.")
            print("   Consider lowering MIN_SCORE in config.py temporarily.")
            return
        
        # Limit to max papers per digest
        final_papers = winning_papers[:MAX_PAPERS_IN_DIGEST]
        
        print(f"\n🏆 FINAL DIGEST: {len(final_papers)} papers selected")
        for i, p in enumerate(final_papers):
            print(f"   {i+1}. [{p['score']}/10] {p['title'][:65]}...")
        
        # ── STEP 4: SAVE PREVIEW ──────────────────────────────
        save_digest_locally(final_papers)
        
        # ── STEP 5: SEND EMAIL ────────────────────────────────
        if preview_only:
            print("\n👀 PREVIEW MODE — Email NOT sent. Check the HTML file!")
        else:
            send_digest(final_papers)
        
        # ── DONE ──────────────────────────────────────────────
        elapsed = (datetime.now() - start_time).seconds
        print(f"\n✅ PIPELINE COMPLETE in {elapsed}s")
        print(f"   Papers fetched: {len(papers)}")
        print(f"   Papers selected: {len(final_papers)}")
        print("🧬" * 25 + "\n")
        
    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {e}")
        logging.error(f"Pipeline failed: {e}", exc_info=True)


def run_scheduler():
    """
    Sets up the automatic weekly schedule.
    Every Monday at 7:00 AM — pipeline runs automatically.
    """
    print("⏰ Research Radar scheduler started...")
    print("   Will run every Monday at 07:00")
    print("   Ctrl+C to stop\n")
    
    # Schedule the job — every Monday at 7am
    schedule.every().monday.at("07:00").do(run_full_pipeline, preview_only=False)
    
    # Keep running and check the schedule every minute
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every 60 seconds


# ============================================================
# COMMAND LINE INTERFACE
# How to use this file:
#
#   python research_radar.py           → runs scheduler (automated mode)
#   python research_radar.py preview   → one-time run, no email sent
#   python research_radar.py send      → one-time run, emails ARE sent
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "preview":
            print("🔍 Running in PREVIEW mode (no email will be sent)")
            run_full_pipeline(preview_only=True)
            
        elif mode == "send":
            print("📧 Running in SEND mode (will email subscribers)")
            run_full_pipeline(preview_only=False)
            
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python research_radar.py [preview|send]")
    
    else:
        # No argument = run the scheduler for automated weekly emails
        run_scheduler()
