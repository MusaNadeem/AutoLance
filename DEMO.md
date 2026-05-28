# AutoLance — Demo Script

**Run time: ~4 minutes. All 10 features demonstrated.**

---

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- PostgreSQL and Redis running (Docker: `docker start autolance_postgres autolance_redis`)
- Celery worker running for scraping/scoring
- `ANTHROPIC_API_KEY` set in `.env` for CV parsing + cover letter generation

---

## Step 1 — Register & Onboard with CV (45s)

1. Open `http://localhost:3000/register` in a fresh browser (incognito)
2. Enter name, email, password → **CREATE ACCOUNT**
3. App redirects to `/onboarding` — **Step 1: Upload CV**
4. Drag & drop a PDF/DOCX resume onto the dropzone
5. Progress bar fills → "Claude is reading your CV..." → auto-advances to Step 2
6. Form is pre-filled: headline, skills, experience level, inferred rates (from AI parsing)
7. Review/edit skills, click **Confirm & Start Matching** → redirected to `/dashboard/jobs`

**Feature shown:** 2-step onboarding, real CV parsing with Claude claude-sonnet-4-6, AI profile extraction

---

## Step 2 — Trigger Profile-Aware Scrape (30s)

1. Click **Scrape Now** in the StatusBar
2. Status transitions: `● idle` → `◌ Scraping now...` (Celery worker running)
3. After completion: `● completed — N new jobs` — job list refreshes automatically
4. Point out: scrape used **your niche and top skills** as search keywords — not generic Python/React defaults

**Feature shown:** Profile-driven job discovery via Bright Data Unlocker API + NUXT parsing

---

## Step 3 — Alert Bell Fires (30s)

1. After the scrape, look at the **bell icon** in the top-right
2. If any job scored ≥ 75 and was posted within 30 min, a red badge appears
3. Click the bell → dropdown shows job title + score
4. Click **Mark all read** → badge disappears

**Feature shown:** Real-time in-app notifications, score-threshold alerts

---

## Step 4 — Filter + AI Job Detail (45s)

1. On the Jobs page, set **Sort by: Score** → cards re-order highest first
2. Drag the **Min Score** slider to `70` → lower-scored jobs disappear
3. Click a high-scoring job card to open the detail panel
4. Point out the **Score Breakdown** — 4 coloured bars (Skill Match, ROI, Competition, Client Quality)
5. Point out the **Bid Recommendation** — amount, strategy badge (Competitive/Value/Premium), confidence bar, rationale text
6. Point out the **Bookmark icon** → click to save job to `/dashboard/saved`

**Feature shown:** AI scoring (4 signals), bid strategy engine, job bookmarking, filter/pagination

---

## Step 5 — Proposal Generation + Apply & Track (45s)

1. With a job selected, scroll to the **AI Proposal** panel
2. The proposal auto-generates on Professional tone
3. Click **Friendly** tone → select but don't auto-regenerate
4. Click **Regenerate** → new tone-aware proposal loads
5. Click **Apply + Track** → toast: "Proposal saved — find it in your Proposals tracker"
6. Navigate to **Proposals** sidebar (`/dashboard/proposals`)
7. The new proposal card appears in the **Drafted** column with job title + bid + match score
8. Click the card's **Move** button → move it to **Sent**

**Feature shown:** Tone-aware cover letter generation, proposal tracker Kanban

---

## Step 6 — Analytics Dashboard (30s)

1. Navigate to **Analytics** in the sidebar (`/dashboard/analytics`)
2. Show 4 summary cards: total jobs scraped, average match score, top skill, new this week
3. Show Score distribution histogram
4. Show Scrape history line chart (jobs found over last 7 runs)
5. Show Top skills in demand bar chart

**Feature shown:** Market intelligence dashboard

---

## Notes

- If no CV uploaded: "Scrape Now" returns an error with "Upload CV →" link — intentional gate
- Cover letter generation requires a real `ANTHROPIC_API_KEY` — set in `.env`
- With `sk-dummy`, the proposal area shows a red error banner (graceful fail, not a crash)
- Mock data (20 varied jobs) loads automatically if Bright Data credentials aren't set
- Filter URL params persist across refresh — shareable filtered view
- Password reset: `http://localhost:3000/forgot-password`
- Saved jobs: `http://localhost:3000/dashboard/saved`
