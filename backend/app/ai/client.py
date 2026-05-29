"""
AutoLance — AI Client
Uses the AI/ML API (aimlapi.com) which exposes Claude via an OpenAI-compatible
endpoint. Falls back to the Anthropic SDK if AIML_API_KEY is not set.
"""
import json
import re
from typing import Any, Optional, Type, TypeVar

import structlog
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()
T = TypeVar("T", bound=BaseModel)


class ClaudeClient:
    """
    Unified AI client.
    Priority: AIML_API_KEY (aimlapi.com OpenAI-compat) → ANTHROPIC_API_KEY (native SDK).
    """

    def __init__(self):
        self.model      = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self._client    = None      # lazy-initialised

    def _get_client(self):
        if self._client is not None:
            return self._client

        if settings.AIML_API_KEY:
            # AI/ML API — OpenAI-compatible endpoint
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key  = settings.AIML_API_KEY,
                base_url = settings.AIML_BASE_URL,
            )
            logger.info("AI client: AI/ML API", model=self.model, base=settings.AIML_BASE_URL)
        elif settings.ANTHROPIC_API_KEY:
            # Native Anthropic SDK (legacy path)
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("AI client: Anthropic SDK", model=self.model)
        else:
            raise RuntimeError(
                "No AI API key configured. Set AIML_API_KEY (recommended) "
                "or ANTHROPIC_API_KEY in your .env file."
            )

        return self._client

    async def complete(
        self,
        system_prompt: str,
        user_prompt:   str,
        temperature:   float         = 0.1,
        max_tokens:    Optional[int] = None,
    ) -> str:
        """Send a completion request and return raw text response."""
        client = self._get_client()
        tokens = max_tokens or self.max_tokens

        if settings.AIML_API_KEY:
            # OpenAI-compatible path (AI/ML API)
            response = await client.chat.completions.create(
                model       = self.model,
                max_tokens  = tokens,
                temperature = temperature,
                messages    = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or ""
        else:
            # Native Anthropic SDK path
            response = await client.messages.create(
                model      = self.model,
                max_tokens = tokens,
                temperature= temperature,
                system     = system_prompt,
                messages   = [{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text

    async def complete_json(
        self,
        system_prompt:  str,
        user_prompt:    str,
        response_model: Optional[Type[T]] = None,
        temperature:    float             = 0.05,
    ) -> dict[str, Any]:
        """
        Complete with JSON enforcement.
        Forces the model to return valid JSON, optionally validated against a Pydantic model.
        """
        json_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: Your response MUST be valid JSON only. "
            "No markdown, no code blocks, no prose. Start with {{ and end with }}."
        )

        raw_text = await self.complete(json_system, user_prompt, temperature=temperature)
        json_str = self._extract_json(raw_text)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("AI JSON parse error", raw=raw_text[:500], error=str(e))
            raise ValueError(f"AI returned invalid JSON: {e}")

        if response_model:
            return response_model(**data).model_dump()

        return data

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks."""
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            return text[start:end]
        return text

    async def count_tokens(self, text: str) -> int:
        """Rough token estimate: 1 token ≈ 4 chars."""
        return len(text) // 4


# Singleton
claude = ClaudeClient()
