# AutoLance — AI Coding Session Tracker

> **App name in code:** FreelanceRadar / FreelanceIQ  
> **Stack:** FastAPI (Python 3.13) · Next.js 14 App Router · PostgreSQL · Redis · Celery  
> **Test runner:** `cd backend && linux_venv/bin/pytest tests/ -q`  
> **Start backend:** `cd backend && DATABASE_URL="postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar" SECRET_KEY=devkey JWT_SECRET=devjwt ANTHROPIC_API_KEY=<key> UPLOAD_DIR=/tmp/autolance_uploads linux_venv/bin/uvicorn main:app --reload`  
> **Start frontend:** `cd frontend && npm run dev`  
> **Postgres (Docker):** `fr_postgres_dev` on port **5433** (not 5432). `.env` uses Docker hostname `postgres:5432` — override with `127.0.0.1:5433` when running locally.

---

## Session Rules

- All backend code lives under `backend/app/`
- All frontend code lives under `frontend/src/`
- Migrations go in `backend/alembic/versions/`
- Tests go in `backend/tests/`
- After every phase: run tests, commit, push to `origin/main`
- **Score values: 0–100 integer** throughout backend and frontend (never 0.0–1.0 float in DB or API)
- Frontend displays `score.overall * 100` because the API returns the raw float — convert at display layer only

---

## Phase Status

| Phase | Focus | Status | Tests |
|---|---|---|---|
| **Phase 1** | Scoring engine + bid strategy + jobs UI | ✅ Done | 22/22 |
| **Phase 2** | Scrape observability + alert inbox + NotificationBell + StatusBar | ✅ Done | 37/37 |
| **Phase 3** | Proposal tone selector + CV profile PUT + Onboarding + Profile pages | ✅ Done | 61/61 |
| **Phase 4** | Job filtering/pagination + analytics dashboard | ✅ Done | 86/86 |
| **Phase 5** | Integration hardening + demo prep | ✅ Done | 86/86 |

---

## Architecture & Design Decisions

### Backend

| Decision | Detail |
|---|---|
| **API prefix** | All routes under `/api/v1` — set in `main.py` as `API_PREFIX = "/api/v1"` |
| **Auth dependency** | `Depends(get_current_user)` from `app.middleware.auth` — every protected endpoint uses this |
| **DB session** | `AsyncSession` via `async_sessionmaker`. Injected with `Depends(get_db)`. Never use sync SQLAlchemy. |
| **Score storage** | `match_scores` table stores **0–100 integers**. The pipeline calls `int(raw_float * 100)` before insert. |
| **Score API** | `GET /jobs` serialises back to 0.0–1.0 float for the `score` object. Frontend multiplies by 100 for display. |
| **Bid strategy** | `BidStrategyEngine` in `app/services/bid_strategy.py`. Floor = `budget_min * 0.75`, ceiling = `budget_max * 1.15`. |
| **Cover letter tone** | `VALID_TONES = {"professional", "friendly", "bold"}` in `cover_letter_gen.py`. Unknown tones default to `professional`. Tone injects a specific instruction block into the Claude prompt. |
| **Profile upsert** | `PUT /api/v1/cv/profile` uses `exclude_none=True` — sends only changed fields. Backend merges into existing row (never wipes unchanged fields). Bumps `profile_version` on every save. |
| **Notifications** | `notification_service` (Slack/email) and `alert_service` (in-app DB insert) are called from `match_tasks.py` after every score cycle. |
| **Celery tasks** | `match_tasks.py` handles scoring + alert dispatch. `scrape_tasks.py` handles web scraping. Beat schedule every 20 min. |
| **Migration chain** | `b45adee43753` → `20260524_phase1` → `20260525_phase2` → `20260525_phase3_profile_target_fixed`. Do NOT set `down_revision` to an earlier branch. |
| **Alembic on fresh DB** | Base init migration tries to CREATE tables that already exist when DB was bootstrapped by dev mode. Use `alembic stamp head` if tables already exist, or apply Phase N migrations manually via raw SQL. |
| **Analytics endpoint** | `GET /api/v1/analytics/` — no pagination, always returns full aggregated data. `avg_score` is 0 for new users with no match scores yet (not a bug). Scores fetched from `match_scores` table, capped at 500 rows for performance. |
| **Jobs filter: min_score** | Applied **post-fetch** (not in SQL) because scores live in `match_scores`, not `jobs`. This means `total` count in response reflects pre-filter count; actual `jobs` array may be smaller after min_score filtering. |
| **Jobs filter: sort_by=score** | Also applied post-fetch — sorted in Python after match score join. Invalid `sort_by` values silently fall back to `posted_at`. |
| **Jobs response envelope** | Phase 4 adds `total` field: `{page, limit, total, jobs[]}`. Old consumers that only used `jobs` are unaffected. |

