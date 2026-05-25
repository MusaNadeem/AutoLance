# AutoLance — Demo Script

**Run time: ~3 minutes. All 8 features demonstrated.**

---

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3001`
- PostgreSQL seeded with at least 10 jobs (mix of scores, hourly and fixed)
- A user account already registered (or register live in Step 1)

---

## Step 1 — Register & Onboard (30s)

1. Open `http://localhost:3001/register` in a fresh browser (incognito)
2. Enter name, email, password → **CREATE ACCOUNT**
3. App redirects to `/onboarding`
4. Add 3–4 skills (e.g. `Python`, `FastAPI`, `React`, `PostgreSQL`) pressing Enter after each
5. Set experience to **Senior**
6. Set Hourly Min=`80` Max=`180`, Fixed Min=`1000` Fixed Max=`15000`
7. Click **Confirm Profile** → redirected to `/dashboard/jobs`

**Feature shown:** Registration → Profile setup → Onboarding flow

---

## Step 2 — Trigger Scrape & Watch Status (30s)

1. Look at the **StatusBar** at the top of the dashboard
   - Shows: `● Last scraped X min ago — Y new jobs`
2. Click **Scrape Now** button
3. Status transitions: `● idle` → `◌ Scraping now...` → `● completed — Z new jobs`
4. Job list refreshes automatically after scrape completes

**Feature shown:** Real-time scrape observability, Celery integration

---

## Step 3 — Alert Bell Fires (30s)

1. After the scrape, look at the **bell icon** in the top-right
2. If any job scored ≥ 75 and was posted within 30 min, a red badge appears
3. Click the bell → dropdown shows job title + score
4. Click the alert row → navigates to that job in the feed
5. Click **Mark all read** → badge disappears

**Feature shown:** Alert system — real-time in-app notifications

---

## Step 4 — Filter + Job Detail (45s)

1. On the Jobs page, set **Sort by: Score** → cards re-order highest first
2. Drag the **Min Score** slider to `70` → lower-scored jobs disappear
3. Toggle **Budget: Hourly** → only hourly jobs visible
4. Click a high-scoring job card to open the detail panel
5. Point out the **Score Breakdown** — 4 coloured bars (Relevance, Client Quality, Budget Fit, Competition)
6. Point out the **Bid Recommendation** — amount, strategy badge (Competitive/Value/Premium), confidence bar, rationale
7. Click **Clear All** to reset filters

**Feature shown:** AI scoring (4 signals), bid strategy engine, filter/pagination

---

## Step 5 — Proposal + Analytics (45s)

1. With a job still selected, scroll to the **AI Proposal** panel
2. The proposal auto-generated on Professional tone
3. Click **Friendly** → tone highlighted (no regeneration yet)
4. Click **Regenerate** → textarea shows loading → new proposal loads
5. Click **Copy to Clipboard** → button flashes ✓ Copied!
6. Navigate to **Analytics** in sidebar (`/dashboard/analytics`)
7. Show: 4 summary cards (total jobs, avg score, new this week, top skill)
8. Show: Score distribution histogram, Scrape history line chart, Top skills bar chart

**Feature shown:** Tone-aware cover letter generation, analytics dashboard

---

## Notes

- Cover letter generation requires a real `ANTHROPIC_API_KEY` — set in `.env`
- With `sk-dummy`, the proposal area shows a red error banner (graceful fail, not a crash)
- Filter URL params persist across page refresh — share a filtered view by copying the URL
- All 6 pages are clean: no console errors, no React warnings
