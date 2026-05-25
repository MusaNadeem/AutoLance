# AutoLance (FreelanceRadar) — Complete LLM Reference

> **Internal app name:** FreelanceRadar / FreelanceIQ  
> **Purpose:** AI-powered Upwork job matching — scrapes jobs, scores them against your freelancer profile, generates tone-aware proposals, and alerts you on high-match jobs.

---

## Quick Start Commands

```bash
# Run ALL tests (86/86)
cd backend && linux_venv/bin/pytest tests/ -q

# Run live API QA (backend must be running on :8000)
cd backend && DATABASE_URL="postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar" \
  SECRET_KEY=devkey JWT_SECRET=devjwt ANTHROPIC_API_KEY=sk-dummy UPLOAD_DIR=/tmp/autolance_uploads \
  linux_venv/bin/python qa_full.py

# TypeScript check
cd frontend && npx tsc --noEmit

# Start backend (local dev)
cd backend && DATABASE_URL="postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar" \
  SECRET_KEY=devkey JWT_SECRET=devjwt ANTHROPIC_API_KEY=<real_key> \
  UPLOAD_DIR=/tmp/autolance_uploads linux_venv/bin/uvicorn main:app --reload

# Start frontend (local dev)
cd frontend && npm run dev

# Docker (full stack)
docker-compose up --build
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115 · Python 3.11 · Pydantic v2 · SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 + pgvector extension |
| Cache / Queue | Redis 7 · Celery 5.4 · Celery Beat · Flower |
| AI | Anthropic Claude (`claude-sonnet-4-5`) via `anthropic==0.40.0` |
| Scraping | Bright Data Web Scraper API + Web Unlocker proxy |
| CV parsing | PyMuPDF (PDF) · python-docx (DOCX) · pytesseract (OCR fallback) |
| Frontend | Next.js 15 · React 19 · TypeScript 5 · TailwindCSS 3 |
| UI libs | Framer Motion · Lucide · Recharts v2 · SWR · Axios · Radix UI |
| Auth | JWT (python-jose) · bcrypt (passlib) |
| Monitoring | Sentry · Prometheus (prometheus-fastapi-instrumentator) · Flower |
| Proxy | Nginx (routes `/api/` → FastAPI, all else → Next.js) |

---

## Phase Status & Test Counts

| Phase | Focus | Status | Tests |
|---|---|---|---|
| **Phase 1** | Scoring engine + bid strategy + jobs UI | ✅ Done | 22/22 |
| **Phase 2** | Scrape observability + alert inbox + NotificationBell + StatusBar | ✅ Done | 37/37 |
| **Phase 3** | Proposal tone selector + CV profile PUT + Onboarding + Profile pages | ✅ Done | 61/61 |
| **Phase 4** | Job filtering/pagination + analytics dashboard | ✅ Done | 86/86 |
| **Phase 5** | Integration hardening + demo prep | ✅ Done | 86/86 |

**Live API QA:** 75/75 (`qa_full.py`) | **TypeScript:** 0 errors

---

## Environment Variables — Complete Reference

### Required (app won't start without these)

```bash
DATABASE_URL=postgresql+asyncpg://freelanceradar:secret@postgres:5432/freelanceradar
# Local dev override: postgresql+asyncpg://freelanceradar:secret@127.0.0.1:5433/freelanceradar

SECRET_KEY=<long-random-string>          # App signing key
JWT_SECRET=<another-long-random-string>  # JWT token signing key
ANTHROPIC_API_KEY=sk-ant-...             # Claude API — cover letter generation + CV parsing
UPLOAD_DIR=/app/uploads                  # Local dev: /tmp/autolance_uploads
```

### Bright Data (scraping — leave blank for mock data in dev)

```bash
BRIGHT_DATA_API_KEY=                     # From brightdata.com dashboard
BRIGHT_DATA_WS_DATASET_ID=              # Pre-configured Upwork dataset ID
BRIGHT_DATA_WS_ZONE=                    # Web Scraper zone name
BRIGHT_DATA_UNLOCKER_ZONE=             # Web Unlocker zone name (optional)
BRIGHT_DATA_USERNAME=                   # Proxy auth username
BRIGHT_DATA_PASSWORD=                   # Proxy auth password
BRIGHT_DATA_HOST=brd.superproxy.io      # Fixed Bright Data proxy host
BRIGHT_DATA_PORT=22225                  # Fixed Bright Data proxy port
```

> **Without Bright Data keys** the scraper automatically falls back to `_get_mock_jobs()` — returns 10 hardcoded Python/FastAPI jobs. All pipeline, scoring, and alert logic runs identically on mock data.

### Redis / Celery

```bash
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### Database (Postgres)

