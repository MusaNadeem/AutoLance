# AutoLance — AI Coding Session Tracker

> **App name in code:** FreelanceRadar / FreelanceIQ  
> **Stack:** FastAPI (Python) · Next.js 14 App Router · PostgreSQL · Redis · Celery  
> **Test runner:** `backend/linux_venv/bin/pytest`  
> **Start backend:** `cd backend && linux_venv/bin/uvicorn main:app --reload`  
> **Start frontend:** `cd frontend && npm run dev`

---

## Session Rules

- All backend code lives under `backend/app/`
- All frontend code lives under `frontend/src/`
- Migrations go in `backend/alembic/versions/`
- Tests go in `backend/tests/`
- After every phase: run tests, commit, push to `origin/main`
- Score values: **0–100 integer** throughout backend and frontend (not 0.0–1.0 float)

---

## Phase Status

| Phase | Focus | Status | Tests |
|---|---|---|---|
| **Phase 1** | Scoring engine + bid strategy + jobs UI | ✅ Done | 22/22 |
| **Phase 2** | Scrape observability + alert inbox + NotificationBell + StatusBar | ✅ Done | 37/37 |
| **Phase 3** | Proposal tone selector + CV profile PUT + Onboarding page | 🔄 In Progress | — |
| **Phase 4** | Job filtering/pagination + analytics dashboard | ⏳ Pending | — |

---

## Phase 1 — Done ✅

### Backend (Musa)
- `app/services/job_scorer.py` — full scoring pipeline (skill, semantic, budget, client quality)
- `app/services/bid_strategy.py` — bid recommendation with floor/ceiling + rationale
- `app/config.py` — weight sum validation, alert thresholds
- Migration `20260524_phase1_client_quality_and_bid_columns.py` — 5 new columns on `jobs`
- `tests/test_phase1.py` — 22 passing tests

### Frontend (Omer)
- `components/jobs/ScoreBadge.tsx` — colour-coded 0–100 score chip
- `components/jobs/BidRecommendation.tsx` — bid range + strategy rationale card
- `(dashboard)/dashboard/jobs/page.tsx` — SWR disabled retries (`shouldRetryOnError: false`), `layout="position"` on cards

---

## Phase 2 — Done ✅

### Backend (Musa)
- `app/models/notification.py` — `Notification` model (Integer score 0–100, `is_read` server_default false)
- `alembic/versions/20260525_phase2_notifications.py` — notifications table migration
- `app/routers/scrape.py` — `GET /scrape/status`, `POST /scrape/trigger`, `GET /scrape/history`
- `app/routers/__init__.py` → alerts router: `GET /alerts/`, `POST /alerts/read/{id}`, `POST /alerts/read-all`
- `app/workers/match_tasks.py` — Notification insert in `_check_and_dispatch_alert` (deduped)
- `tests/test_phase2.py` — 15 passing tests

### Frontend (Omer)
- `components/layout/StatusBar.tsx` — SWR 30s poll, 3-state dot, Scrape Now button, auto-mutates `/jobs`
- `components/layout/NotificationBell.tsx` — badge, dropdown, optimistic mark-all-read, SWR 60s poll
- `(dashboard)/dashboard/alerts/page.tsx` — filter tabs (All/Unread/Read), score badges, empty state
- `(dashboard)/layout.tsx` — `<StatusBar />` below topbar, `<NotificationBell />` in header

### Known Type Convention
- `Notification.score` = **Integer 0–100** (backend) ↔ `number` in TypeScript
- `scoreColor()` thresholds: ≥85 lime · ≥70 cyan · ≥50 orange · else pink

---

## Phase 3 — In Progress 🔄

### What needs to be built

#### Backend (Musa) — R5 + R6

**R5 — Tone-aware proposal generation**
- [ ] `POST /proposal/generate` — add optional `tone` param (`professional` | `friendly` | `bold`, default `professional`)
- [ ] `app/ai/prompts/cover_letter.py` — add tone instruction blocks
- [ ] `app/ai/client.py` — append tone block to system prompt

**R6 — CV profile PUT endpoint**
- [ ] `PUT /api/v1/cv/profile` — update profile for current user (auth required)
  - Fields: `headline`, `summary`, `skills[]`, `experience_level`, `target_hourly_rate_min`, `target_hourly_rate_max`, `target_fixed_min`, `target_fixed_max`