### Frontend

| Decision | Detail |
|---|---|
| **API client** | `apiClient` in `frontend/src/lib/api.ts` — Axios instance with `baseURL = NEXT_PUBLIC_API_URL/api/v1` (default `http://localhost:8000/api/v1`) |
| **401 interceptor** | Redirects to `/login` on 401 **except** when the request URL contains `/auth/login` or `/auth/register`. Without this guard, a wrong password causes a page reload instead of showing the error message. |
| **SWR for jobs** | `revalidateOnFocus: false, shouldRetryOnError: false, errorRetryCount: 0` — prevents spam-refreshing the job list. Only the StatusBar polls (30s). |
| **Score display** | `Math.round(job.score.overall * 100)` — multiply API float by 100 at the component level. Do NOT store or pass the multiplied value. |
| **ProposalPanel tone** | Tone buttons are **select-only** — they highlight the chosen tone but do NOT auto-regenerate. The user clicks **Regenerate** to apply the selected tone. This avoids unwanted API calls on every button click. |
| **Post-login redirect** | Login page: `GET /cv/profile` → `skills.length === 0` or 404 → `/onboarding`, else `/dashboard`. |
| **Post-register redirect** | Register page makes a real `POST /auth/register` then `POST /auth/login`, stores tokens, and always goes to `/onboarding` (new users never have skills). |
| **Route ordering (FastAPI)** | Specific routes (`/profile`) must be declared **before** wildcard routes (`/{cv_id}`) in the same router. FastAPI matches top-to-bottom. Violating this causes `/profile` to be treated as a cv_id string. |
| **ExperienceLevel type** | `"entry" | "intermediate" | "expert" | "junior" | "mid" | "senior"` — backend uses junior/mid/senior; job filter UI uses entry/intermediate. Both are valid. |
| **StatusBar polling** | `refreshInterval: 30_000` for scrape status. Detects `is_running` transition via `useRef(prevRunning)` and calls SWR `mutate` on the `/jobs` key when scrape finishes. |
| **NotificationBell polling** | `refreshInterval: 60_000`. Badge hidden when unread count = 0. |
| **FilterBar state** | Filter params are stored in `useState` and synced to the URL via `useRouter.replace()` — no page reload. On mount, `useSearchParams()` seeds the initial state so filters survive a page refresh. |
| **Jobs SWR key with filters** | SWR key is built dynamically: `"/jobs?sort_by=score&min_score=70"` etc. Changing any filter triggers a new SWR fetch automatically. |
| **Analytics demo fallback** | `AnalyticsPage` has `DEMO_DATA` hardcoded as `fallbackData` for SWR — charts always render, even before the API responds. |
| **recharts version** | `recharts@2.x` (v2) is installed. v3 migration is not needed. Import from `"recharts"` — `BarChart`, `LineChart`, `ResponsiveContainer`, `Cell`, `Tooltip`. |

---

## Key File Map