```bash
POSTGRES_USER=freelanceradar
POSTGRES_PASSWORD=secret
POSTGRES_DB=freelanceradar
```

### JWT Config

```bash
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440    # 24 hours
# JWT_REFRESH_TOKEN_EXPIRE_DAYS=30      # Set in config.py default
```

### AI Model

```bash
CLAUDE_MODEL=claude-sonnet-4-5          # Change here to switch models
# CLAUDE_MAX_TOKENS=4096                # Default in config.py
# CLAUDE_TEMPERATURE=0.1                # Low temp for consistent proposals
```

### Scoring Weights (must sum exactly to 1.0 — validated at startup)

```bash
SCORE_WEIGHT_SKILL=0.35           # Job-to-profile skill relevance
SCORE_WEIGHT_ROI=0.30             # Budget fit vs user target rate
SCORE_WEIGHT_COMPETITION=0.20     # Low proposals = higher score
SCORE_WEIGHT_CLIENT_QUALITY=0.15  # Client hire rate × rating × history
```

### Notifications (all optional)

```bash
# Email via SendGrid
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=alerts@freelanceradar.io
SENDGRID_FROM_NAME=FreelanceRadar

# Email via SMTP (alternative)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

# Slack alerts
SLACK_DEFAULT_WEBHOOK_URL=
```

### Other

```bash
ENVIRONMENT=development               # or production
DEBUG=true                            # false in production
ALERT_THRESHOLD=0.75                  # Minimum score to trigger alert
SCRAPE_INTERVAL_MINUTES=15            # Celery beat schedule
SCRAPE_MAX_JOBS_PER_RUN=500
SCRAPE_RETRY_ATTEMPTS=3
SCRAPE_RETRY_DELAY_SECONDS=30
ALLOWED_ORIGINS=http://localhost:3000 # Comma-separated for CORS
FLOWER_USER=admin                     # Flower dashboard auth
FLOWER_PASSWORD=secret
SENTRY_DSN=                           # Optional error tracking
NEXT_PUBLIC_API_URL=http://localhost:8000  # Frontend → backend URL
```

### Supabase (optional — not actively used, can be left blank)

```bash
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_ANON_KEY=
```

---

## Architecture — Backend

### Directory Structure

```
backend/
├── main.py                          # App factory, router registration
├── alembic/versions/                # Migrations (4 files, linear chain)
├── app/
│   ├── config.py                    # All settings (Pydantic BaseSettings)
│   ├── database.py                  # AsyncSession, get_db, get_db_context
│   ├── middleware/auth.py           # JWT verify → get_current_user dependency
│   ├── models/
│   │   ├── __init__.py              # Exports: ScrapingRun, MatchScore, AlertConfig, AlertEvent
│   │   ├── user.py                  # User (id, email, hashed_password, is_active)
│   │   ├── job.py                   # Job + MatchScore models
│   │   ├── profile.py               # FreelancerProfile (12 fields + target_fixed cols)
│   │   ├── client.py                # Client (hire_rate, rating, total_spent, country)
│   │   └── notification.py          # Notification (in-app alerts)
│   ├── routers/
│   │   ├── auth.py                  # /auth/register, /login, /refresh
│   │   ├── cv.py                    # /cv/upload, /cv/profile (GET+PUT)
│   │   ├── jobs.py                  # /jobs (list + filter), /jobs/{id}
│   │   ├── alerts.py                # /alerts, /alerts/read-all, /alerts/config
│   │   ├── scrape.py                # /scrape/status, /scrape/trigger
│   │   └── analytics.py             # /analytics
│   ├── services/
│   │   ├── job_scorer.py            # AI scoring per user profile → match_scores
│   │   ├── bid_strategy.py          # BidStrategyEngine (competitive/value/premium)
│   │   ├── cover_letter_gen.py      # VALID_TONES, Claude API call
│   │   ├── cv_parser.py             # PDF/DOCX text extraction + Claude analysis
│   │   ├── client_analyzer.py       # Client upsert from scraped data
│   │   ├── notification.py          # notification_service (Slack/email) + alert_service (DB)
│   │   └── scoring.py               # client_quality_score() helper
│   ├── ai/
│   │   ├── client.py                # Claude API wrapper (model, max_tokens, temperature)
│   │   └── prompts/
│   │       ├── cover_letter.py      # build_cover_letter_prompt(profile, job, match, tone)
│   │       ├── cv_parser.py         # CV analysis prompt
│   │       └── job_scorer.py        # Job scoring prompt
│   ├── scraping/
│   │   ├── bright_data.py           # BrightDataClient (trigger, poll, mock fallback)
│   │   └── pipeline.py              # JobIngestionPipeline (normalize, dedupe, score)
│   └── workers/
│       ├── celery_app.py            # Celery config, queues, beat schedule
│       ├── scrape_tasks.py          # run_scheduled_scrape, manual_scrape
│       └── match_tasks.py           # score_new_jobs_for_all_users
```

