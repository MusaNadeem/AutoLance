"""
Bright Data Scraping Engine
Web Scraper API + Web Unlocker client for Upwork job scraping.
"""
import asyncio
from typing import Any, Optional
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger()

UPWORK_SEARCH_URLS = [
    "https://www.upwork.com/nx/search/jobs?q=&sort=recency&page=1",
    "https://www.upwork.com/nx/search/jobs?q=python&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=react&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=fullstack&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=machine+learning&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=node.js&sort=recency",
    "https://www.upwork.com/nx/search/jobs?q=typescript&sort=recency",
]


class BrightDataClient:
    """Client for Bright Data Web Scraper API and Web Unlocker."""

    def __init__(self):
        self.api_key = settings.BRIGHT_DATA_API_KEY
        self.ws_zone = settings.BRIGHT_DATA_WS_ZONE
        self.unlocker_zone = settings.BRIGHT_DATA_UNLOCKER_ZONE
        self.dataset_id = settings.BRIGHT_DATA_WS_DATASET_ID
        self.base_url = "https://api.brightdata.com"

        # Proxy config for Web Unlocker
        self.proxy_url = (
            f"http://{settings.BRIGHT_DATA_USERNAME}:{settings.BRIGHT_DATA_PASSWORD}"
            f"@{settings.BRIGHT_DATA_HOST}:{settings.BRIGHT_DATA_PORT}"
        )

    @retry(
        stop=stop_after_attempt(settings.SCRAPE_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=5, max=60),
    )
    async def trigger_dataset_collection(
        self,
        urls: Optional[list[str]] = None,
    ) -> str:
        """
        Trigger a Bright Data Web Scraper dataset collection.
        Returns snapshot_id for polling.
        """
        if not self.api_key or not self.dataset_id:
            logger.warning("Bright Data not configured — using mock data")
            return "mock_snapshot_id"

        target_urls = urls or UPWORK_SEARCH_URLS
        payload = [{"url": url} for url in target_urls]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/datasets/v3/trigger",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                params={
                    "dataset_id": self.dataset_id,
                    "include_errors": "true",
                    "type": "discover_new",
                    "discover_by": "url",
                },
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            snapshot_id = data.get("snapshot_id")
            logger.info("Dataset collection triggered", snapshot_id=snapshot_id)
            return snapshot_id

    async def wait_for_snapshot(
        self,
        snapshot_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 15,
    ) -> list[dict]:
        """Poll for snapshot completion and return results."""
        if snapshot_id == "mock_snapshot_id":
            return self._get_mock_jobs()

        elapsed = 0
        async with httpx.AsyncClient() as client:
            while elapsed < max_wait_seconds:
                response = await client.get(
                    f"{self.base_url}/datasets/v3/snapshot/{snapshot_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"format": "json"},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info("Snapshot ready", count=len(data))
                    return data if isinstance(data, list) else [data]

                elif response.status_code == 202:
                    # Still processing
                    logger.debug("Snapshot still processing", elapsed=elapsed)
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
                else:
                    response.raise_for_status()

        logger.error("Snapshot timed out", snapshot_id=snapshot_id)
        return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def fetch_with_unlocker(self, url: str) -> str:
        """
        Fetch a specific URL using Bright Data Web Unlocker proxy.
        Returns raw HTML.
        """
        if not self.unlocker_zone:
            logger.warning("Web Unlocker not configured")
            return ""

        proxies = {"http://": self.proxy_url, "https://": self.proxy_url}

        async with httpx.AsyncClient(proxies=proxies, verify=False) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
                timeout=60.0,
            )
            return response.text

    def _get_mock_jobs(self) -> list[dict]:
        """Return mock job data for development/testing."""
        return [
            {
                "upwork_job_id": f"mock_{i}",
                "title": f"Senior Python Developer for FastAPI Project {i}",
                "description": "We need an experienced Python developer to build a scalable FastAPI backend with PostgreSQL, Redis, and Celery. Must have experience with async Python and Docker.",
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