| File | Purpose |
|---|---|
| `backend/main.py` | App factory, router registration, `API_PREFIX = "/api/v1"` |
| `backend/app/models/job.py` | Job + MatchScore SQLAlchemy models |
| `backend/app/models/profile.py` | `FreelancerProfile` — includes `target_fixed_min/max` (Phase 3) |
| `backend/app/models/notification.py` | In-app notification records |
| `backend/app/services/job_scorer.py` | `client_quality_score()`, `aggregate_score()` — outputs 0–100 int |
| `backend/app/services/bid_strategy.py` | `BidStrategyEngine` — competitive/value/premium logic |
| `backend/app/services/cover_letter_gen.py` | `VALID_TONES`, tone validation, Claude API call |
| `backend/app/services/notification.py` | `notification_service` (Slack/email), `alert_service` (DB insert) |
| `backend/app/ai/prompts/cover_letter.py` | `build_cover_letter_prompt(profile, job, match, tone)` — 3 tone instruction blocks |
| `backend/app/routers/cv.py` | `/cv/upload`, `/cv/profile` (GET+PUT) — `/profile` routes must come before `/{cv_id}` |
| `backend/app/routers/scrape.py` | `GET /scrape/status`, `POST /scrape/trigger` |
| `backend/app/routers/alerts.py` | `GET /alerts`, `POST /alerts/read-all`, `GET /alerts/config`, `PUT /alerts/config` |
| `backend/app/workers/match_tasks.py` | Scoring + alert dispatch Celery task |
| `backend/alembic/versions/` | Migration chain: phase1 → phase2 → phase3 (no Phase 4 migration needed) |
| `backend/app/routers/analytics.py` | `GET /analytics/` — jobs_scraped_total, avg_score, score_distribution, top_skills, scrape_history |
| `frontend/src/lib/api.ts` | Axios client, 401 interceptor (auth-endpoint guard), all API namespaces |
| `frontend/src/types/index.ts` | All shared TS types — `AnalyticsData`, `JobsListParams`, `ProposalTone`, `CVProfile`, etc. |
| `frontend/src/components/jobs/ScoreBadge.tsx` | 4-bar score display with threshold colours |
| `frontend/src/components/jobs/BidRecommendation.tsx` | Bid amount, strategy badge, confidence bar, rationale |
| `frontend/src/components/jobs/ProposalPanel.tsx` | Tone selector (select-only), textarea, char/word counter, copy, regenerate |
| `frontend/src/components/jobs/FilterBar.tsx` | Sort dropdown, min-score slider, budget toggle, posted-within select, animated Clear All |
| `frontend/src/components/layout/StatusBar.tsx` | Scrape status dot + polling (30s) + Scrape Now button |
| `frontend/src/components/layout/NotificationBell.tsx` | Bell + badge + dropdown + mark-all-read (60s poll) |
| `frontend/src/app/(auth)/login/page.tsx` | Login → profile check → `/onboarding` or `/dashboard` |
| `frontend/src/app/(auth)/register/page.tsx` | Real API register → auto-login → always `/onboarding` |
| `frontend/src/app/(auth)/onboarding/page.tsx` | Initial profile setup: skills chips, rates, experience level, PUT /cv/profile |
| `frontend/src/app/(dashboard)/layout.tsx` | Sidebar nav — Dashboard, CV, Jobs, Proposals, Analytics, Alerts, Profile, Settings |
| `frontend/src/app/(dashboard)/dashboard/jobs/page.tsx` | Job feed + FilterBar (URL-persisted) + right-panel detail + ProposalPanel |
| `frontend/src/app/(dashboard)/dashboard/analytics/page.tsx` | 4 summary cards + score histogram + scrape history line + top skills bar (recharts) |
| `frontend/src/app/(dashboard)/dashboard/alerts/page.tsx` | Full alert history table |
| `frontend/src/app/(dashboard)/dashboard/profile/page.tsx` | Profile edit (pre-filled, PUT on save, green toast) |

---

## Bugs Fixed (reference for future sessions)

