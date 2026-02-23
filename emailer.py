# ============================================================
# MODULE 4: EMAIL DIGEST SENDER
# This takes all our investor briefs and packages them into
# a beautiful weekly email, then sends it to your subscribers.
# Uses Resend.com — simple, reliable, free up to 3,000 emails/month.
# ============================================================

import requests
from datetime import datetime

from config import (
    RESEND_API_KEY,
    FROM_EMAIL,
    FROM_NAME,
    SUBSCRIBERS,
    DIGEST_SUBJECT,
    MAX_PAPERS_IN_DIGEST,
)


def build_email_html(papers: list[dict]) -> str:
    """
    Builds the actual HTML email that subscribers receive.
    Think of this as designing the newsletter layout.
    """

    date_str = datetime.now().strftime("%B %d, %Y")
    paper_count = len(papers)

    # --- EMAIL HEADER ---
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Research Radar</title>
</head>
<body style="margin:0; padding:0; background:#0f0f0f; font-family: 'Georgia', serif; color:#e8e8e8;">

  <div style="max-width:640px; margin:0 auto; padding:40px 20px;">

    <!-- MASTHEAD -->
    <div style="border-bottom:1px solid #333; padding-bottom:30px; margin-bottom:40px;">
      <div style="font-size:11px; letter-spacing:3px; color:#888; text-transform:uppercase; margin-bottom:12px;">
        Longevity Intelligence
      </div>
      <h1 style="margin:0; font-size:32px; font-weight:normal; color:#ffffff; letter-spacing:-0.5px;">
        Research Radar
      </h1>
      <div style="margin-top:8px; font-size:13px; color:#666;">
        {date_str} · {paper_count} opportunity brief{"s" if paper_count != 1 else ""} this week
      </div>
    </div>

    <!-- INTRO -->
    <div style="margin-bottom:40px; padding:20px; background:#1a1a1a; border-left:3px solid #4a9eff; border-radius:4px;">
      <p style="margin:0; font-size:15px; line-height:1.6; color:#bbb; font-style:italic;">
        This week's radar swept <strong style="color:#e8e8e8;">arXiv and PubMed</strong> for longevity breakthroughs 
        with commercial potential. Only papers scoring 7/10 or higher on our commercial viability index 
        made the cut.
      </p>
    </div>
    """

    # --- PAPER BRIEFS ---
    for i, paper in enumerate(papers[:MAX_PAPERS_IN_DIGEST]):
        score = paper.get("score", 0)
        flag = paper.get("flag", "incremental").upper().replace("_", " ")

        # Color code by signal strength
        flag_color = "#ff6b6b" if flag == "BREAKTHROUGH" else "#ffd93d" if flag == "INCREMENTAL" else "#6bcb77"

        # Format the brief text as HTML (convert markdown bold to HTML)
        brief_html = paper.get("brief", "").replace("\n\n", "</p><p>").replace("**", "<strong>", 1)
        # Alternate replacing ** to close the strong tag
        while "**" in brief_html:
            brief_html = brief_html.replace("**", "</strong>", 1).replace("**", "<strong>", 1)

        html += f"""
    <!-- PAPER {i+1} -->
    <div style="margin-bottom:50px; padding-bottom:50px; border-bottom:1px solid #222;">
      
      <!-- Signal badge -->
      <div style="margin-bottom:12px;">
        <span style="font-size:10px; letter-spacing:2px; color:{flag_color}; text-transform:uppercase; 
                     background:{flag_color}22; padding:4px 10px; border-radius:20px; border:1px solid {flag_color}44;">
          {flag}
        </span>
        <span style="font-size:10px; color:#555; margin-left:10px; letter-spacing:1px;">
          #{i+1} OF {paper_count}
        </span>
      </div>

      <!-- Paper title -->
      <h2 style="margin:0 0 16px 0; font-size:19px; font-weight:normal; color:#ffffff; line-height:1.4;">
        <a href="{paper.get('url', '#')}" style="color:#ffffff; text-decoration:none;"
           onmouseover="this.style.color='#4a9eff'" onmouseout="this.style.color='#ffffff'">
          {paper['title']}
        </a>
      </h2>

      <!-- Meta info -->
      <div style="font-size:12px; color:#555; margin-bottom:20px; letter-spacing:0.5px;">
        {', '.join(paper.get('authors', ['Unknown']))} · 
        {paper.get('source', '')} · 
        {paper.get('published', '')}
      </div>

      <!-- The Brief -->
      <div style="font-size:15px; line-height:1.8; color:#cccccc;">
        <p>{brief_html}</p>
      </div>

      <!-- Read paper link -->
      <div style="margin-top:20px;">
        <a href="{paper.get('url', '#')}" 
           style="font-size:12px; color:#4a9eff; text-decoration:none; letter-spacing:1px; text-transform:uppercase;">
          Read full paper →
        </a>
      </div>

    </div>
    """

    # --- FOOTER ---
    html += """
    <!-- FOOTER -->
    <div style="padding-top:20px; border-top:1px solid #222; text-align:center;">
      <p style="font-size:12px; color:#444; line-height:1.6; margin:0 0 10px 0;">
        Research Radar is an AI-powered longevity intelligence digest.<br>
        Papers are scored and summarised automatically. Not financial advice.
      </p>
      <p style="font-size:11px; color:#333; margin:0;">
        You're receiving this because you subscribed to Research Radar.<br>
        <a href="#" style="color:#555; text-decoration:none;">Unsubscribe</a>
      </p>
    </div>

  </div>
</body>
</html>
    """

    return html


def send_digest(papers: list[dict]) -> bool:
    """
    Actually sends the email to all subscribers via Resend.
    Returns True if successful, False if something went wrong.
    """
    print("\n📧 STEP 4: SENDING EMAIL DIGEST")
    print("=" * 50)

    if not papers:
        print("  ℹ️  No papers to send. Skipping email.")
        return False

    if not SUBSCRIBERS:
        print("  ⚠️  No subscribers in config.py! Add some email addresses.")
        return False

    html_content = build_email_html(papers)

    # Resend API — simple HTTP request to send an email
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    success_count = 0
    fail_count = 0

    for subscriber in SUBSCRIBERS:
        payload = {
            "from": FROM_EMAIL,
            "to": [subscriber],
            "subject": DIGEST_SUBJECT,
            "html": html_content,
        }

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                print(f"  ✅ Sent to {subscriber}")
                success_count += 1
            else:
                print(f"  ❌ Failed for {subscriber}: {response.text}")
                fail_count += 1

        except Exception as e:
            print(f"  ❌ Error sending to {subscriber}: {e}")
            fail_count += 1

    print(f"\n  📊 Sent: {success_count} | Failed: {fail_count}")
    return success_count > 0


def save_digest_locally(papers: list[dict]):
    """
    Also saves the digest as an HTML file you can preview in your browser.
    Useful for checking how it looks before sending.
    """
    html = build_email_html(papers)
    filename = f"digest_preview_{datetime.now().strftime('%Y%m%d')}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  💾 Saved preview: {filename}")
    print(f"     Open this file in your browser to see exactly what subscribers get!")