### API Prefix & Router Registration

All routes: `/api/v1/...` — set as `API_PREFIX = "/api/v1"` in `main.py`

| Router | Prefix result | Key endpoints |
|---|---|---|
| auth | `/api/v1/auth/` | POST /register, POST /login, POST /refresh |
| cv | `/api/v1/cv/` | POST /upload, GET /profile, PUT /profile |
| jobs | `/api/v1/jobs/` | GET / (filter+paginate), GET /{id} |
| alerts | `/api/v1/alerts/` | GET /, POST /read-all, POST /read/{id}, GET /config, PUT /config |
| scrape | `/api/v1/scrape/` | GET /status, POST /trigger |
| analytics | `/api/v1/analytics/` | GET / |
| cover-letters | `/api/v1/cover-letters/` | POST /generate |

> **Route ordering critical in cv.py:** `/profile` (GET+PUT) must be declared **before** `/{cv_id}` or FastAPI matches "profile" as a cv_id string.

### Database / ORM Rules

- Always use `AsyncSession` — never sync SQLAlchemy
- Inject via `Depends(get_db)` in routers
- Use `get_db_context()` in Celery tasks (context manager, not generator)
- DB pool: size=20, overflow=10, timeout=30s

### Score System

- **Storage:** `match_scores` table stores **0–100 integers** (`int(raw_float * 100)`)
- **API response:** `/jobs` serializes back to **0.0–1.0 float** in the `score` object
- **Frontend:** `Math.round(job.score.overall * 100)` at display layer only — never stored multiplied

### Migration Chain (Alembic)

```
b45adee43753_init
  → 20260524_phase1_client_quality_and_bid_columns
    → 20260525_phase2_notifications
      → 20260525_phase3_profile_target_fixed
```

**No Phase 4 migration** — analytics queries existing tables.

**Fresh DB setup:**
```bash
cd backend && DATABASE_URL=... linux_venv/bin/alembic upgrade head
```
If tables already exist (dev bootstrapped): `alembic stamp head` then apply manually.

### Celery Queues

| Queue | Tasks |
|---|---|
| `scraping` | `scrape_tasks.*` |
| `matching` | `match_tasks.*` |
| `alerts` | `alert_tasks.*` |
| `default` | everything else |

Worker command: `celery -A app.workers.celery_app worker --concurrency=4 -Q default,scraping,matching,alerts`

---

## Scraping Pipeline (How It Works)

```
Celery Beat (every 15 min)
  → scrape_tasks.run_scheduled_scrape
    → BrightDataClient.trigger_dataset_collection()
        POST brightdata.com/datasets/v3/trigger
        with 7 Upwork search URLs (python, react, fullstack, ML, node, ts, general)
    → wait_for_snapshot() — polls every 15s up to 5 min
    → raw_jobs[] returned as JSON

  → pipeline.ingest_batch(db, raw_jobs)
      For each job:
        1. Deduplicate by upwork_job_id
        2. Normalize fields (budget, posted_at, proposal_tier)
        3. client_analyzer_service.analyze_from_raw() → upsert Client row
        4. client_quality_score(hire_rate, avg_rating, jobs_posted)
        5. BidStrategyEngine.calculate(DEFAULT_HOURLY_RATE=$50) → 5 bid columns
        6. Save to jobs table

  → If new > 0: match_tasks.score_new_jobs_for_all_users.apply_async()
      For each active user with a FreelancerProfile:
        → Claude AI scoring vs user's actual skills + rates
        → Saves to match_scores (0-100)
        → alert_service.check_and_dispatch() → Notification row if score ≥ threshold
```

