#!/usr/bin/env python3
"""
Upwork GraphQL field discovery via Bright Data.

Run: cd backend && linux_venv/bin/python scripts/test_graphql.py
Credentials are auto-loaded from the project root .env file.
"""
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

import requests

# ── Load .env ──────────────────────────────────────────────────────────────
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env = os.path.join(_root, ".env")
if os.path.exists(_env):
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY  = os.getenv("BRIGHT_DATA_API_KEY", "")
ZONE     = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "")
BASE     = "https://api.brightdata.com"

if not API_KEY:
    sys.exit("ERROR: BRIGHT_DATA_API_KEY not set in .env")

print(f"API key: {API_KEY[:12]}...   Zone: {ZONE!r}")
print()

MINIMAL = 'query { marketplaceJobPostings(filter: {query: "python"}, pagination: {first: 3}) { edges { node { id title ciphertext premium } } } }'


# ── Unlocker API wrapper ───────────────────────────────────────────────────

def unlocker(url: str, method: str = "GET", extra_headers: dict = None,
             body: str = None) -> dict:
    """
    Route a request through Bright Data Unlocker API.
    Returns the parsed outer response dict (has status_code, headers, body).
    """
    payload: dict = {"zone": ZONE, "url": url, "format": "json"}
    if method != "GET":
        payload["method"] = method
    if extra_headers:
        payload["headers"] = extra_headers
    if body is not None:
        payload["body"] = body

    r = requests.post(
        f"{BASE}/request",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    r.raise_for_status()
    return r.json()


def parse_cookies(outer: dict) -> dict:
    """Extract all cookies from an Unlocker API response's inner headers."""
    cookies: dict = {}
    raw = outer.get("headers", {}).get("set-cookie", "")
    if isinstance(raw, list):
        raw = ",".join(raw)
    for chunk in re.split(r",\s*(?=[A-Za-z_]+=)", raw):
        m = re.match(r"([A-Za-z_][A-Za-z0-9_\-]*)=([^;,\s]+)", chunk.strip())
        if m:
            cookies[m.group(1)] = m.group(2)
    return cookies


# ── STEP 1: Get token via Unlocker API ────────────────────────────────────

print("=" * 60)
print("STEP 1: Upwork homepage via Bright Data Unlocker API")
print("=" * 60)

outer = unlocker("https://www.upwork.com")
all_cookies = parse_cookies(outer)
inner_body = outer.get("body", "")
print(f"  Inner status: {outer.get('status_code')}  Body: {len(inner_body)} bytes")
print(f"  Cookies found: {list(all_cookies.keys())}")

token = all_cookies.get("visitor_gql_token")
if not token:
    hit = re.search(r'visitor_gql_token["\s:=]+([A-Za-z0-9%_\-\.]+)', inner_body[:10000])
    token = hit.group(1) if hit else None

if not token:
    sys.exit("❌  visitor_gql_token not found.")

print(f"  ✅ visitor_gql_token: {token[:50]}...")
print()

cookie_str = "; ".join(f"{k}={v}" for k, v in all_cookies.items())


# ── STEP 2: Try multiple GraphQL strategies ───────────────────────────────

print("=" * 60)
print("STEP 2: GraphQL query — trying all strategies")
print("=" * 60)

def parse_graphql_response(raw: str) -> dict:
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {"_parse_error": raw[:200]}


def edges_from(d: dict) -> list:
    return d.get("data", {}).get("marketplaceJobPostings", {}).get("edges", [])


working_strategy = None
data = None

# ── Strategy A: Unlocker API with all cookies in Cookie header ────────────
print("  A) Unlocker API + full Cookie header + Authorization Bearer")
try:
    outer_gql = unlocker(
        url="https://www.upwork.com/api/graphql/v1",
        method="POST",
        extra_headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Cookie": cookie_str,
            "Origin": "https://www.upwork.com",
            "Referer": "https://www.upwork.com/nx/search/jobs",
        },
        body=json.dumps({"query": MINIMAL}),
    )
    inner_raw = outer_gql.get("body", "{}")
    d = parse_graphql_response(inner_raw)
    edges = edges_from(d)
    if edges:
        print(f"     ✅ Got {len(edges)} jobs! Method A works.")
        working_strategy = "A"
        data = d
    elif d.get("message") or d.get("errors"):
        print(f"     ❌ Upwork error: {json.dumps(d)[:200]}")
    else:
        print(f"     ❌ No jobs, no error: {json.dumps(d)[:200]}")
