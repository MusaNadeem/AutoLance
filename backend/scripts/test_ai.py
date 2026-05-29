#!/usr/bin/env python3
"""
Test AI/ML API connection and CV parsing.
Run: cd backend && linux_venv/bin/python scripts/test_ai.py
"""
import asyncio, os, sys
from pathlib import Path

# Load .env
env = Path(__file__).resolve().parents[2] / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("UPLOAD_DIR", "/tmp")

aiml_key = os.getenv("AIML_API_KEY", "")
if not aiml_key:
    sys.exit("❌  AIML_API_KEY not set in .env\n"
             "Add: AIML_API_KEY=<your-key>\n"
             "     AIML_BASE_URL=https://api.aimlapi.com/v1\n"
             "     CLAUDE_MODEL=anthropic/claude-sonnet-4-5")

print("=" * 50)
print("AI/ML API Connection Test")
print("=" * 50)
print(f"Key:   {aiml_key[:12]}...")
print(f"URL:   {os.getenv('AIML_BASE_URL')}")
print(f"Model: {os.getenv('CLAUDE_MODEL')}")
print()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

async def main():
    from app.ai.client import claude

    # Test 1: basic completion
    print("Test 1: Basic completion...")
    reply = await claude.complete(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say exactly: 'AutoLance AI online'",
        max_tokens=20,
    )
    print(f"  ✅ {reply.strip()}")

    # Test 2: JSON completion (used by CV parser)
    print("Test 2: JSON completion (CV parser format)...")
    result = await claude.complete_json(
        system_prompt="Extract skills from the text. Return JSON with key 'skills' as an array of strings.",
        user_prompt="I have 5 years of Python, 3 years of React, and 2 years of PostgreSQL experience.",
        temperature=0.05,
    )
    skills = result.get("skills", [])
    print(f"  ✅ Extracted {len(skills)} skills: {skills[:3]}")

    print()
    print("🎉 AI/ML API is working. CV parsing and cover letters will use this API.")

asyncio.run(main())