**No Bright Data keys?** → falls back to `_get_mock_jobs()` (10 hardcoded jobs).

---

## Architecture — Frontend

### Directory Structure

```
frontend/src/
├── app/
│   ├── page.tsx                          # Landing / root redirect
│   ├── (auth)/
│   │   ├── login/page.tsx               # Login → profile check → /onboarding or /dashboard
│   │   ├── register/page.tsx            # Real API register → auto-login → /onboarding
│   │   └── onboarding/page.tsx          # First-time profile setup
│   └── (dashboard)/
│       ├── layout.tsx                    # Sidebar nav (8 items)
│       └── dashboard/
│           ├── page.tsx                  # Main dashboard (redirect/summary)
│           ├── jobs/page.tsx            # Job feed + FilterBar + ProposalPanel
│           ├── cv/page.tsx              # CV upload
│           ├── proposals/page.tsx       # Saved proposals
│           ├── analytics/page.tsx       # 4 recharts sections
│           ├── alerts/page.tsx          # Alert history table
│           ├── profile/page.tsx         # Profile edit
│           └── settings/page.tsx        # Settings
├── components/
│   ├── jobs/
│   │   ├── ScoreBadge.tsx              # 4-bar score display (threshold colours)
│   │   ├── BidRecommendation.tsx       # Bid amount + strategy + confidence bar
│   │   ├── FilterBar.tsx               # Sort / min-score / budget / time filters
│   │   └── ProposalPanel.tsx           # Tone selector + textarea + copy + regenerate
│   └── layout/
│       ├── StatusBar.tsx               # Scrape dot status (30s poll)
│       └── NotificationBell.tsx        # Bell + badge + dropdown (60s poll)
├── lib/
│   └── api.ts                          # Axios client + all API namespaces + 401 interceptor
└── types/
    └── index.ts                        # All shared TS types
```

### API Client (`lib/api.ts`)

```typescript
baseURL = `${NEXT_PUBLIC_API_URL}/api/v1`  // default: http://localhost:8000/api/v1
```

**401 Interceptor rule:** Redirects to `/login` on 401 EXCEPT when `error.config.url` contains `/auth/login` or `/auth/register` — prevents page reload on wrong password.

### Key Frontend Decisions

| Decision | Detail |
|---|---|
| **SWR jobs config** | `revalidateOnFocus: false, shouldRetryOnError: false, errorRetryCount: 0` |
| **StatusBar polling** | `refreshInterval: 30_000`. Detects `is_running` transition via `useRef` → calls `mutate` on `/jobs` key |
| **NotificationBell polling** | `refreshInterval: 60_000` |
| **Score display** | `Math.round(job.score.overall * 100)` — never store multiplied value |
| **ProposalPanel tone** | Tone buttons = select-only. Regenerate button applies selected tone. No auto-call on click. |
| **Post-login redirect** | GET /cv/profile → 0 skills or 404 → `/onboarding`, else `/dashboard` |
| **Post-register redirect** | Real POST /auth/register → auto-login → always `/onboarding` |
| **FilterBar state** | `useState` + `useRouter.replace()` URL sync. `useSearchParams()` seeds on mount. |
| **SWR key with filters** | Built dynamically: `/jobs?sort_by=score&min_score=70` — filter change auto-triggers fetch |
| **Analytics fallback** | `DEMO_DATA` as SWR `fallbackData` — charts render before API responds |
| **recharts version** | v2.x — import from `"recharts"`: `BarChart`, `LineChart`, `ResponsiveContainer`, `Cell`, `Tooltip` |
| **Suspense required** | `useSearchParams()` in Next.js 14+ App Router requires `<Suspense>` wrapper or interactivity freezes |
| **ExperienceLevel values** | `"junior" | "mid" | "senior" | "expert"` (backend) — UI may also accept `"entry" | "intermediate"` |

---

## Cover Letter / Proposal System

- **Endpoint:** `POST /api/v1/cover-letters/generate`
- **Payload:** `{ job_id, tone }` (tone optional, defaults to `"professional"`)
- **`VALID_TONES`:** `{"professional", "friendly", "bold"}` — unknown tones → `"professional"`
- **Prompt:** `build_cover_letter_prompt(profile, job, match, tone)` in `ai/prompts/cover_letter.py`
  - Each tone injects a distinct instruction block into the Claude prompt
  - 3 tones produce provably distinct outputs (tested in QA)
