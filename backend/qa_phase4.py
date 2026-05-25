import asyncio, json
from httpx import AsyncClient, ASGITransport
from main import app

async def qa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register (may already exist)
        await client.post("/api/v1/auth/register", json={
            "email": "qa_phase4@test.com", "password": "testpass123", "full_name": "QA Tester"
        })
        # Login
        r = await client.post("/api/v1/auth/login", json={
            "email": "qa_phase4@test.com", "password": "testpass123"
        })
        if r.status_code != 200:
            print("LOGIN FAILED:", r.text)
            return
        token = r.json()["access_token"]
        headers = {"Authorization": "Bearer " + token}

        tests = [
            ("GET /jobs default", "/api/v1/jobs/", {}),
            ("GET /jobs sort_by=score", "/api/v1/jobs/", {"sort_by": "score"}),
            ("GET /jobs sort_by=budget", "/api/v1/jobs/", {"sort_by": "budget"}),
            ("GET /jobs min_score=70", "/api/v1/jobs/", {"min_score": "70"}),
            ("GET /jobs min_score=0", "/api/v1/jobs/", {"min_score": "0"}),
            ("GET /jobs posted_within=24", "/api/v1/jobs/", {"posted_within": "24"}),
            ("GET /jobs posted_within=1", "/api/v1/jobs/", {"posted_within": "1"}),
            ("GET /jobs budget_type=hourly", "/api/v1/jobs/", {"budget_type": "hourly"}),
            ("GET /jobs budget_type=fixed", "/api/v1/jobs/", {"budget_type": "fixed"}),
            ("GET /jobs sort_by=INVALID", "/api/v1/jobs/", {"sort_by": "INVALID"}),
            ("GET /jobs page=2", "/api/v1/jobs/", {"page": "2", "limit": "5"}),
        ]

        print("\n" + "="*60)
        print("PHASE 4 QA — GET /jobs filter params")
        print("="*60)
        for label, url, params in tests:
            r = await client.get(url, headers=headers, params=params)
            d = r.json()
            total = d.get("total", "N/A")
            count = len(d.get("jobs", []))
            status_str = "PASS" if r.status_code == 200 else "FAIL"
            print(f"[{status_str}] {label}")
            print(f"       status={r.status_code}, total={total}, returned={count}")

        print("\n" + "="*60)
        print("PHASE 4 QA — GET /analytics")
        print("="*60)
        r = await client.get("/api/v1/analytics/", headers=headers)
        d = r.json()
        status_str = "PASS" if r.status_code == 200 else "FAIL"
        print(f"[{status_str}] Status: {r.status_code}")
        
        required_keys = {"jobs_scraped_total", "avg_score", "score_distribution", "top_skills_in_demand", "scrape_history"}
        missing = required_keys - set(d.keys())
        print(f"[{'PASS' if not missing else 'FAIL'}] All required keys present: {not bool(missing)}")
        if missing:
            print(f"       MISSING: {missing}")

        dist = d.get("score_distribution", [])
        buckets = {b["bucket"] for b in dist}
        expected_buckets = {"0-25", "25-50", "50-75", "75-100"}
        print(f"[{'PASS' if buckets == expected_buckets else 'FAIL'}] 4 score buckets present: {buckets}")

        avg = d.get("avg_score", -1)
        print(f"[{'PASS' if isinstance(avg, int) and 0 <= avg <= 100 else 'FAIL'}] avg_score is int in 0-100: {avg}")

        total_jobs = d.get("jobs_scraped_total", -1)
        print(f"[{'PASS' if isinstance(total_jobs, int) and total_jobs >= 0 else 'FAIL'}] jobs_scraped_total >= 0: {total_jobs}")

        skills = d.get("top_skills_in_demand", [])
        skills_ok = all("skill" in s and "count" in s for s in skills)
        print(f"[{'PASS' if skills_ok else 'FAIL'}] top_skills_in_demand has skill+count keys")
        print(f"       top 3: {[s['skill'] for s in skills[:3]]}")

        history = d.get("scrape_history", [])
        history_ok = all("date" in h and "jobs_found" in h and "jobs_new" in h for h in history)
        print(f"[{'PASS' if history_ok else 'FAIL'}] scrape_history has date+jobs_found+jobs_new keys")
        print(f"       entries: {len(history)}")

        # Verify counts are non-negative
        counts_ok = all(b.get("count", -1) >= 0 for b in dist)
        print(f"[{'PASS' if counts_ok else 'FAIL'}] All score_distribution counts >= 0")

        print("\n" + "="*60)
        print("QA COMPLETE")
        print("="*60)

asyncio.run(qa())
