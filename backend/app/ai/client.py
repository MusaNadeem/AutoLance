"""
FreelanceRadar — Claude AI Client
Centralized Anthropic SDK wrapper with retry logic and structured output parsing
"""
import json
import re
from typing import Any, Optional, Type, TypeVar
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import anthropic
from pydantic import BaseModel
import structlog

from app.config import settings

logger = structlog.get_logger()
T = TypeVar("T", bound=BaseModel)


class ClaudeClient:
    """Singleton Claude API client with retry and structured output support."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
        reraise=True,
    )
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a completion request and return raw text response."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.05,
    ) -> dict[str, Any]:
        """
        Complete with JSON enforcement.
        Forces Claude to return valid JSON, optionally validated against a Pydantic model.
        """
        json_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: Your response MUST be valid JSON only. "
            "No markdown, no code blocks, no prose. Start with {{ and end with }}."
        )

        raw_text = await self.complete(json_system, user_prompt, temperature=temperature)

        # Extract JSON from response (handles cases where model still wraps in markdown)
        json_str = self._extract_json(raw_text)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("Claude JSON parse error", raw=raw_text[:500], error=str(e))
            raise ValueError(f"Claude returned invalid JSON: {e}")

        if response_model:
            return response_model(**data).model_dump()

        return data

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks."""
        # Try to find JSON block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return text[start:end]

        return text

    async def count_tokens(self, text: str) -> int:
        """Estimate token count for a text string."""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4


# Singleton instance
claude = ClaudeClient()