- **Claude model:** `claude-sonnet-4-5` (configurable via `CLAUDE_MODEL` env var)
- **Character limit warning:** ProposalPanel warns at >4500 chars (red counter)
- **Word warnings:** <50 words (too short) or >250 words (too long)

---

## CV Upload & Parsing

- **Endpoint:** `POST /api/v1/cv/upload` (multipart form)
- **Accepted types:** PDF, DOCX, TXT (max 10MB)
- **Extraction:** PyMuPDF for PDF, python-docx for DOCX, pytesseract OCR as fallback
- **Analysis:** Full CV text sent to Claude → returns structured JSON profile
- **Storage:** File saved to `UPLOAD_DIR`, profile saved to `freelancer_profiles` table
- **Profile endpoint:** `GET/PUT /api/v1/cv/profile` (12 fields)

### Profile Fields (12)

`id`, `headline`, `summary`, `skills` (array of `{name, level, years}`), `experience_level`, `niche`, `inferred_hourly_rate_min`, `inferred_hourly_rate_max`, `target_fixed_min`, `target_fixed_max`, `last_analyzed_at`, `profile_version`

`PUT /api/v1/cv/profile`:
- Uses `exclude_none=True` — only sends changed fields
- Never wipes unchanged fields (true partial update)
- Bumps `profile_version` on every save

---

## Bugs Fixed (Critical Reference)

| Bug | Root Cause | Fix |
|---|---|---|
| Login reloads on wrong password | 401 interceptor redirected to `/login` even for `/auth/login` 401s | Interceptor skips redirect when `error.config.url` contains auth endpoints |
| Register went to `/dashboard/cv` | `handleSubmit` used `setTimeout` mock — never called API | Real `POST /auth/register` + `POST /auth/login` flow, always → `/onboarding` |
| `GET /cv/profile` returned 500 | FastAPI matched `/profile` against `/{cv_id}` wildcard | Moved `/profile` routes above `/{cv_id}` in `cv.py` |
| Phase 3 migration broken branch | `down_revision` pointed to Phase 1 instead of Phase 2 | Fixed to `"20260525_phase2"`, columns applied via raw SQL on dev DB |
| Tone change re-generated proposal | `handleToneChange` called `generate(newTone)` directly | Split into `handleToneSelect` (state only) — generation on Regenerate click |
| Jobs list refreshed on focus | SWR default options | Added `revalidateOnFocus: false, shouldRetryOnError: false, errorRetryCount: 0` |
| StatusBar stuck on "Loading..." | `cover_letter.py` had backslash in f-string (SyntaxError on Python 3.11) | Moved string building outside f-string |
| FilterBar buttons dead | `useSearchParams` in App Router needs `<Suspense>` | Wrapped `JobsFeed` in `<Suspense>` in `jobs/page.tsx` |
| Docker frontend build failing | ESLint blocked build on unused vars | Cleaned up unused imports in `ProposalPanel.tsx`, `FilterBar.tsx`, `jobs/page.tsx` |
| `qa_full.py` FILE checks failing locally | Hardcoded `/app/...` Docker paths | Replaced with `os.path.dirname(os.path.abspath(__file__))` |
| Dashboard job clicks navigated away | Cards and alert rows navigated to jobs feed instead of opening inline | Added inline slide-over detail panel to dashboard so it doesn't navigate away |

---

## Docker Compose Services (7 containers)

| Container | Image | Port | Purpose |
|---|---|---|---|
| `fr_postgres` | pgvector/pgvector:pg16 | 5432 | PostgreSQL database |
| `fr_redis` | redis:7-alpine | 6379 | Celery broker + result backend |
| `fr_backend` | ./backend/Dockerfile | 8000 | FastAPI (Python 3.11-slim) |
| `fr_worker` | ./backend/Dockerfile | — | Celery worker (4 concurrency) |
| `fr_beat` | ./backend/Dockerfile | — | Celery beat scheduler |
| `fr_flower` | ./backend/Dockerfile | 5555 | Celery monitoring dashboard |
| `fr_frontend` | ./frontend/Dockerfile | 3000 | Next.js (multi-stage build) |
| `fr_nginx` | nginx:alpine | 80 | Reverse proxy |

**Nginx routing:** `/api/` → backend:8000, `/health` → backend, `/` → frontend:3000

**Volumes:** `postgres_data`, `redis_data`, `cv_uploads`, `celerybeat_data`

**Network:** `freelanceradar_net`

