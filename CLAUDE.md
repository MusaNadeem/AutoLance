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
| **Phase 4** | Job filtering/pagination + analytics dashboard | ⏳ Pending | — |
| **Phase 5** | Integration hardening + demo prep | ⏳ Pending | — |

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
| `backend/alembic/versions/` | Migration chain: phase1 → phase2 → phase3 |
| `frontend/src/lib/api.ts` | Axios client, 401 interceptor (auth-endpoint guard), all API namespaces |
| `frontend/src/types/index.ts` | All shared TypeScript types — `ProposalTone`, `CVProfile`, `ExperienceLevel`, etc. |
| `frontend/src/components/jobs/ScoreBadge.tsx` | 4-bar score display with threshold colours |
| `frontend/src/components/jobs/BidRecommendation.tsx` | Bid amount, strategy badge, confidence bar, rationale |
| `frontend/src/components/jobs/ProposalPanel.tsx` | Tone selector (select-only), textarea, char/word counter, copy, regenerate |
| `frontend/src/components/layout/StatusBar.tsx` | Scrape status dot + polling (30s) + Scrape Now button |
| `frontend/src/components/layout/NotificationBell.tsx` | Bell + badge + dropdown + mark-all-read (60s poll) |
| `frontend/src/app/(auth)/login/page.tsx` | Login → profile check → `/onboarding` or `/dashboard` |
| `frontend/src/app/(auth)/register/page.tsx` | Real API register → auto-login → always `/onboarding` |
| `frontend/src/app/(auth)/onboarding/page.tsx` | Initial profile setup: skills chips, rates, experience level, PUT /cv/profile |
| `frontend/src/app/(dashboard)/layout.tsx` | Sidebar nav — Dashboard, CV, Jobs, Proposals, Analytics, Alerts, Profile, Settings |
| `frontend/src/app/(dashboard)/dashboard/jobs/page.tsx` | Job feed list + right-panel detail + ProposalPanel |
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

## Phase 4 — Next Up ⏳

From roadmap:
- `GET /jobs` — add query params: `sort_by` (score|posted_at|budget), `min_score` (0–100), `budget_type` (hourly|fixed), `posted_within` (hours), `page`, `page_size`
- `GET /api/v1/analytics` — top-level: `jobs_scraped_total`, `avg_score`, `score_distribution` (4 buckets), `top_skills_in_demand`, `scrape_history` (last 7)
- Frontend: FilterBar component on jobs page (sort dropdown, score slider, budget toggle, time filter, Clear all)
- Frontend: `/dashboard/analytics` — 4 recharts sections (score histogram, skills bar chart, scrape history line, summary cards)
- URL query param persistence for filters (survives page refresh)

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