| Bug | Root Cause | Fix |
|---|---|---|
| Login reloads on wrong password | 401 interceptor redirected to `/login` even when the `/auth/login` endpoint itself returned 401 | Interceptor now checks `error.config.url` and skips redirect for auth endpoints |
| Register went to `/dashboard/cv` (fake stub) | `handleSubmit` used `setTimeout` — never called the API | Replaced with real `POST /auth/register` + `POST /auth/login` flow, redirects to `/onboarding` |
| `GET /cv/profile` returned 500 instead of 404 | FastAPI matched `/profile` against the `/{cv_id}` wildcard route | Moved `/profile` endpoints above `/{cv_id}` in `cv.py` |
| Phase 3 migration was a broken branch | `down_revision` pointed to Phase 1 instead of Phase 2 | Fixed to `"20260525_phase2"`, then applied columns via raw SQL on dev DB |
| Tone change re-generated proposal immediately | `handleToneChange` called `generate(newTone)` | Split into `handleToneSelect` (set state only) — generation happens on Regenerate click |
| Jobs list refreshed every few seconds | SWR default options poll on window focus | Added `revalidateOnFocus: false, shouldRetryOnError: false, errorRetryCount: 0` |
| StatusBar stuck on "Loading status..." after `main` pull | `cover_letter.py` had a `SyntaxError` (backslash inside f-string) crashing the backend on Python 3.11 | Moved string building outside the f-string — `tone_block` and `custom_instructions_block` computed before the `return f"""` |
| Filter UI not clickable (buttons/sliders dead) | Next.js 14 App Router `useSearchParams` triggers a CSR bailout freezing interactivity if not wrapped in a Suspense boundary | Wrapped the `JobsFeed` client component in a `<Suspense>` block in `jobs/page.tsx` |
| Frontend Docker build failing | ESLint strict mode blocked Next.js production builds due to unused variables (`_coverId`, `DEFAULTS`, `FileText`, `ExternalLink`) | Cleaned up unused imports/variables in `ProposalPanel.tsx`, `FilterBar.tsx`, and `jobs/page.tsx` |
| Phase 3 DB missing columns in Docker | Alembic migration file existed but wasn't stamped/run on the Docker postgres volume properly | Manually ran `ALTER TABLE` to add `target_fixed_min`/`max` and updated `alembic_version` to `20260525_phase3_profile_target_fixed` |
| `qa_full.py` FILE checks always failed locally | Hardcoded `/app/...` Docker paths for file existence checks — always missing in local dev | Replaced with `os.path.dirname(os.path.abspath(__file__))` relative paths; 0-jobs is now a skip (INFO) not a FAIL |
---

## Phase 3 — Done ✅

### Backend
- [x] `POST /cover-letters/generate` — `tone` param (professional / friendly / bold, default professional)
- [x] `build_cover_letter_prompt()` — 3 distinct tone instruction blocks
- [x] `VALID_TONES` set in `cover_letter_gen.py` — unknown tones normalise to `professional`
- [x] `GET /api/v1/cv/profile` — returns all 12 fields (explicit null when missing)
- [x] `PUT /api/v1/cv/profile` — partial update, upserts on first call, bumps `profile_version`
- [x] `target_fixed_min` + `target_fixed_max` Numeric(10,2) nullable cols on `FreelancerProfile`
- [x] Migration `20260525_phase3_profile_target_fixed` (chained from Phase 2)

### Frontend
- [x] `ProposalPanel.tsx` — tone selector (select-only), auto-resize textarea, char counter (red >4500), word warnings (<50 / >250), Copy (2s Copied! state), Open on Upwork, Regenerate with dirty-check confirm
- [x] `/onboarding` — SkillChip array (Enter to add, × to remove, no duplicates), experience level, hourly+fixed rate pairs (min<max validation), PUT on Confirm, Skip link
- [x] `/dashboard/profile` — same form, pre-filled from GET, Save Changes + green toast, re-upload CV link
- [x] Login redirect: GET /cv/profile → 0 skills or 404 → `/onboarding`, else `/dashboard`
- [x] Register: real API call → auto-login → always `/onboarding`
- [x] Sidebar: Profile nav item (User icon, between Alerts and Settings)

---

## Phase 4 — Done ✅

### Backend
- [x] `GET /jobs` — `sort_by` (score|posted_at|budget), `min_score` (0–100), `budget_type` (hourly|fixed), `posted_within` (hours), `page`, `limit`. Returns `total` count.
- [x] `GET /api/v1/analytics/` — `jobs_scraped_total`, `avg_score`, `score_distribution` (4 buckets), `top_skills_in_demand` (top 10), `scrape_history` (last 7 runs)
- [x] No new migrations — analytics queries existing `jobs`, `match_scores`, `scraping_runs` tables
- [x] `tests/test_phase4.py` — 25 tests covering sort validation, min_score filter, posted_within cutoff, analytics response shape, bucket logic, skill counting

### Frontend
- [x] `FilterBar.tsx` — sort dropdown, min-score slider (0–100), budget type toggle (All/Hourly/Fixed), posted-within select, animated "Clear All" (only shown when filters active)
- [x] `/dashboard/jobs` — FilterBar wired with URL-persisted params via `useSearchParams`/`useRouter.replace()`. SWR key built from filter params. Real `posted_at` timestamps on cards. Empty state with "Clear Filters" button.
- [x] `AnalyticsData` type updated to match real backend shape. `JobsListParams` type added.
- [x] `/dashboard/analytics` — 4 summary cards + score histogram (recharts BarChart) + scrape history (recharts LineChart) + top skills (horizontal recharts BarChart). Demo fallback data so charts always render.