**Backend Dockerfile system deps:** `build-essential`, `libpq-dev`, `curl`, `tesseract-ocr`, `poppler-utils`, `libmagic1`

---

## Deployment Plan

### Prerequisites

1. Server: Ubuntu 22.04 LTS, min 4GB RAM, 2 vCPU
2. Docker + Docker Compose installed
3. Domain name with DNS A record pointing to server IP
4. All API keys ready (see Environment Variables section)

### Step 1 — Clone & Configure

```bash
git clone https://github.com/MusaNadeem/AutoLance.git
cd AutoLance
cp .env.example .env
nano .env   # Fill in all required values
```

**Minimum required values to set in `.env`:**
```bash
SECRET_KEY=<generate: openssl rand -hex 32>
JWT_SECRET=<generate: openssl rand -hex 32>
ANTHROPIC_API_KEY=sk-ant-...
POSTGRES_PASSWORD=<strong password>
FLOWER_PASSWORD=<strong password>
ALLOWED_ORIGINS=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com
```

### Step 2 — Build & Start

```bash
docker-compose up --build -d
```

Wait for all services healthy:
```bash
docker-compose ps  # All should show "healthy" or "Up"
```

### Step 3 — Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

If DB already has tables (re-deploy):
```bash
docker-compose exec backend alembic stamp head
```

### Step 4 — Verify Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"1.0.0"}

curl http://localhost/api/v1/jobs/
# Expected: 401 Unauthorized (auth working)
```

### Step 5 — SSL with Certbot (production)

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

Update `infra/nginx/nginx.conf` to add HTTPS server block and HTTP→HTTPS redirect.

### Step 6 — Seed Demo Data (optional for demo)

Trigger a manual scrape (with Bright Data configured) or use mock data:
```bash
# With a valid JWT token:
curl -X POST http://localhost:8000/api/v1/scrape/trigger \
  -H "Authorization: Bearer <token>"
```

### Step 7 — Verify Celery

```bash
# Check Flower dashboard
open http://yourdomain.com:5555  # admin / FLOWER_PASSWORD

# Check beat is scheduling
docker-compose logs beat | grep "Scheduler: Sending"
```

### Production Checklist

- [ ] `DEBUG=false` in `.env`
- [ ] `ENVIRONMENT=production` in `.env`
- [ ] Strong random `SECRET_KEY` and `JWT_SECRET` (not "devkey")
- [ ] `POSTGRES_PASSWORD` changed from "secret"
- [ ] `FLOWER_PASSWORD` changed from "secret"
- [ ] `ALLOWED_ORIGINS` set to actual frontend domain
- [ ] `NEXT_PUBLIC_API_URL` set to actual backend URL or domain
- [ ] SSL certificate installed
- [ ] `SENTRY_DSN` set for error tracking (optional but recommended)
- [ ] Firewall: only ports 80, 443, 22 exposed (not 5432, 6379, 5555 to public)
- [ ] `UPLOAD_DIR=/app/uploads` (inside container) — not `/tmp`
- [ ] Docker volumes backed up: `postgres_data`, `cv_uploads`

### Re-deploy (zero-downtime)

```bash
git pull origin main
docker-compose up --build -d --no-deps backend frontend worker beat
```

---

## QA Summary

```bash
# Run everything
cd backend && linux_venv/bin/pytest tests/ -q          # 86/86 unit tests
linux_venv/bin/python qa_full.py                       # 75/75 live API checks
cd ../frontend && npx tsc --noEmit                     # 0 TS errors
```

| Suite | Result |
|---|---|
| pytest tests/test_phase1.py | ✅ 22/22 |
| pytest tests/test_phase2.py | ✅ 15/15 |
| pytest tests/test_phase3.py | ✅ 24/24 |
| pytest tests/test_phase4.py | ✅ 25/25 |
| qa_full.py (live API) | ✅ 75/75 |
| TypeScript | ✅ 0 errors |

---

## Local Dev Notes

- Postgres Docker runs on **port 5433** locally (mapped from 5432 in container). `.env` uses `postgres:5432` (Docker hostname) — override with `127.0.0.1:5433` when running backend directly.
- `linux_venv/` is the local Python virtualenv in the `backend/` directory.
- Frontend dev server: `http://localhost:3001` (Next.js default if 3000 is taken).
- Celery workers are NOT needed for local dev — backend runs without them. Cover letter generation and profile saving work without Celery.
- Only `ANTHROPIC_API_KEY` is needed for full feature parity in local dev. Bright Data is optional.
