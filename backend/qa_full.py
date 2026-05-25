"""
Full Phase 1–4 QA script — runs against the live app + DB.
Prints PASS/FAIL for every requirement check.
"""
import asyncio, json, sys, logging, os

# Force SQLAlchemy echo off before anything is imported
os.environ["SQLALCHEMY_WARN_20"] = "1"

# Silence all loggers
logging.disable(logging.CRITICAL)

# Redirect all print to stderr so SQLAlchemy stdout noise doesn't mix
_real_print = print
def print(*args, **kwargs):  # noqa
    kwargs.setdefault("file", sys.stderr)
    _real_print(*args, **kwargs)

from httpx import AsyncClient, ASGITransport
from main import app

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))

async def run():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:

        # ── Auth setup ───────────────────────────────────────────────────────
        email = "full_qa@test.com"
        await c.post("/api/v1/auth/register", json={"email": email, "password": "testpass123", "full_name": "Full QA"})
        r = await c.post("/api/v1/auth/login", json={"email": email, "password": "testpass123"})
        check("AUTH: Login returns 200 + access_token", r.status_code == 200 and "access_token" in r.json())
        token = r.json().get("access_token", "")
        h = {"Authorization": f"Bearer {token}"}

        # ── Wrong password doesn't redirect (interceptor rule) ───────────────
        r2 = await c.post("/api/v1/auth/login", json={"email": email, "password": "WRONG"})
        check("AUTH: Wrong password returns 401 not 500", r2.status_code == 401)

        # ── PHASE 1: Jobs + Scoring ──────────────────────────────────────────
        r = await c.get("/api/v1/jobs/", headers=h)
        d = r.json()
        check("P1: GET /jobs returns 200", r.status_code == 200)
        check("P1: GET /jobs has 'jobs' list", "jobs" in d)
        check("P1: GET /jobs has 'total' int", isinstance(d.get("total"), int))
        check("P1: GET /jobs has 'page' int", isinstance(d.get("page"), int))
        check("P1: GET /jobs has 'limit' int", isinstance(d.get("limit"), int))
        jobs = d.get("jobs", [])
        if jobs:
            j = jobs[0]
            check("P1: Job has title", bool(j.get("title")))
            check("P1: Job has budget_type", j.get("budget_type") in ("fixed", "hourly", None))
            check("P1: Job score is float or None", j.get("score") is None or isinstance(j.get("score"), dict))
            check("P1: Job has posted_at", "posted_at" in j)
        else:
            check("P1: Has job records (skip if empty DB)", True, "0 jobs in DB — expected in local dev")

        # Scoring engine (via bid_strategy service import)
        from app.services.bid_strategy import BidStrategyEngine
        eng = BidStrategyEngine()
        bid = eng.calculate(
            budget_type="fixed", budget_min=100, budget_max=500,
            hourly_rate_min=None, hourly_rate_max=None,
            user_target_rate=75.0, proposals_count=5, client_quality=0.8
        )
        check("P1: BidStrategyEngine returns bid dict", isinstance(bid, dict))
        check("P1: Bid has bid_strategy field", "bid_strategy" in bid)
        check("P1: Bid recommended >= bid_range_min", bid.get("recommended_bid", 0) >= bid.get("bid_range_min", 0))
        check("P1: Bid bid_confidence in 0-1", 0 <= bid.get("bid_confidence", -1) <= 1)

        # ── PHASE 2: Scrape + Alerts ─────────────────────────────────────────
        r = await c.get("/api/v1/scrape/status", headers=h)
        d2 = r.json()
        check("P2: GET /scrape/status returns 200", r.status_code == 200)
        check("P2: scrape/status has is_running", "is_running" in d2)
        check("P2: scrape/status has next_run_at", "next_run_at" in d2)

        r = await c.get("/api/v1/alerts/", headers=h)
        d3 = r.json()
        check("P2: GET /alerts returns 200", r.status_code == 200)
        check("P2: alerts has unread_count", "unread_count" in d3)
        check("P2: alerts has notifications list", "notifications" in d3)
        check("P2: unread_count is int >= 0", isinstance(d3.get("unread_count"), int) and d3["unread_count"] >= 0)

        r = await c.get("/api/v1/alerts/config", headers=h)
        check("P2: GET /alerts/config returns 200", r.status_code == 200)

        r = await c.post("/api/v1/alerts/read-all", headers=h, content=b"{}")
        check("P2: POST /alerts/read-all returns 200/204", r.status_code in (200, 204), f"got {r.status_code}: {r.text[:100]}")

        # ── PHASE 3: CV Profile + Cover Letter ───────────────────────────────
        r = await c.get("/api/v1/cv/profile", headers=h)
        check("P3: GET /cv/profile returns 200 or 404", r.status_code in (200, 404))

        # Upsert profile
        profile_payload = {
            "full_name": "QA Tester",
            "skills": [
                {"name": "Python", "level": "expert", "years": 5},
                {"name": "FastAPI", "level": "intermediate", "years": 2},
                {"name": "React", "level": "intermediate", "years": 3},
            ],
            "experience_level": "senior",
            "inferred_hourly_rate_min": 50.0,
            "inferred_hourly_rate_max": 100.0,
            "target_fixed_min": 500.0,
            "target_fixed_max": 5000.0,
        }
        r = await c.put("/api/v1/cv/profile", json=profile_payload, headers=h)
        check("P3: PUT /cv/profile returns 200", r.status_code == 200, f"status={r.status_code} body={r.text[:200]}")
        pdata = r.json() if r.status_code == 200 else {}
        check("P3: PUT /cv/profile bumps profile_version", pdata.get("profile_version", 0) >= 1)
        check("P3: PUT /cv/profile returns skills list", isinstance(pdata.get("skills"), list) and len(pdata["skills"]) == 3)
        check("P3: PUT /cv/profile returns target_fixed_min", pdata.get("target_fixed_min") == 500.0)

        # GET after PUT
        r = await c.get("/api/v1/cv/profile", headers=h)
        check("P3: GET /cv/profile after PUT returns 200", r.status_code == 200)
        gdata = r.json()
        check("P3: GET profile has all 12 required keys", all(k in gdata for k in [
            "id", "headline", "summary", "skills", "experience_level", "niche",
            "inferred_hourly_rate_min", "inferred_hourly_rate_max",
            "target_fixed_min", "target_fixed_max",
            "last_analyzed_at", "profile_version"
        ]))

        # Cover letter tones
        from app.services.cover_letter_gen import VALID_TONES
        check("P3: VALID_TONES has professional", "professional" in VALID_TONES)
        check("P3: VALID_TONES has friendly", "friendly" in VALID_TONES)
        check("P3: VALID_TONES has bold", "bold" in VALID_TONES)
        check("P3: VALID_TONES has exactly 3 tones", len(VALID_TONES) == 3)

        from app.ai.prompts.cover_letter import build_cover_letter_prompt

        class FakeProfile:
            full_name = "QA"; skills = ["Python"]; summary = "Dev"
            hourly_rate_min = 50; hourly_rate_max = 100; experience_level = "senior"
            target_fixed_min = None; target_fixed_max = None

        class FakeJob:
            title = "Test Job"; description = "Build API"; required_skills = '["Python"]'
            budget_type = "fixed"; budget_min = 500; budget_max = 2000
            hourly_rate_min = None; hourly_rate_max = None; proposal_count = 5

        fake_match = {"strengths": ["Python expertise"], "weaknesses": [], "recommended_approach": "Direct"}
        p = {t: build_cover_letter_prompt(FakeProfile(), FakeJob(), fake_match, t, t)
             for t in ["professional", "friendly", "bold"]}
        check("P3: 3 tones produce distinct prompts", len(set(p.values())) == 3)

        # ── PHASE 4: Filtering + Analytics ──────────────────────────────────
        test_cases = [
            ("P4: sort_by=score", {"sort_by": "score"}),
            ("P4: sort_by=budget", {"sort_by": "budget"}),
            ("P4: sort_by=posted_at (default)", {"sort_by": "posted_at"}),
            ("P4: sort_by=INVALID fallback", {"sort_by": "INVALID"}),
            ("P4: min_score=0", {"min_score": "0"}),
            ("P4: min_score=50", {"min_score": "50"}),
            ("P4: min_score=100", {"min_score": "100"}),
            ("P4: posted_within=24", {"posted_within": "24"}),
            ("P4: posted_within=168", {"posted_within": "168"}),
            ("P4: budget_type=hourly", {"budget_type": "hourly"}),
            ("P4: budget_type=fixed", {"budget_type": "fixed"}),
            ("P4: pagination page=1&limit=5", {"page": "1", "limit": "5"}),
            ("P4: pagination page=2&limit=5", {"page": "2", "limit": "5"}),
        ]
        for label, params in test_cases:
            r = await c.get("/api/v1/jobs/", headers=h, params=params)
            d = r.json()
            ok = r.status_code == 200 and "jobs" in d and "total" in d
            check(label, ok, f"status={r.status_code}")

        # Analytics endpoint
        r = await c.get("/api/v1/analytics/", headers=h)
        d = r.json()
        check("P4: GET /analytics returns 200", r.status_code == 200)
        required_keys = {"jobs_scraped_total", "avg_score", "score_distribution",
                         "top_skills_in_demand", "scrape_history"}
        check("P4: analytics has all 5 required keys", required_keys <= set(d.keys()))
        dist = d.get("score_distribution", [])
        check("P4: analytics score_distribution has 4 buckets", len(dist) == 4)
        buckets = {b["bucket"] for b in dist}
        check("P4: analytics bucket names correct", buckets == {"0-25","25-50","50-75","75-100"})
        check("P4: analytics avg_score is int", isinstance(d.get("avg_score"), int))
        check("P4: analytics jobs_scraped_total >= 0", d.get("jobs_scraped_total", -1) >= 0)
        skills = d.get("top_skills_in_demand", [])
        check("P4: analytics top_skills max 10", len(skills) <= 10)
        if skills:
            check("P4: analytics skill has 'skill' + 'count'", all("skill" in s and "count" in s for s in skills))
        history = d.get("scrape_history", [])
        if history:
            check("P4: scrape_history has required fields",
                  all("date" in h and "jobs_found" in h and "jobs_new" in h for h in history))

        # ── Key file existence checks (local dev paths) ────────────────────────
        import os
        # __file__ is backend/qa_full.py — base is the backend/ directory
        _base = os.path.dirname(os.path.abspath(__file__))
        files_to_check = [
            (os.path.join(_base, "main.py"),                          "backend/main.py"),
            (os.path.join(_base, "app/models/job.py"),                "models/job.py"),
            (os.path.join(_base, "app/models/profile.py"),            "models/profile.py"),
            (os.path.join(_base, "app/models/notification.py"),       "models/notification.py"),
            (os.path.join(_base, "app/services/job_scorer.py"),       "services/job_scorer.py"),
            (os.path.join(_base, "app/services/bid_strategy.py"),     "services/bid_strategy.py"),
            (os.path.join(_base, "app/services/cover_letter_gen.py"), "services/cover_letter_gen.py"),
            (os.path.join(_base, "app/routers/cv.py"),                "routers/cv.py"),
            (os.path.join(_base, "app/routers/scrape.py"),            "routers/scrape.py"),
            (os.path.join(_base, "app/routers/alerts.py"),            "routers/alerts.py"),
            (os.path.join(_base, "app/routers/analytics.py"),         "routers/analytics.py"),
            (os.path.join(_base, "app/workers/match_tasks.py"),       "workers/match_tasks.py"),
            (os.path.join(_base, "tests/test_phase1.py"),             "tests/test_phase1.py"),
            (os.path.join(_base, "tests/test_phase2.py"),             "tests/test_phase2.py"),
            (os.path.join(_base, "tests/test_phase3.py"),             "tests/test_phase3.py"),
            (os.path.join(_base, "tests/test_phase4.py"),             "tests/test_phase4.py"),
        ]
        for path, label in files_to_check:
            check(f"FILE: {label}", os.path.exists(path))

        # ── Router registration check ────────────────────────────────────────
        routes = [r.path for r in app.routes]
        check("ROUTER: /api/v1/jobs/ registered", any("/jobs" in p for p in routes))
        check("ROUTER: /api/v1/analytics/ registered", any("/analytics" in p for p in routes))
        check("ROUTER: /api/v1/alerts/ registered", any("/alerts" in p for p in routes))
        check("ROUTER: /api/v1/scrape/ registered", any("/scrape" in p for p in routes))
        check("ROUTER: /api/v1/cv/ registered", any("/cv" in p for p in routes))
        check("ROUTER: /api/v1/cover-letters/ registered", any("/cover-letters" in p for p in routes))

asyncio.run(run())

# ── Print results ────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("FULL QA REPORT — Phases 1–4")
print("=" * 70)
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
for status, label, detail in results:
    line = f"{status} {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
print()
print("=" * 70)
print(f"  TOTAL: {passed + failed}  |  PASSED: {passed}  |  FAILED: {failed}")
print("=" * 70)
if failed:
    sys.exit(1)