except Exception as e:
    print(f"     ❌ Exception: {e}")

# ── Strategy B: Unlocker API, Cookie only (no Authorization header) ────────
if not working_strategy:
    print("  B) Unlocker API + Cookie header only (no Authorization)")
    try:
        outer_gql = unlocker(
            url="https://www.upwork.com/api/graphql/v1",
            method="POST",
            extra_headers={
                "Content-Type": "application/json",
                "Cookie": cookie_str,
                "Origin": "https://www.upwork.com",
                "Referer": "https://www.upwork.com/nx/search/jobs",
            },
            body=json.dumps({"query": MINIMAL}),
        )
        d = parse_graphql_response(outer_gql.get("body", "{}"))
        edges = edges_from(d)
        if edges:
            print(f"     ✅ Got {len(edges)} jobs! Method B works.")
            working_strategy = "B"
            data = d
        else:
            print(f"     ❌ {json.dumps(d)[:200]}")
    except Exception as e:
        print(f"     ❌ Exception: {e}")

# ── Strategy C: curl_cffi direct (no proxy) ───────────────────────────────
# This was confirmed working in previous sessions with this same token format.
if not working_strategy:
    print("  C) curl_cffi Chrome131 direct (no proxy) — previously confirmed working")
    try:
        from curl_cffi import requests as cffi_requests
        r = cffi_requests.post(
            "https://www.upwork.com/api/graphql/v1",
            impersonate="chrome131",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Cookie": cookie_str,
                "Origin": "https://www.upwork.com",
                "Referer": "https://www.upwork.com/nx/search/jobs",
            },
            json={"query": MINIMAL},
            timeout=30,
        )
        d = r.json()
        edges = edges_from(d)
        if edges:
            print(f"     ✅ Got {len(edges)} jobs! Method C works.")
            working_strategy = "C"
            data = d
        else:
            print(f"     ❌ {json.dumps(d)[:200]}")
    except ImportError:
        print("     ⚠️  curl_cffi not installed — skipping")
    except Exception as e:
        print(f"     ❌ Exception: {e}")

# ── Strategy D: curl_cffi + get fresh token directly ─────────────────────
if not working_strategy:
    print("  D) curl_cffi direct for BOTH homepage (fresh token) AND GraphQL")
    try:
        from curl_cffi import requests as cffi_requests

        home = cffi_requests.get(
            "https://www.upwork.com",
            impersonate="chrome131",
            timeout=30,
        )
        direct_token = home.cookies.get("visitor_gql_token")
        if not direct_token:
            raw = home.headers.get("set-cookie", "")
            m2 = re.search(r"visitor_gql_token=([^;,\s]+)", raw)
            direct_token = m2.group(1) if m2 else None

        print(f"     Direct token: {(direct_token or 'NOT FOUND')[:40]}...")

        if direct_token:
            direct_cookies = "; ".join(f"{k}={v}" for k, v in home.cookies.items())
            r2 = cffi_requests.post(
                "https://www.upwork.com/api/graphql/v1",
                impersonate="chrome131",
                headers={
                    "Authorization": f"Bearer {direct_token}",
                    "Content-Type": "application/json",
                    "Cookie": direct_cookies,
                    "Origin": "https://www.upwork.com",
                },
                json={"query": MINIMAL},
                timeout=30,
            )
            d = r2.json()
            edges = edges_from(d)
            if edges:
                print(f"     ✅ Got {len(edges)} jobs! Method D works.")
                working_strategy = "D"
                data = d
                # Promote the direct token for field discovery
                token = direct_token
                cookie_str = direct_cookies
            else:
                print(f"     ❌ {json.dumps(d)[:200]}")
    except ImportError:
        print("     ⚠️  curl_cffi not installed")
    except Exception as e:
        print(f"     ❌ Exception: {e}")

print()

