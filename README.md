# AutoLance 🎯

> AI-Powered Upwork Intelligence Engine — Built on Bright Data + Claude

AutoLance continuously scrapes the Upwork job board in real time, deeply analyzes freelancer profiles using Claude AI, and surfaces the highest-converting job opportunities with ranked match scores, personalized cover letters, and real-time alerts.

---

## Features

- **CV Intelligence Engine** — Upload PDF/DOCX resumes; Claude extracts skills, experience, niche, and builds a persistent profile
- **Real-Time Job Scraping** — Bright Data Web Scraper API + Web Unlocker bypasses Upwork bot protection at scale
- **AI Match Scoring** — Claude scores every job 0–100 against your profile with win probability and reasoning
- **Client Quality Detector** — Classifies clients as High/Medium/Risky/Avoid with red/green flag analysis
- **Cover Letter Generator** — Personalized, human-sounding cover letters per job in one click
- **Real-Time Alerts** — Slack, email, and browser push when high-match jobs appear
- **Proposal Tracker** — Kanban board tracking full proposal lifecycle
- **Competition Analyzer** — Identifies easy-win opportunities with low saturation
- **Rate Optimizer** — Pricing intelligence from scraped marketplace data

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, shadcn/ui |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.0 |
| Workers | Celery, Redis |
| Database | PostgreSQL 16 + pgvector |
| AI | Claude (Anthropic) |
| Scraping | Bright Data Web Scraper API + Web Unlocker |
| Storage | Supabase Storage |
| Email | SendGrid |
| DevOps | Docker Compose, Nginx |

## Quick Start

### Prerequisites
- Docker + Docker Compose
- API keys (see `.env.example`)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/MusaNadeem/AutoLance.git
cd AutoLance

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up -d

# 4. Run database migrations
docker-compose exec backend alembic upgrade head

# 5. Access the app
open http://localhost:3000
```

### Development (without Docker)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
AutoLance/
├── backend/          # FastAPI Python backend
├── frontend/         # Next.js 15 frontend
├── infra/            # Nginx, monitoring configs
├── docker-compose.yml
└── .env.example
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Flower (Celery)**: http://localhost:5555

## Architecture

See [implementation plan](docs/architecture.md) for full system design.

## License

MIT