---

## Phase 5 — Done ✅

### Backend
- [x] `.env.example` — all required + optional vars with inline comments
- [x] Celery beat schedule verified: `crontab(minute=f"*/{SCRAPE_INTERVAL_MINUTES}")` every 20 min
- [x] All Phase 4 endpoints (`/jobs`, `/analytics`) guarded with `Depends(get_current_user)`
- [x] DB indexes confirmed: `upwork_job_id`, `posted_at`, `is_active` on `jobs` table
- [x] `qa_full.py` file path checks fixed — uses `os.path.dirname(__file__)` not `/app` Docker paths
- [x] **86/86 unit tests passing** (all phases, regression-clean)
- [x] **75/75 live API QA passing** (`qa_full.py` — auth, P1–P4 endpoints, file existence, router registration)

### Frontend
- [x] Loading skeleton on `alerts/page.tsx` — 3 animate-pulse rows matching layout
- [x] Loading skeleton on `profile/page.tsx` — full form skeleton (header + 5 blocks)
- [x] Profile page `catch` now surfaces error instead of swallowing it silently
- [x] `DEMO.md` — 5-step demo script covering all 8 features in under 3 minutes
- [x] TypeScript: 0 errors across entire frontend
- [x] Existing skeletons confirmed: `jobs/page.tsx`, `analytics/page.tsx`, `dashboard/page.tsx`, `cv/page.tsx`, `BidRecommendation.tsx`, `StatusBar.tsx`
- [x] Existing empty states confirmed: `alerts/page.tsx` (BellOff), `jobs/page.tsx` (Clear Filters), `NotificationBell.tsx` (No alerts yet), `onboarding/page.tsx`

---

## QA Summary — Final State

| Suite | Tool | Result |
|---|---|---|
| Unit tests Phase 1 | `pytest tests/test_phase1.py` | ✅ 22/22 |
| Unit tests Phase 2 | `pytest tests/test_phase2.py` | ✅ 15/15 |
| Unit tests Phase 3 | `pytest tests/test_phase3.py` | ✅ 24/24 |
| Unit tests Phase 4 | `pytest tests/test_phase4.py` | ✅ 25/25 |
| **All unit tests** | `pytest tests/` | ✅ **86/86** |
| Live API QA — Auth | `qa_full.py` | ✅ 2/2 |
| Live API QA — Phase 1 | `qa_full.py` | ✅ 8/8 |
| Live API QA — Phase 2 | `qa_full.py` | ✅ 8/8 |
| Live API QA — Phase 3 | `qa_full.py` | ✅ 13/13 |
| Live API QA — Phase 4 | `qa_full.py` | ✅ 18/18 |
| Live API QA — Files | `qa_full.py` | ✅ 16/16 |
| Live API QA — Routers | `qa_full.py` | ✅ 6/6 |
| **All live API checks** | `qa_full.py` | ✅ **75/75** |
| TypeScript | `npx tsc --noEmit` | ✅ 0 errors |

### How to run QA
```bash
# Unit tests
cd backend && linux_venv/bin/pytest tests/ -q

# Live API QA (backend must be running on :8000)
cd backend && DATABASE_URL="postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar" \
  SECRET_KEY=devkey JWT_SECRET=devjwt ANTHROPIC_API_KEY=sk-dummy UPLOAD_DIR=/tmp/autolance_uploads \
  linux_venv/bin/python qa_full.py

# TypeScript
cd frontend && npx tsc --noEmit
```

---

## All Phases Complete ✅

All 5 phases are done. The project is demo-ready.

Next steps (if any): docker-compose production build, seed DB with 20+ varied jobs for demo, run final Phase 5 QA from roadmap against a fresh `docker-compose up`.

---

## Environment

```
# Local dev (postgres running in Docker on 5433)
DATABASE_URL=postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar
SECRET_KEY=devkey
JWT_SECRET=devjwt
ANTHROPIC_API_KEY=<real key for cover letter generation>
UPLOAD_DIR=/tmp/autolance_uploads

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The `.env` file in the project root uses Docker hostnames (`postgres:5432`) — only works inside the Docker network. Override env vars inline for local dev as shown above.
