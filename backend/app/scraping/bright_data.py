"""
Bright Data Scraping Engine
Fetches Upwork job search pages via Bright Data Unlocker API,
then parses the __NUXT__ server-rendered JSON embedded in the HTML.
"""
import asyncio
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
import requests
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger()

UPWORK_SEARCH_URLS = [
    "https://www.upwork.com/nx/search/jobs?q=python&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=react&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=fullstack&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=machine+learning&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=node.js&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=typescript&sort=recency",
]


class BrightDataClient:
    """
    Fetches real Upwork jobs via Bright Data Unlocker API.

    Flow:
        scrape_jobs()
          → _fetch_search_page(url)        # POST api.brightdata.com/request
          → _parse_nuxt_html(html)         # decode IIFE + extract jobs array
          → _map_nuxt_jobs(raw_jobs, vars) # resolve variable refs → pipeline dicts
    """

    def __init__(self):
        self.api_key       = settings.BRIGHT_DATA_API_KEY
        self.unlocker_zone = settings.BRIGHT_DATA_UNLOCKER_ZONE
        self.username      = settings.BRIGHT_DATA_USERNAME
        self.password      = settings.BRIGHT_DATA_PASSWORD
        self.host          = settings.BRIGHT_DATA_HOST
        self.port          = settings.BRIGHT_DATA_PORT
        self.collector_id  = "c_mploxioqxid2gjlhg"
        self.base_url      = "https://api.brightdata.com"

    # ── Unlocker API fetch ─────────────────────────────────────────────────

    # ── Redis HTML cache ───────────────────────────────────────────────────
    # Caches successful Unlocker API responses for SCRAPE_CACHE_TTL seconds.
    # The Celery beat runs every 15 min; a 14-min cache ensures each beat cycle
    # makes at most one real Bright Data request per URL, regardless of how many
    # manual triggers happen in between.

    _CACHE_TTL = 840  # 14 minutes

    def _cache_key(self, url: str) -> str:
        return f"scrape:html:{hashlib.md5(url.encode()).hexdigest()}"

    def _get_cached_html(self, url: str) -> Optional[str]:
        try:
            import redis as _redis
            r = _redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            val = r.get(self._cache_key(url))
            return val.decode("utf-8") if val else None
        except Exception:
            return None

    def _set_cached_html(self, url: str, html: str) -> None:
        try:
            import redis as _redis
            r = _redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            r.setex(self._cache_key(url), self._CACHE_TTL, html.encode("utf-8"))
        except Exception:
            pass

    # ── GraphQL scraping (preferred — faster + more stable than NUXT parser) ─

    # GraphQL query using field names confirmed to exist on Upwork's API.
    # `filter` argument was found invalid; `searchExpression` is the correct one.
    # If this query starts returning errors, run backend/scripts/test_graphql.py
    # to re-discover field names.
    _GQL_QUERY = """
    query JobSearch($query: String!, $count: Int) {
      marketplaceJobPostings(
        searchExpression: { query: $query }
        pagination: { first: $count }
      ) {
        edges {
          node {
            id
            title
            description
            ciphertext
            premium
            contractorTier
            jobType
            totalApplicants
            postedDateTime
            hourlyBudgetMin
            hourlyBudgetMax
            budget { amount currencyCode }
            skills { prettyName }
            duration { label }
            client {
              totalPostedJobs totalHires feedbackScore
              location { country }
              paymentVerification
              totalSpent { amount }
            }
          }
        }
      }
    }
    """

    def _get_visitor_token(self) -> Optional[str]:
        """
        Fetch Upwork homepage via Bright Data Unlocker API to get visitor_gql_token.
        This token has elevated scope (Bright Data bypasses Cloudflare bot detection)
        which is required to query the GraphQL API.
        """
        resp = requests.post(
            f"{self.base_url}/request",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"zone": self.unlocker_zone, "url": "https://www.upwork.com", "format": "json"},
            timeout=90,
        )
        resp.raise_for_status()
        outer = resp.json()
        raw = outer.get("headers", {}).get("set-cookie", "")
        if isinstance(raw, list):
            raw = ",".join(raw)
        cookies: dict = {}
        for chunk in re.split(r",\s*(?=[A-Za-z_]+=)", raw):
            m = re.match(r"([A-Za-z_][A-Za-z0-9_\-]*)=([^;,\s]+)", chunk.strip())
            if m:
                cookies[m.group(1)] = m.group(2)
        return cookies.get("visitor_gql_token")

    def _graphql_query(self, token: str, keyword: str, count: int = 20) -> list[dict]:
        """
        Query Upwork's GraphQL endpoint via curl_cffi (Chrome TLS impersonation).
        The visitor_gql_token obtained from Bright Data has the required scope.
        Falls back gracefully if curl_cffi is not available.
        """
        try:
            from curl_cffi import requests as cffi_requests
        except ImportError:
            raise RuntimeError("curl_cffi not installed — GraphQL path unavailable")

        cookie_str = f"visitor_gql_token={token}"
        r = cffi_requests.post(
            "https://www.upwork.com/api/graphql/v1",
            impersonate="chrome131",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Cookie": cookie_str,
                "Origin": "https://www.upwork.com",
            },
            json={"query": self._GQL_QUERY, "variables": {"query": keyword, "count": count}},
            timeout=30,
        )
        data = r.json()

        if data.get("errors"):
            first_err = data["errors"][0].get("message", "")
            raise RuntimeError(f"GraphQL error: {first_err[:120]}")

        edges = (
            data.get("data", {})
                .get("marketplaceJobPostings", {})
                .get("edges", [])
        )
        return [e["node"] for e in edges if e.get("node")]

    def _map_graphql_jobs(self, nodes: list[dict]) -> list[dict]:
        """Convert GraphQL job nodes to pipeline format."""
        jobs = []
        for node in nodes:
            cipher    = (node.get("ciphertext") or "").lstrip("~").lstrip("0")
            job_type  = (node.get("jobType") or "").lower()
            budget_type = "fixed" if "fixed" in job_type else "hourly"
            budget    = node.get("budget") or {}
            budget_amt = budget.get("amount")
            skills    = [s["prettyName"] for s in (node.get("skills") or []) if s.get("prettyName")]
            client_raw = node.get("client") or {}

            posted_at = None
            raw_date  = node.get("postedDateTime")
            if raw_date:
                try:
                    posted_at = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).isoformat()
                except Exception:
                    pass

            jobs.append({
                "upwork_job_id":   node.get("id", ""),
                "title":           self._strip_html(node.get("title", "")),
                "description":     self._strip_html(node.get("description") or "")[:2000],
                "url":             f"https://www.upwork.com/jobs/~0{cipher}" if cipher else "",
                "budget_type":     budget_type,
                "budget_min":      float(budget_amt) if budget_amt and budget_type == "fixed" else None,
                "budget_max":      float(budget_amt) if budget_amt and budget_type == "fixed" else None,
                "hourly_rate_min": node.get("hourlyBudgetMin"),
                "hourly_rate_max": node.get("hourlyBudgetMax"),
                "required_skills": list(dict.fromkeys(skills)),
                "experience_level":node.get("contractorTier"),
                "project_length":  (node.get("duration") or {}).get("label"),
                "proposal_count":  node.get("totalApplicants", 0) or 0,
                "posted_at":       posted_at,
                "is_featured":     node.get("premium", False),
                "client_country":  (client_raw.get("location") or {}).get("country"),
                "payment_verified":client_raw.get("paymentVerification") == "VERIFIED",
                "client_total_spent": (client_raw.get("totalSpent") or {}).get("amount"),
                "client_hire_rate":   client_raw.get("feedbackScore"),
                "client_total_hires": client_raw.get("totalHires"),
            })
        return [j for j in jobs if j["upwork_job_id"]]

    # ── Unlocker API fetch ─────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=5, max=20))
    def _fetch_search_page(self, url: str, timeout: int = 120) -> str:
        """
        Fetch an Upwork search results page through Bright Data Unlocker API.
        Checks Redis cache first — a cache hit avoids the slow Bright Data call
        entirely and returns in milliseconds.
        Returns the raw HTML string. Raises on HTTP error or timeout.
        """
        cached = self._get_cached_html(url)
        if cached:
            logger.info("HTML served from cache", url=url.split("q=")[1].split("&")[0] if "q=" in url else url[:50])
            return cached

        resp = requests.post(
            f"{self.base_url}/request",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"zone": self.unlocker_zone, "url": url, "format": "json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        outer = resp.json()
        html = outer.get("body", "")
        inner_status = outer.get("status_code", 0)
        if inner_status and int(inner_status) >= 400:
            raise RuntimeError(f"Upwork returned HTTP {inner_status}")
        if not html or len(html) < 10_000:
            raise RuntimeError(f"Response too short ({len(html)} bytes) — likely a block page")

        self._set_cached_html(url, html)
        return html

    # ── __NUXT__ parser ────────────────────────────────────────────────────

    def _parse_nuxt_html(self, html: str) -> list[dict]:
        """
        Parse job listings from Upwork's server-rendered __NUXT__ HTML.

        Upwork embeds all search result data in:
            window.__NUXT__=(function(a,b,c,...){ return {...} }(val0,val1,...))

        Variable substitution is used to compress repeated strings (skill names,
        experience levels, duration labels). We decode the variable table first,
        then resolve each reference when reading job fields.
        """
        if "__NUXT__" not in html:
            logger.warning("__NUXT__ not found in HTML")
            return []

        # ── Build variable lookup from IIFE params/args ───────────────────
        func_m = re.search(r"window\.__NUXT__=\(function\(([^)]+)\)", html)
        if not func_m:
            logger.warning("Cannot find __NUXT__ IIFE header")
            return []

        params = [p.strip() for p in func_m.group(1).split(",")]

        # The call args are between the last '}(' and the closing '))'
        script_end = re.search(r"</script>", html[func_m.start():])
        region = html[func_m.start():func_m.start() + script_end.start()] if script_end else html[func_m.start():]
        args_m = re.search(r"\}\((.+)\)\)", region, re.DOTALL)
        if not args_m:
            logger.warning("Cannot find __NUXT__ IIFE arguments")
            return []

        lookup = self._build_var_lookup(params, args_m.group(1))

        # ── Find the jobs array ───────────────────────────────────────────
        jobs_array_raw = self._extract_jobs_array(html)
        if not jobs_array_raw:
            return []

        return self._map_nuxt_jobs(jobs_array_raw, lookup)

    def _build_var_lookup(self, params: list[str], args_raw: str) -> dict:
        """Parse IIFE call arguments and map them to parameter names."""
        args = self._split_js_args(args_raw)
        lookup: dict = {}
        for i, param in enumerate(params):
            if i >= len(args):
                break
            val = args[i].strip()
            if val == "null":
                lookup[param] = None
            elif val == "true":
                lookup[param] = True
            elif val == "false":
                lookup[param] = False
            elif val.startswith('"') and val.endswith('"'):
                inner = val[1:-1]
                try:
                    inner = inner.encode("raw_unicode_escape").decode("unicode_escape")
                except Exception:
                    pass
                lookup[param] = inner
            else:
                try:
                    lookup[param] = int(val)
                except ValueError:
                    try:
                        lookup[param] = float(val)
                    except ValueError:
                        lookup[param] = val
        return lookup

    def _split_js_args(self, s: str) -> list[str]:
        """Split a JS argument list by comma, respecting strings and brackets."""
        args: list[str] = []
        depth = 0
        in_str = False
        escape = False
        cur: list[str] = []
        for c in s:
            if escape:
                cur.append(c); escape = False; continue
            if c == "\\" and in_str:
                cur.append(c); escape = True; continue
            if c == '"' and not in_str:
                in_str = True; cur.append(c); continue
            if c == '"' and in_str:
                in_str = False; cur.append(c); continue
            if not in_str:
                if c in "([{":
                    depth += 1
                elif c in ")]}":
                    depth -= 1
                if c == "," and depth == 0:
                    args.append("".join(cur).strip())
                    cur = []; continue
            cur.append(c)
        if cur:
            args.append("".join(cur).strip())
        return args

    def _extract_jobs_array(self, html: str) -> str:
        """Find the jobsSearch.jobs array and return its raw contents."""
        for match in re.finditer(r"jobs:\[", html):
            ctx = html[match.start():match.start() + 200]
            if re.search(r'uid:"\d{15,}"', ctx):
                bracket_pos = html.index("[", match.start())
                array_start = bracket_pos + 1
                depth = 1
                in_str = False
                escape = False
                for pos in range(array_start, len(html)):
                    c = html[pos]
                    if escape:
                        escape = False; continue
                    if c == "\\" and in_str:
                        escape = True; continue
                    if c == '"' and not in_str:
                        in_str = True; continue
                    if c == '"' and in_str:
                        in_str = False; continue
                    if not in_str:
                        if c == "[":
                            depth += 1
                        elif c == "]":
                            depth -= 1
                            if depth == 0:
                                return html[array_start:pos]
        logger.warning("No jobs array with 19-digit UIDs found in HTML")
        return ""

    def _map_nuxt_jobs(self, array_raw: str, lookup: dict) -> list[dict]:
        """Parse individual job objects from the raw array string."""
        job_positions = [m.start() for m in re.finditer(r'\{uid:"\d{15,}"', array_raw)]
        jobs: list[dict] = []

        for i, start in enumerate(job_positions):
            end = job_positions[i + 1] if i + 1 < len(job_positions) else len(array_raw)
            block = array_raw[start:end]

            uid       = self._get_str(block, "uid")
            cipher    = (self._get_str(block, "ciphertext") or "").lstrip("~").lstrip("0")
            title     = self._strip_html(self._get_str(block, "title") or "")
            desc      = self._strip_html(self._get_str(block, "description") or "")
            pub_date  = self._get_str(block, "publishedOn")
            jtype     = self._get_field(block, "type", lookup)
            tier      = self._get_field(block, "tierText", lookup)
            dur       = self._get_field(block, "durationLabel", lookup)
            ptier     = self._get_field(block, "proposalsTier", lookup)
            premium   = self._get_field(block, "premium", lookup)

            # Budget — infer type from available fields when variable ref fails
            fixed_m = re.search(r"amount:\{amount:(-?[\d.]+)", block)
            fixed_amt = float(fixed_m.group(1)) if fixed_m else None
            hourly_min = self._get_num(block, "min")
            hourly_max = self._get_num(block, "max")
            if isinstance(jtype, str):
                budget_type = "hourly" if "hourly" in jtype.lower() else "fixed"
            else:
                budget_type = "hourly" if (hourly_min is not None or hourly_max is not None) else "fixed"

            # Skills
            skills: list[str] = []
            seen: set[str] = set()
            for attr_m in re.finditer(r"prefLabel:([^,}]+)", block):
                raw_val = attr_m.group(1).strip()
                resolved = self._resolve(raw_val, lookup)
                if resolved and isinstance(resolved, str) and len(resolved) > 1:
                    if resolved not in seen:
                        skills.append(resolved); seen.add(resolved)

            # Proposal count from proposalsTier string
            proposal_count = 0
            if isinstance(ptier, str):
                low_ptier = ptier.lower()
                if "less than 5" in low_ptier:
                    proposal_count = 2
                elif "5 to 10" in low_ptier:
                    proposal_count = 7
                elif "10 to 15" in low_ptier:
                    proposal_count = 12
                elif "15 to 20" in low_ptier:
                    proposal_count = 17
                elif "20 to 50" in low_ptier:
                    proposal_count = 35
                elif "50" in low_ptier:
                    proposal_count = 55

            # Normalise posted_at to ISO format
            posted_iso: Optional[str] = None
            if pub_date:
                try:
                    dt = datetime.fromisoformat(str(pub_date).replace("Z", "+00:00"))
                    posted_iso = dt.isoformat()
                except Exception:
                    # Sometimes publishedOn is a timestamp in ms
                    try:
                        ts = int(str(pub_date))
                        if ts > 1e12:
                            ts //= 1000
                        posted_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                    except Exception:
                        pass

            if not uid or not title:
                continue

            jobs.append({
                "upwork_job_id":   uid,
                "title":           title,
                "description":     desc[:2000],
                "url":             f"https://www.upwork.com/jobs/~0{cipher}" if cipher else "",
                "budget_type":     budget_type,
                "budget_min":      fixed_amt if budget_type == "fixed" else None,
                "budget_max":      fixed_amt if budget_type == "fixed" else None,
                "hourly_rate_min": hourly_min,
                "hourly_rate_max": hourly_max,
                "required_skills": skills,
                "experience_level":str(tier) if tier else None,
                "project_length":  str(dur) if dur else None,
                "proposal_count":  proposal_count,
                "posted_at":       posted_iso,
                "is_featured":     premium is True,
            })

        logger.info("Parsed jobs from __NUXT__", count=len(jobs))
        return jobs

    # ── Field extraction helpers ───────────────────────────────────────────

    def _resolve(self, val: str, lookup: dict):
        """Resolve a JS value: variable ref → lookup, or literal."""
        val = val.strip()
        if val in ("null", "undefined"):
            return None
        if val in ("true",):
            return True
        if val in ("false",):
            return False
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$", val):
            return lookup.get(val)
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    def _get_str(self, block: str, key: str) -> Optional[str]:
        """Extract a quoted string literal for a key."""
        m = re.search(rf'(?<![a-zA-Z]){re.escape(key)}:"((?:[^"\\]|\\.)*)"', block)
        if not m:
            return None
        raw = m.group(1)
        try:
            return raw.encode("raw_unicode_escape").decode("unicode_escape")
        except Exception:
            return raw

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove Upwork's search-highlight markup and any other HTML tags."""
        if not text:
            return text
        # Drop tags, collapse whitespace, decode common entities
        clean = re.sub(r"<[^>]+>", "", text)
        clean = (clean.replace("&amp;", "&").replace("&lt;", "<")
                      .replace("&gt;", ">").replace("&quot;", '"')
                      .replace("&#39;", "'").replace("&nbsp;", " "))
        return re.sub(r"\s+", " ", clean).strip()

    def _get_field(self, block: str, key: str, lookup: dict):
        """Extract a field that may be a literal string or variable reference."""
        v = self._get_str(block, key)
        if v is not None:
            return v
        m = re.search(rf"(?<![a-zA-Z]){re.escape(key)}:([a-zA-Z_$][a-zA-Z0-9_$]*)", block)
        if m:
            return self._resolve(m.group(1), lookup)
        return None

    def _get_num(self, block: str, key: str) -> Optional[float]:
        m = re.search(rf"(?<![a-zA-Z]){re.escape(key)}:(-?[\d.]+)", block)
        return float(m.group(1)) if m else None

    # ── Main public scraping method ────────────────────────────────────────

    @staticmethod
    def _keywords_to_urls(keywords: list[str]) -> list[str]:
        """Convert plain keyword strings to Upwork search URLs."""
        import urllib.parse
        return [
            f"https://www.upwork.com/nx/search/jobs?q={urllib.parse.quote_plus(kw)}&sort=recency"
            for kw in keywords if kw.strip()
        ]

    def _scrape_single_url(self, url: str, gql_token: Optional[str] = None) -> tuple[str, list[dict]]:
        """
        Fetch and parse one search URL. Returns (keyword, jobs).
        Strategy:
          1. If gql_token is provided, try GraphQL first (faster, more stable).
          2. Fall back to NUXT HTML parsing via Unlocker API (slower, fragile).
        Raises on failure so the caller can log and continue.
        """
        import urllib.parse as _up
        keyword = _up.unquote_plus(url.split("q=")[1].split("&")[0]) if "q=" in url else url

        # Try GraphQL path (fast: ~5s vs 90-300s for NUXT)
        if gql_token:
            try:
                nodes = self._graphql_query(gql_token, keyword)
                jobs  = self._map_graphql_jobs(nodes)
                if jobs:
                    logger.info("Scraped via GraphQL", keyword=keyword, count=len(jobs))
                    return keyword, jobs
                logger.warning("GraphQL returned 0 jobs — falling back to NUXT", keyword=keyword)
            except Exception as e:
                logger.warning("GraphQL failed — falling back to NUXT", keyword=keyword, error=str(e)[:120])

        # NUXT HTML fallback
        html = self._fetch_search_page(url, timeout=120)
        jobs = self._parse_nuxt_html(html)
        return keyword, jobs

    def scrape_jobs(self, keywords: Optional[list[str]] = None) -> list[dict]:
        """
        Scrape Upwork jobs via Bright Data Unlocker API + __NUXT__ HTML parsing.

        `keywords` is a list of plain search terms built from the user's profile.
        When None, uses the hardcoded UPWORK_SEARCH_URLS defaults.

        URLs are fetched in parallel (max 3 concurrent) to reduce total wall time.
        Partial success is accepted: if any URL returns jobs, those are used.
        Falls back to mock data only when credentials are absent or ALL fetches fail.
        Called synchronously from Celery tasks via run_in_executor.
        """
        if not self.api_key or not self.unlocker_zone:
            logger.warning("Bright Data credentials not configured — using mock data")
            return self._get_mock_jobs()

        if keywords:
            targets = self._keywords_to_urls(keywords[:3])
        else:
            targets = UPWORK_SEARCH_URLS
        logger.info("Starting scrape", keywords=keywords or "defaults", urls=len(targets))

        # Try to get a visitor_gql_token once for all parallel workers.
        # The token obtained via Bright Data Unlocker has elevated scope —
        # it allows GraphQL queries that plain visitor tokens can't make.
        # Failure is non-fatal; workers fall back to NUXT parsing.
        gql_token: Optional[str] = None
        try:
            gql_token = self._get_visitor_token()
            if gql_token:
                logger.info("visitor_gql_token obtained — will try GraphQL first")
            else:
                logger.info("No token obtained — using NUXT parser only")
        except Exception as e:
            logger.warning("Token fetch failed", error=str(e)[:100])

        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_jobs: list[dict] = []
        seen_ids: set[str] = set()
        successes = 0
        failures  = 0

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(self._scrape_single_url, url, gql_token): url for url in targets}
            for future in as_completed(futures, timeout=300):
                url = futures[future]
                keyword = url.split("q=")[1].split("&")[0] if "q=" in url else url
                try:
                    kw, jobs = future.result()
                    new = [j for j in jobs if j["upwork_job_id"] not in seen_ids]
                    seen_ids.update(j["upwork_job_id"] for j in new)
                    all_jobs.extend(new)
                    successes += 1
                    logger.info("Scraped jobs", keyword=kw, count=len(new))
                except Exception as e:
                    failures += 1
                    logger.error("Failed to scrape URL", keyword=keyword, error=str(e)[:200])

        logger.info("Scrape complete", total=len(all_jobs), success_urls=successes, failed_urls=failures)

        if not all_jobs:
            logger.warning("All %d URL(s) failed — using mock data", failures)
            return self._get_mock_jobs()

        return all_jobs

    # ── DCA collector (legacy — kept for backward compat) ──────────────────

    async def trigger_collection(self, urls: Optional[list[str]] = None) -> str:
        if not self.api_key:
            return "mock_snapshot_id"
        target_urls = urls or UPWORK_SEARCH_URLS
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/dca/trigger",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                params={"collector": self.collector_id, "queue_next": "1"},
                json=[{"url": u} for u in target_urls],
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            cid = data.get("collection_id") or data.get("snapshot_id")
            logger.info("DCA collection triggered", collection_id=cid)
            return cid

    async def wait_for_collection(self, collection_id: str, max_wait: int = 300, poll: int = 15) -> list[dict]:
        if collection_id == "mock_snapshot_id":
            return self._get_mock_jobs()
        endpoint = f"{self.base_url}/dca/dataset?id={collection_id}"
        elapsed = 0
        async with httpx.AsyncClient() as client:
            while elapsed < max_wait:
                response = await client.get(endpoint, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                elif response.status_code != 202:
                    response.raise_for_status()
                await asyncio.sleep(poll)
                elapsed += poll
        return []

    async def trigger_dataset_collection(self, urls: Optional[list[str]] = None) -> str:
        return await self.trigger_collection(urls)

    async def wait_for_snapshot(self, snapshot_id: str, max_wait_seconds: int = 300, poll_interval: int = 15) -> list[dict]:
        return await self.wait_for_collection(snapshot_id, max_wait_seconds, poll_interval)

    # ── Mock data ──────────────────────────────────────────────────────────

    def _get_mock_jobs(self) -> list[dict]:
        return [
            {
                "upwork_job_id": "mock_001",
                "title": "Build AI-powered SaaS dashboard with FastAPI + React",
                "description": "We are building an analytics SaaS and need a senior full-stack engineer to architect the backend API (FastAPI, PostgreSQL, Redis) and integrate with our React frontend. Must have experience with async Python and data visualization.",
                "url": "https://www.upwork.com/jobs/mock-001",
                "budget_type": "fixed", "budget_min": 4500.0, "budget_max": 6000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "FastAPI", "React", "PostgreSQL", "Redis"],
                "experience_level": "Expert", "project_length": "1 to 3 months",
                "proposal_count": 8, "posted_at": "2026-05-29T08:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "United States", "client_total_spent": 52000, "client_hire_rate": 82.0, "client_total_hires": 14,
            },
            {
                "upwork_job_id": "mock_002",
                "title": "Python backend engineer for fintech startup — long term",
                "description": "Series A fintech startup looking for a Python engineer to own our transaction processing service. You'll work with Celery, Kafka, and PostgreSQL. We value clean code and strong test coverage.",
                "url": "https://www.upwork.com/jobs/mock-002",
                "budget_type": "hourly", "budget_min": None, "budget_max": None,
                "hourly_rate_min": 65.0, "hourly_rate_max": 95.0,
                "required_skills": ["Python", "Celery", "PostgreSQL", "Kafka", "Docker"],
                "experience_level": "Senior", "project_length": "More than 6 months",
                "proposal_count": 4, "posted_at": "2026-05-29T07:30:00+00:00",
                "is_featured": True, "payment_verified": True,
                "client_country": "United Kingdom", "client_total_spent": 120000, "client_hire_rate": 91.0, "client_total_hires": 23,
            },
            {
                "upwork_job_id": "mock_003",
                "title": "Next.js 15 + TypeScript frontend for B2B platform",
                "description": "We need an experienced Next.js developer to build a complex B2B dashboard. Features include real-time charts (Recharts), role-based access, and a design system using Radix UI + Tailwind.",
                "url": "https://www.upwork.com/jobs/mock-003",
                "budget_type": "fixed", "budget_min": 3200.0, "budget_max": 4800.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Next.js", "TypeScript", "Tailwind CSS", "Radix UI", "Recharts"],
                "experience_level": "Senior", "project_length": "1 to 3 months",
                "proposal_count": 12, "posted_at": "2026-05-29T06:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Germany", "client_total_spent": 38000, "client_hire_rate": 78.0, "client_total_hires": 9,
            },
            {
                "upwork_job_id": "mock_004",
                "title": "Machine learning engineer — NLP pipeline for document classification",
                "description": "Building an automated document classification system using transformer models (HuggingFace). Need experience with fine-tuning BERT/RoBERTa, deploying models as REST APIs, and working with large document corpora.",
                "url": "https://www.upwork.com/jobs/mock-004",
                "budget_type": "fixed", "budget_min": 8000.0, "budget_max": 12000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "HuggingFace", "NLP", "PyTorch", "FastAPI"],
                "experience_level": "Expert", "project_length": "3 to 6 months",
                "proposal_count": 3, "posted_at": "2026-05-29T05:30:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Canada", "client_total_spent": 89000, "client_hire_rate": 88.0, "client_total_hires": 19,
            },
            {
                "upwork_job_id": "mock_005",
                "title": "Scraping & data pipeline — real estate market data",
                "description": "Need a Python developer to build a scraping system for real estate listings across 5 sites, normalize the data, and load into a PostgreSQL warehouse. Must handle rate limiting, proxies, and schedule via Celery Beat.",
                "url": "https://www.upwork.com/jobs/mock-005",
                "budget_type": "fixed", "budget_min": 2800.0, "budget_max": 3500.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "BeautifulSoup", "Celery", "PostgreSQL", "Scrapy"],
                "experience_level": "Intermediate", "project_length": "1 to 3 months",
                "proposal_count": 18, "posted_at": "2026-05-28T22:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Australia", "client_total_spent": 15000, "client_hire_rate": 71.0, "client_total_hires": 6,
            },
            {
                "upwork_job_id": "mock_006",
                "title": "Senior React developer — complex state management & performance",
                "description": "Our React app has severe performance issues due to unnecessary re-renders and poor state architecture. We need an expert to audit, refactor with Zustand, implement code-splitting, and document the patterns.",
                "url": "https://www.upwork.com/jobs/mock-006",
                "budget_type": "hourly", "budget_min": None, "budget_max": None,
                "hourly_rate_min": 75.0, "hourly_rate_max": 110.0,
                "required_skills": ["React", "TypeScript", "Zustand", "Webpack", "Performance"],
                "experience_level": "Expert", "project_length": "Less than 1 month",
                "proposal_count": 6, "posted_at": "2026-05-29T04:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Netherlands", "client_total_spent": 67000, "client_hire_rate": 85.0, "client_total_hires": 17,
            },
            {
                "upwork_job_id": "mock_007",
                "title": "Backend API architect — microservices migration",
                "description": "We are splitting a Django monolith into microservices using FastAPI and Docker Compose. Looking for an architect to design the service boundaries, implement inter-service communication (gRPC + REST), and set up observability.",
                "url": "https://www.upwork.com/jobs/mock-007",
                "budget_type": "hourly", "budget_min": None, "budget_max": None,
                "hourly_rate_min": 90.0, "hourly_rate_max": 140.0,
                "required_skills": ["FastAPI", "Docker", "gRPC", "PostgreSQL", "Prometheus"],
                "experience_level": "Expert", "project_length": "3 to 6 months",
                "proposal_count": 2, "posted_at": "2026-05-29T03:00:00+00:00",
                "is_featured": True, "payment_verified": True,
                "client_country": "United States", "client_total_spent": 240000, "client_hire_rate": 94.0, "client_total_hires": 41,
            },
            {
                "upwork_job_id": "mock_008",
                "title": "TypeScript SDK development for developer API",
                "description": "We are building a TypeScript SDK for our REST API. Need a developer with deep TS expertise (generics, conditional types, declaration files) to write the SDK, auto-generated types from OpenAPI spec, and comprehensive tests with Vitest.",
                "url": "https://www.upwork.com/jobs/mock-008",
                "budget_type": "fixed", "budget_min": 3800.0, "budget_max": 5200.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["TypeScript", "OpenAPI", "Vitest", "Node.js", "REST API"],
                "experience_level": "Senior", "project_length": "1 to 3 months",
                "proposal_count": 7, "posted_at": "2026-05-28T20:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Sweden", "client_total_spent": 28000, "client_hire_rate": 80.0, "client_total_hires": 8,
            },
            {
                "upwork_job_id": "mock_009",
                "title": "Full-stack developer — MVP SaaS app (2 month deadline)",
                "description": "Need a full-stack developer to build an MVP for a project management SaaS. Stack: FastAPI backend, Next.js frontend, PostgreSQL, hosted on Railway. We have Figma designs ready. Strong communicator required.",
                "url": "https://www.upwork.com/jobs/mock-009",
                "budget_type": "fixed", "budget_min": 6000.0, "budget_max": 9000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["FastAPI", "Next.js", "PostgreSQL", "Figma", "Railway"],
                "experience_level": "Senior", "project_length": "1 to 3 months",
                "proposal_count": 14, "posted_at": "2026-05-28T18:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Singapore", "client_total_spent": 9500, "client_hire_rate": 69.0, "client_total_hires": 4,
            },
            {
                "upwork_job_id": "mock_010",
                "title": "Django → FastAPI migration + async refactor",
                "description": "We have a large Django 3.2 app that needs to be migrated to FastAPI with full async support. Need someone who has done this migration before. SQLAlchemy 2.0 async ORM, Alembic migrations, Pydantic v2 schemas.",
                "url": "https://www.upwork.com/jobs/mock-010",
                "budget_type": "hourly", "budget_min": None, "budget_max": None,
                "hourly_rate_min": 70.0, "hourly_rate_max": 100.0,
                "required_skills": ["Python", "FastAPI", "SQLAlchemy", "Alembic", "Django"],
                "experience_level": "Expert", "project_length": "3 to 6 months",
                "proposal_count": 9, "posted_at": "2026-05-28T16:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "United States", "client_total_spent": 44000, "client_hire_rate": 77.0, "client_total_hires": 11,
            },
            {
                "upwork_job_id": "mock_011",
                "title": "Node.js backend — real-time multiplayer game API",
                "description": "Building a browser-based multiplayer game. Need a Node.js developer experienced with Socket.io, Redis pub/sub for game state synchronisation, and low-latency REST endpoints. 10k concurrent users target.",
                "url": "https://www.upwork.com/jobs/mock-011",
                "budget_type": "fixed", "budget_min": 5500.0, "budget_max": 8000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Node.js", "Socket.io", "Redis", "TypeScript", "AWS"],
                "experience_level": "Senior", "project_length": "3 to 6 months",
                "proposal_count": 11, "posted_at": "2026-05-28T14:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Japan", "client_total_spent": 31000, "client_hire_rate": 73.0, "client_total_hires": 7,
            },
            {
                "upwork_job_id": "mock_012",
                "title": "Data engineer — dbt + BigQuery pipeline for e-commerce analytics",
                "description": "We run a mid-size e-commerce store and need a data engineer to build our analytics layer. dbt models on BigQuery, Airflow orchestration, Metabase dashboards, and documentation. Ongoing role.",
                "url": "https://www.upwork.com/jobs/mock-012",
                "budget_type": "hourly", "budget_min": None, "budget_max": None,
                "hourly_rate_min": 60.0, "hourly_rate_max": 85.0,
                "required_skills": ["Python", "dbt", "BigQuery", "Airflow", "SQL"],
                "experience_level": "Senior", "project_length": "More than 6 months",
                "proposal_count": 5, "posted_at": "2026-05-28T12:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Canada", "client_total_spent": 72000, "client_hire_rate": 87.0, "client_total_hires": 16,
            },
            {
                "upwork_job_id": "mock_013",
                "title": "AWS infrastructure — Terraform + ECS deployment automation",
                "description": "Seeking a DevOps engineer to set up our AWS infrastructure with Terraform: ECS Fargate, RDS, ElastiCache, CloudFront, and CI/CD via GitHub Actions. Must follow least-privilege IAM and have production experience.",
                "url": "https://www.upwork.com/jobs/mock-013",
                "budget_type": "fixed", "budget_min": 4200.0, "budget_max": 6500.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["AWS", "Terraform", "Docker", "GitHub Actions", "ECS"],
                "experience_level": "Expert", "project_length": "Less than 1 month",
                "proposal_count": 16, "posted_at": "2026-05-28T10:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Ireland", "client_total_spent": 55000, "client_hire_rate": 84.0, "client_total_hires": 13,
            },
            {
                "upwork_job_id": "mock_014",
                "title": "Claude API integration — AI writing assistant for legal documents",
                "description": "Building an AI writing assistant using Claude claude-sonnet-4-6. Need a Python developer to integrate the Anthropic SDK, implement streaming responses, build the FastAPI wrapper, and handle prompt engineering for legal document review.",
                "url": "https://www.upwork.com/jobs/mock-014",
                "budget_type": "fixed", "budget_min": 3500.0, "budget_max": 5000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "FastAPI", "Anthropic API", "Prompt Engineering", "PostgreSQL"],
                "experience_level": "Senior", "project_length": "1 to 3 months",
                "proposal_count": 6, "posted_at": "2026-05-28T09:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "United States", "client_total_spent": 19000, "client_hire_rate": 76.0, "client_total_hires": 5,
            },
            {
                "upwork_job_id": "mock_015",
                "title": "React Native app — fitness tracking with wearable BLE integration",
                "description": "Consumer fitness app using React Native + Expo. Requires BLE (Bluetooth Low Energy) integration with heart rate monitors, local SQLite storage, background tracking, and a clean UI. iOS + Android.",
                "url": "https://www.upwork.com/jobs/mock-015",
                "budget_type": "fixed", "budget_min": 7000.0, "budget_max": 11000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["React Native", "Expo", "TypeScript", "BLE", "SQLite"],
                "experience_level": "Senior", "project_length": "3 to 6 months",
                "proposal_count": 21, "posted_at": "2026-05-28T07:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Australia", "client_total_spent": 48000, "client_hire_rate": 79.0, "client_total_hires": 10,
            },
            {
                "upwork_job_id": "mock_016",
                "title": "Postgres performance tuning — 50M row OLTP database",
                "description": "Our PostgreSQL database is degrading under load. Need an expert to analyse slow query logs, add/fix indexes, rewrite bad queries, tune autovacuum, and implement connection pooling with pgBouncer. Read replica setup preferred.",
                "url": "https://www.upwork.com/jobs/mock-016",
                "budget_type": "fixed", "budget_min": 2500.0, "budget_max": 4000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["PostgreSQL", "pgBouncer", "SQL", "Query Optimisation", "Linux"],
                "experience_level": "Expert", "project_length": "Less than 1 month",
                "proposal_count": 7, "posted_at": "2026-05-28T06:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "France", "client_total_spent": 33000, "client_hire_rate": 83.0, "client_total_hires": 9,
            },
            {
                "upwork_job_id": "mock_017",
                "title": "Stripe billing integration — SaaS subscription with usage-based pricing",
                "description": "We need to integrate Stripe Billing into our FastAPI SaaS: subscription plans, metered usage billing, webhook handling, customer portal, and proration. Must have production Stripe experience.",
                "url": "https://www.upwork.com/jobs/mock-017",
                "budget_type": "fixed", "budget_min": 2200.0, "budget_max": 3500.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "Stripe", "FastAPI", "PostgreSQL", "Webhooks"],
                "experience_level": "Senior", "project_length": "Less than 1 month",
                "proposal_count": 9, "posted_at": "2026-05-28T05:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "United States", "client_total_spent": 26000, "client_hire_rate": 74.0, "client_total_hires": 7,
            },
            {
                "upwork_job_id": "mock_018",
                "title": "Python automation scripts — document processing & OCR pipeline",
                "description": "We process hundreds of PDFs daily. Need scripts to extract structured data using PyMuPDF + Tesseract OCR, classify document types, validate extracted fields, and export to a CSV/JSON pipeline. 95%+ accuracy required.",
                "url": "https://www.upwork.com/jobs/mock-018",
                "budget_type": "fixed", "budget_min": 1800.0, "budget_max": 2800.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "PyMuPDF", "Tesseract", "OCR", "Pandas"],
                "experience_level": "Intermediate", "project_length": "Less than 1 month",
                "proposal_count": 24, "posted_at": "2026-05-27T22:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Israel", "client_total_spent": 11000, "client_hire_rate": 68.0, "client_total_hires": 4,
            },
            {
                "upwork_job_id": "mock_019",
                "title": "Svelte/SvelteKit frontend — dashboard for IoT sensor data",
                "description": "We collect telemetry from 500+ IoT sensors and need a SvelteKit dashboard to visualise real-time and historical data. D3.js charts, WebSocket live updates, dark theme, and responsive. Backend API already built.",
                "url": "https://www.upwork.com/jobs/mock-019",
                "budget_type": "hourly", "budget_min": None, "budget_max": None,
                "hourly_rate_min": 55.0, "hourly_rate_max": 80.0,
                "required_skills": ["SvelteKit", "TypeScript", "D3.js", "WebSockets", "Tailwind CSS"],
                "experience_level": "Senior", "project_length": "1 to 3 months",
                "proposal_count": 13, "posted_at": "2026-05-27T20:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Denmark", "client_total_spent": 22000, "client_hire_rate": 81.0, "client_total_hires": 6,
            },
            {
                "upwork_job_id": "mock_020",
                "title": "LLM fine-tuning engineer — domain-specific Q&A chatbot",
                "description": "We want to fine-tune a small LLM (Mistral 7B or LLaMA 3.1 8B) on proprietary documentation for a customer support chatbot. Need experience with LoRA/QLoRA, PEFT, evaluation metrics (ROUGE, BERTScore), and deployment on Modal.",
                "url": "https://www.upwork.com/jobs/mock-020",
                "budget_type": "fixed", "budget_min": 5000.0, "budget_max": 8000.0,
                "hourly_rate_min": None, "hourly_rate_max": None,
                "required_skills": ["Python", "PyTorch", "HuggingFace", "LLM Fine-tuning", "LoRA"],
                "experience_level": "Expert", "project_length": "1 to 3 months",
                "proposal_count": 4, "posted_at": "2026-05-27T18:00:00+00:00",
                "is_featured": False, "payment_verified": True,
                "client_country": "Switzerland", "client_total_spent": 95000, "client_hire_rate": 90.0, "client_total_hires": 22,
            },
        ]


bright_data = BrightDataClient()