- [ ] `GET /api/v1/cv/profile` — return all 7 fields (must be explicit null, not missing)
- [ ] Add `target_fixed_min` + `target_fixed_max` Float nullable columns to `FreelancerProfile`
- [ ] Migration: `20260525_phase3_profile_target_fixed.py`

#### Frontend (Omer) — R5 + R6

**R5 — ProposalPanel upgrade**
- [ ] `components/jobs/ProposalPanel.tsx` (new or upgrade)
  - Auto-resizing textarea pre-filled with cover letter
  - Live character counter (turns red >4500)
  - Word count warnings (<50 and >250)
  - 3 tone buttons: Professional | Friendly | Bold (Professional default)
  - Tone change → POST /proposal/generate with tone → textarea disabled+spinner
  - Copy to Clipboard (2s Copied! state)
  - Open on Upwork button
  - Regenerate with dirty-check confirm dialog

**R6 — Onboarding + Profile pages**
- [ ] `/onboarding` page — post-upload redirect, name/title/skills/rate form, PUT /cv/profile on confirm
- [ ] `(dashboard)/dashboard/profile` page — same form, edit + Save Changes
- [ ] Post-login redirect: check `GET /cv/profile` skills[] presence → if empty go to `/onboarding`

### Phase 3 QA Checklist (16 checks)
See roadmap lines 503–557 for full list.

---

## Phase 4 — Pending ⏳

### Backend (Musa) — R7 + R8
- Filtered + paginated `GET /jobs` (sort_by, min_score, min_budget, job_type, max_proposals, posted_within, page)
- Paginated response: `{jobs[], total, page, page_size, total_pages}`
- DB indexes on `overall_score`, `posted_at`, `budget_min`, `budget_max`
- `GET /api/v1/analytics` — single endpoint: jobs counts, score distribution, budget averages, top skills, scrape history, proposal/alert counts

### Frontend (Omer) — R7 + R8
- `FilterBar` component (sort, score, budget, type, proposals, time filters)
- Paginated job list with Prev/Next controls
- Analytics dashboard: sparkline charts, score histogram, top-skills bar chart

---

## Key File Map

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app factory, all routers wired |
| `backend/app/routers/__init__.py` | matches, cover-letters, proposals, alerts routers |
| `backend/app/routers/scrape.py` | Phase 2 scrape status/trigger |
| `backend/app/routers/cv.py` | CV upload, list, get — Phase 3 adds PUT /profile |
| `backend/app/models/profile.py` | FreelancerProfile — Phase 3 adds target_fixed columns |
| `backend/app/models/notification.py` | Phase 2 in-app notification (score = Integer 0–100) |
| `backend/app/workers/scrape_tasks.py` | Celery scrape — already tracks ScrapingRun |
| `backend/app/workers/match_tasks.py` | Score + dispatch + Notification insert |
| `frontend/src/lib/api.ts` | All API calls. `scrape.*`, `notifications.*`, `alerts.*` |
| `frontend/src/types/index.ts` | All shared TypeScript types |
| `frontend/src/components/layout/StatusBar.tsx` | Phase 2 live scrape status bar |
| `frontend/src/components/layout/NotificationBell.tsx` | Phase 2 bell dropdown |

---

## Common Commands

```bash
# Run all tests
cd backend && linux_venv/bin/pytest tests/ -v

# Run phase-specific tests  
linux_venv/bin/pytest tests/test_phase1.py tests/test_phase2.py -v

# Generate Alembic migration
linux_venv/bin/alembic revision --autogenerate -m "description"

# Apply migrations
linux_venv/bin/alembic upgrade head

# Check current migration head
linux_venv/bin/alembic current

# Type-check frontend
cd frontend && npx tsc --noEmit
```

---

## Gotchas & Decisions

| Decision | Reason |
|---|---|
| Score is **0–100 int**, not 0.0–1.0 | Matches `MatchScore.overall_score` Integer column. `scoreColor()` thresholds use 85/70/50 |
| SWR `shouldRetryOnError: false` on jobs page | Prevents re-animation loop on 404/network error |
| `layout="position"` on job cards | Restricts framer-motion layout animations to mount only |
| `Notification` vs `AlertEvent` | `AlertEvent` = external dispatch audit log. `Notification` = in-app user inbox |
| `notifications` SWR key = `"/alerts/"` | Trailing slash matches FastAPI route. Both `NotificationBell` and alerts page use same key |
| `is_running` transition detection in `StatusBar` | `useRef(prevRunning)` + `onSuccess` callback — mutates `/jobs` SWR key when scrape finishes |
