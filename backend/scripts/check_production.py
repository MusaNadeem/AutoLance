#!/usr/bin/env python3
"""
Production readiness checker.
Run before deploying: python scripts/check_production.py

Exits 0 if safe to deploy, 1 if critical issues found.
"""
import os, sys, re
from pathlib import Path

# Load .env
_root = Path(__file__).resolve().parents[2]
_env = _root / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

ERRORS   = []
WARNINGS = []

def err(msg):  ERRORS.append(f"  ❌  {msg}")
def warn(msg): WARNINGS.append(f"  ⚠️   {msg}")
def ok(msg):   print(f"  ✅  {msg}")

print("\n🔍  AutoLance — Production Readiness Check\n" + "─" * 45)

# ── Required secrets ───────────────────────────────────────────────────────
sk  = os.getenv("SECRET_KEY", "")
jwt = os.getenv("JWT_SECRET", "")
if not sk or sk in ("devkey", "change-me-to-a-long-random-string"):
    err("SECRET_KEY is weak or unset — generate with: openssl rand -hex 32")
elif len(sk) < 32:
    err(f"SECRET_KEY too short ({len(sk)} chars) — must be ≥ 32")
else:
    ok(f"SECRET_KEY is set ({len(sk)} chars)")

if not jwt or jwt in ("devjwt", "change-me-to-another-long-random-string"):
    err("JWT_SECRET is weak or unset — generate with: openssl rand -hex 32")
elif len(jwt) < 32:
    err(f"JWT_SECRET too short ({len(jwt)} chars) — must be ≥ 32")
else:
    ok(f"JWT_SECRET is set ({len(jwt)} chars)")

# ── Database password ──────────────────────────────────────────────────────
db_url = os.getenv("DATABASE_URL", "")
if ":secret@" in db_url or "@127.0.0.1:5433" in db_url:
    warn("DATABASE_URL contains dev credentials or localhost — use production host")
else:
    ok("DATABASE_URL looks production-like")

# ── Anthropic ──────────────────────────────────────────────────────────────
ak = os.getenv("ANTHROPIC_API_KEY", "")
if not ak or ak.startswith("sk-dummy") or ak == "sk-ant-xxxxxxxxxxxxxxxxxxxx":
    err("ANTHROPIC_API_KEY is not set — CV parsing and cover letters will fail")
else:
    ok("ANTHROPIC_API_KEY is set")

# ── Debug mode ─────────────────────────────────────────────────────────────
debug = os.getenv("DEBUG", "true").lower()
if debug == "true":
    warn("DEBUG=true — set DEBUG=false in production to suppress stack traces")
else:
    ok("DEBUG=false")

env = os.getenv("ENVIRONMENT", "development")
if env != "production":
    warn(f"ENVIRONMENT={env!r} — set ENVIRONMENT=production")
else:
    ok("ENVIRONMENT=production")

# ── Bright Data ────────────────────────────────────────────────────────────
bd_key  = os.getenv("BRIGHT_DATA_API_KEY", "")
bd_zone = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "")
if not bd_key:
    warn("BRIGHT_DATA_API_KEY not set — scraper will use mock data only")
else:
    ok("BRIGHT_DATA_API_KEY is set")
if not bd_zone:
    warn("BRIGHT_DATA_UNLOCKER_ZONE not set")
else:
    ok(f"BRIGHT_DATA_UNLOCKER_ZONE={bd_zone!r}")

# ── Email ──────────────────────────────────────────────────────────────────
sg = os.getenv("SENDGRID_API_KEY", "")
if not sg:
    warn("SENDGRID_API_KEY not set — password reset and email verification emails won't send")
else:
    ok("SENDGRID_API_KEY is set")

# ── Upload dir ─────────────────────────────────────────────────────────────
upload_dir = os.getenv("UPLOAD_DIR", "")
if not upload_dir or upload_dir == "/tmp/autolance_uploads":
    warn("UPLOAD_DIR is /tmp — files will be lost on restart; use a persistent volume")
elif upload_dir == "/app/uploads":
    ok("UPLOAD_DIR=/app/uploads (Docker volume)")
else:
    ok(f"UPLOAD_DIR={upload_dir!r}")

# ── Sentry ─────────────────────────────────────────────────────────────────
sentry = os.getenv("SENTRY_DSN", "")
if not sentry:
    warn("SENTRY_DSN not set — no error tracking in production")
else:
    ok("SENTRY_DSN is set")

# ── CORS origins ───────────────────────────────────────────────────────────
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
if "localhost" in origins:
    warn(f"ALLOWED_ORIGINS contains localhost — set to your production domain")
else:
    ok(f"ALLOWED_ORIGINS={origins!r}")

# ── Summary ────────────────────────────────────────────────────────────────
print()
if ERRORS:
    print("CRITICAL (must fix before deploying):")
    for e in ERRORS: print(e)
if WARNINGS:
    print("\nWARNINGS (fix before going live):")
    for w in WARNINGS: print(w)
if not ERRORS and not WARNINGS:
    print("  🎉  All checks passed — safe to deploy!")
elif not ERRORS:
    print(f"\n✅  No critical issues. {len(WARNINGS)} warning(s) to address.")
else:
    print(f"\n🛑  {len(ERRORS)} critical issue(s). Fix before deploying.")
    sys.exit(1)