if not working_strategy:
    print("❌  All strategies failed. Cannot reach Upwork GraphQL API.")
    print()
    print("DIAGNOSIS:")
    print("  • zone1 is an Unlocker API zone — cannot be used as HTTP proxy (407)")
    print("  • Unlocker API returns token but GraphQL rejects it (IP session mismatch)")
    print("  • curl_cffi direct — check output above for error details")
    print()
    print("RECOMMENDED FIX:")
    print("  Create a 'Web Unlocker' proxy zone in your Bright Data dashboard.")
    print("  It will appear as a username/password zone at brd.superproxy.io:22225.")
    print("  Set BRIGHT_DATA_UNLOCKER_ZONE=<new_zone_name> in .env.")
    sys.exit(1)

print(f"✅  Working strategy: {working_strategy}")
print()


# ── Helpers for field discovery ────────────────────────────────────────────

def run_query(q: str) -> dict:
    if working_strategy in ("A", "B"):
        hdrs = {
            "Content-Type": "application/json",
            "Cookie": cookie_str,
            "Origin": "https://www.upwork.com",
        }
        if working_strategy == "A":
            hdrs["Authorization"] = f"Bearer {token}"
        o = unlocker("https://www.upwork.com/api/graphql/v1", "POST",
                     extra_headers=hdrs, body=json.dumps({"query": q}))
        return parse_graphql_response(o.get("body", "{}"))
    else:
        from curl_cffi import requests as cffi_requests
        r = cffi_requests.post(
            "https://www.upwork.com/api/graphql/v1",
            impersonate="chrome131",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Cookie": cookie_str,
                "Origin": "https://www.upwork.com",
            },
            json={"query": q},
            timeout=30,
        )
        return r.json()


# ── STEP 3: Field discovery ────────────────────────────────────────────────

print("=" * 60)
print("STEP 3: Extended field discovery")
print("=" * 60)

CANDIDATE_FIELDS = [
    ("contractorTier",     "contractorTier"),
    ("jobType",            "jobType"),
    ("type",               "type"),
    ("totalApplicants",    "totalApplicants"),
    ("applicantsCount",    "applicantsCount"),
    ("postedDateTime",     "postedDateTime"),
    ("postedOn",           "postedOn"),
    ("publishedOn",        "publishedOn"),
    ("hourlyBudgetMin",    "hourlyBudgetMin"),
    ("hourlyBudgetMax",    "hourlyBudgetMax"),
    ("budget_obj",         "budget { amount currencyCode }"),
    ("skills_prettyName",  "skills { prettyName }"),
    ("attrs",              "attrs { prefLabel }"),
    ("duration_label",     "duration { label }"),
    ("engagementDuration", "engagementDuration"),
    ("client_basic",       "client { totalPostedJobs totalHires }"),
    ("client_feedback",    "client { feedbackScore }"),
    ("client_location",    "client { location { country } }"),
    ("client_payment",     "client { paymentVerification }"),
    ("client_spent",       "client { totalSpent { amount } }"),
]

working_fields = []
for name, field_expr in CANDIDATE_FIELDS:
    q = f'query {{ marketplaceJobPostings(filter: {{query: "python"}}, pagination: {{first: 1}}) {{ edges {{ node {{ id {field_expr} }} }} }} }}'
    try:
        d = run_query(q)
        errs = d.get("errors")
        if errs:
            print(f"  ❌  {name:30s}  {errs[0].get('message','')[:70]}")
        else:
            first_key = field_expr.split("{")[0].strip().split()[0]
            node = (d.get("data", {}).get("marketplaceJobPostings", {})
                      .get("edges", [{}]))[0] if d.get("data") else {}
            node = node.get("node", {}) if isinstance(node, dict) else {}
            val = str(node.get(first_key, "?"))[:60]
            print(f"  ✅  {name:30s}  {val}")
            working_fields.append(field_expr)
    except Exception as e:
        print(f"  ⚠️   {name:30s}  {e}")

print()
print("=" * 60)
print(f"RESULT — strategy {working_strategy} works.")
print("WORKING FIELDS (copy into bright_data.py GRAPHQL_QUERY):")
print("=" * 60)
for f in working_fields:
    print(f"        {f}")
