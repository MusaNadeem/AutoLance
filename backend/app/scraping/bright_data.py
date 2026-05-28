"""
Bright Data Scraping Engine
Fetches Upwork job search pages via Bright Data Unlocker API,
then parses the __NUXT__ server-rendered JSON embedded in the HTML.
"""
import asyncio
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=10, max=60))
    def _fetch_search_page(self, url: str) -> str:
        """
        Fetch an Upwork search results page through Bright Data Unlocker API.
        Returns the raw HTML string. Raises on HTTP error or timeout.
        The Upwork search page takes 90-180s; 300s timeout handles this reliably.
        """
        resp = requests.post(
            f"{self.base_url}/request",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"zone": self.unlocker_zone, "url": url, "format": "json"},
            timeout=300,
        )
        resp.raise_for_status()
        outer = resp.json()
        html = outer.get("body", "")
        inner_status = outer.get("status_code", 0)
        if inner_status and int(inner_status) >= 400:
            raise RuntimeError(f"Upwork returned HTTP {inner_status} for {url}")
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
            title     = self._get_str(block, "title") or ""
            desc      = self._get_str(block, "description") or ""
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

    def scrape_jobs(self, keywords: Optional[list[str]] = None) -> list[dict]:
        """
        Scrape Upwork jobs via Bright Data Unlocker API + __NUXT__ HTML parsing.

        `keywords` is a list of plain search terms (e.g. ["Python", "FastAPI"]).
        When None, falls back to the hardcoded UPWORK_SEARCH_URLS defaults.
        Falls back to mock data when credentials are absent or all fetches fail.
        Called synchronously from Celery tasks via run_in_executor.
        """
        if not self.api_key or not self.unlocker_zone:
            logger.warning("Bright Data credentials not configured — using mock data")
            return self._get_mock_jobs()

        targets = (
            self._keywords_to_urls(keywords) if keywords else UPWORK_SEARCH_URLS
        )
        logger.info("Starting scrape", keywords=keywords or "defaults", urls=len(targets))

        all_jobs: list[dict] = []
        seen_ids: set[str] = set()

        for url in targets:
            keyword = url.split("q=")[1].split("&")[0] if "q=" in url else url
            try:
                html = self._fetch_search_page(url)
                jobs = self._parse_nuxt_html(html)
                new = [j for j in jobs if j["upwork_job_id"] not in seen_ids]
                seen_ids.update(j["upwork_job_id"] for j in new)
                all_jobs.extend(new)
                logger.info("Scraped jobs", keyword=keyword, count=len(new))
            except Exception as e:
                logger.error("Failed to scrape URL", keyword=keyword, error=str(e))

        if not all_jobs:
            logger.warning("All scrape attempts failed — using mock data")
            return self._get_mock_jobs()

        logger.info("Scrape complete", total=len(all_jobs))
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
                "upwork_job_id": f"mock_{i}",
                "title": f"Senior Python Developer for FastAPI Project {i}",
                "description": "We need an experienced Python developer...",
                "url": f"https://www.upwork.com/jobs/mock-{i}",
                "budget_type": "fixed",
                "budget_min": 2000 + (i * 500),
                "budget_max": 5000 + (i * 500),
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                "experience_level": "Expert",
                "project_length": "1 to 3 months",
                "proposal_count": 5 + i,
                "payment_verified": True,
                "client_country": "United States",
                "client_total_spent": 15000 + (i * 3000),
                "client_hire_rate": 75.5,
                "client_total_hires": 12 + i,
                "client_rating": 4.9,
                "posted_at": "2026-05-23T10:00:00Z",
            }
            for i in range(1, 11)
        ]


bright_data = BrightDataClient()
