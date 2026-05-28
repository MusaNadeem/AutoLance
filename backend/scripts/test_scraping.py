#!/usr/bin/env python3
"""
Live scraping integration test.
Fetches real Upwork jobs via Bright Data Unlocker API and prints results.

Run: cd backend && linux_venv/bin/python scripts/test_scraping.py
Credentials are auto-loaded from the project root .env file.

Takes 90-180 seconds per URL (Unlocker API rendering time).
"""
import os
import sys

# Load .env from project root
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env = os.path.join(_root, ".env")
if os.path.exists(_env):
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Minimal settings override so we can import the module without a full FastAPI setup
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("UPLOAD_DIR", "/tmp")

from app.scraping.bright_data import BrightDataClient

API_KEY = os.getenv("BRIGHT_DATA_API_KEY", "")
ZONE    = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "")

print("=" * 60)
print("AutoLance — Bright Data Scraping Test")
print("=" * 60)
print(f"API key: {API_KEY[:12]}...   Zone: {ZONE!r}")
print()

if not API_KEY or not ZONE:
    print("ERROR: BRIGHT_DATA_API_KEY and BRIGHT_DATA_UNLOCKER_ZONE must be set in .env")
    sys.exit(1)

client = BrightDataClient()

# Test with a single URL first
TEST_URL = "https://www.upwork.com/nx/search/jobs?q=python&sort=recency"
print(f"Fetching: {TEST_URL}")
print("(This takes 90-180 seconds — Bright Data is rendering the page...)")
print()

try:
    html = client._fetch_search_page(TEST_URL)
    print(f"HTML received: {len(html):,} bytes")
    jobs = client._parse_nuxt_html(html)
    print(f"Jobs parsed: {len(jobs)}")
    print()

    if not jobs:
        print("❌ No jobs found. Check if __NUXT__ is present in the HTML.")
        sys.exit(1)

    print("Sample jobs:")
    for j in jobs[:5]:
        print(f"\n  [{j['budget_type'].upper()}] {j['title'][:70]}")
        print(f"    ID: {j['upwork_job_id']}")
        print(f"    URL: {j['url']}")
        if j['budget_min']:  print(f"    Budget: ${j['budget_min']:.0f}")
        if j['hourly_rate_min']: print(f"    Hourly: ${j['hourly_rate_min']:.0f}-${j['hourly_rate_max'] or 0:.0f}/hr")
        if j['required_skills']:  print(f"    Skills: {', '.join(j['required_skills'][:4])}")
        if j['experience_level']: print(f"    Level: {j['experience_level']}")
        if j['project_length']:   print(f"    Duration: {j['project_length']}")
        if j['posted_at']:        print(f"    Posted: {j['posted_at']}")
        print(f"    Proposals: ~{j['proposal_count']}")

    print()
    with_titles = [j for j in jobs if j['title']]
    with_skills = [j for j in jobs if j['required_skills']]
    with_budget = [j for j in jobs if j['budget_min'] or j['hourly_rate_min']]
    with_posted = [j for j in jobs if j['posted_at']]

    print(f"✅ {len(jobs)} real Upwork jobs extracted")
    print(f"   With titles:   {len(with_titles)}/{len(jobs)}")
    print(f"   With skills:   {len(with_skills)}/{len(jobs)}")
    print(f"   With budget:   {len(with_budget)}/{len(jobs)}")
    print(f"   With posted_at:{len(with_posted)}/{len(jobs)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
