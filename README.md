# AutoLance 🎯

> AI-Powered Upwork Intelligence Engine — built on **Bright Data** + **AI/ML API**

AutoLance scrapes live Upwork jobs, scores each one against your CV using AI, and
generates personalized, tone-aware proposals — so freelancers apply where it
actually matters instead of manually scrolling hundreds of listings.

🏆 Built for the **Web Data UNLOCKED Hackathon** (Bright Data) — *GTM Intelligence Track* — by **Team Mutex** (Musa Nadeem · Omer Irfan).

---

## How It Works

```
Upload CV  →  AI extracts niche + skills + rates
   ↓
Scrape Now  →  Bright Data Web Unlocker pulls live Upwork jobs (profile-driven keywords)
   ↓
AI Scoring  →  every job scored 0–100 across 10 signals + bid strategy
   ↓
One-click Proposal  →  tone-aware cover letter, tracked in a Kanban pipeline
```

## Features

- **CV Intelligence** — Upload PDF/DOCX/TXT; AI extracts skills, experience, niche, and target rates into a persistent profile
- **Profile-Driven Scraping** — Bright Data **Web Unlocker API** bypasses Cloudflare; the user's niche + top skills drive which Upwork jobs are fetched
- **AI Match Scoring** — Every job scored 0–100 across 10 signals (skill match, budget fit, competition, client quality, win probability) with written reasoning
- **Bid Strategy Engine** — Deterministic 8-step algorithm recommends a Competitive / Value / Premium bid with a confidence score
- **Tone-Aware Cover Letters** — One-click proposals in Professional, Friendly, or Bold tones, personalized to the client's pain points
- **Proposal Tracker** — Kanban board (Drafted → Won), funnel analytics, and CSV export
- **Saved Jobs** — Bookmark interesting jobs to a dedicated list
- **Real-Time Alerts** — In-app notification bell, Slack, and email when high-match jobs appear; SSE stream for instant scrape-complete refresh
- **Analytics Dashboard** — Score distribution, top in-demand skills, and scrape history
- **Full Auth** — Email verification, password reset, account settings, activity log

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 · React 19 · TypeScript 5 · TailwindCSS 3 · Framer Motion · Recharts · SWR · Radix UI |
| Backend | FastAPI 0.115 · Python 3.11 · SQLAlchemy 2.0 (async) · Pydantic v2 |
| Workers | Celery 5.4 · Celery Beat · Flower |
| Database | PostgreSQL 16 + pgvector |
| Cache / Queue | Redis 7 |
| AI | **AI/ML API** (aimlapi.com) — OpenAI-compatible, serving Claude & DeepSeek |
| Scraping | **Bright Data Web Unlocker API** + `__NUXT__` HTML parsing |
| CV parsing | PyMuPDF (PDF) · python-docx (DOCX) · Tesseract OCR fallback |
| Email | SendGrid (optional) |
| DevOps | Docker Compose (8 services) · Nginx · Azure |

## Quick Start

### Prerequisites
- Docker + Docker Compose
- An [AI/ML API](https://aimlapi.com) key and a [Bright Data](https://brightdata.com) account (see `.env.example`)

### Setup

```bash
# 1. Clone
git clone https://github.com/MusaNadeem/AutoLance.git
cd AutoLance

# 2. Configure environment
cp .env.example .env
#    Fill in at minimum:
#      AIML_API_KEY, CLAUDE_MODEL (e.g. deepseek/deepseek-v4-flash)
#      BRIGHT_DATA_API_KEY, BRIGHT_DATA_UNLOCKER_ZONE
#      SECRET_KEY, JWT_SECRET, POSTGRES_PASSWORD

# 3. Start all services
docker compose up -d --build

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Open the app
open http://localhost:3000
```

> **No Bright Data keys?** The scraper falls back to realistic mock jobs so the
> full scoring/proposal pipeline still runs end-to-end for local development.

### Local Development (without Docker)

Requires a local PostgreSQL (with pgvector) and Redis.

```bash
# Backend
cd backend
python3 -m venv linux_venv
linux_venv/bin/pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://... linux_venv/bin/uvicorn main:app --reload --port 8000

# Celery worker (required for scraping + scoring)
linux_venv/bin/celery -A app.workers.celery_app worker -Q default,scraping,matching,alerts --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

> The Celery worker **must** be running — "Scrape Now" and AI scoring are
> background tasks. Without a worker they queue but never execute.

## Project Structure

```
AutoLance/
├── backend/            # FastAPI app, Celery workers, Alembic migrations, tests
│   ├── app/
│   │   ├── routers/    # auth, cv, jobs, alerts, scrape, analytics, settings, ...
│   │   ├── services/   # job scorer, bid strategy, cover letters, CV parser
│   │   ├── scraping/   # Bright Data client + NUXT parser + ingestion pipeline
│   │   ├── workers/    # scrape + match Celery tasks
│   │   └── ai/         # AI client (AI/ML API) + prompts
│   └── alembic/        # database migrations
├── frontend/           # Next.js 15 app (dashboard, auth, components)
├── infra/nginx/        # reverse proxy config
├── presentation/       # hackathon deck (PDF), poster, cover image
├── docker-compose.yml
└── .env.example
```

## API Documentation

Once running:
- **Swagger UI** — http://localhost:8000/docs
- **ReDoc** — http://localhost:8000/redoc
- **Flower (Celery)** — http://localhost:5555

## Testing

```bash
cd backend && linux_venv/bin/pytest tests/ -q   # 86 backend tests
cd frontend && npx tsc --noEmit                 # TypeScript check
```

## License

MIT
