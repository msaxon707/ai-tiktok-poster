"""Authentication helpers and OpenAI client wrapper."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from openai import OpenAI

from .config import AppConfig

logger = logging.getLogger(__name__)

PRICE_PER_1K_TOKENS = 0.006  # conservative upper bound in USD


@dataclass
class OpenAIUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def estimated_cost(self) -> float:
        return (self.total_tokens / 1000.0) * PRICE_PER_1K_TOKENS


class OpenAIClient:
    def __init__(self, config: AppConfig):
        self._config = config
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIClient")
        self._client = OpenAI(api_key=config.openai_api_key)
        self._usage = OpenAIUsage()

    @property
    def usage(self) -> OpenAIUsage:
        return self._usage

    def can_afford(self, expected_tokens: int) -> bool:
        projected_cost = (
            (self._usage.total_tokens + expected_tokens) / 1000.0
        ) * PRICE_PER_1K_TOKENS
        return projected_cost <= self._config.openai_max_cost

    def generate_post_payload(self, prompt: str) -> Optional[Dict[str, str]]:
        expected_tokens = self._config.openai_max_tokens * 2
        if not self.can_afford(expected_tokens):
            logger.warning(
                "Skipping OpenAI call to stay within cost ceiling of $%.2f",
                self._config.openai_max_cost,
            )
            return None

        try:
            response = self._client.responses.create(
                model=self._config.openai_model,
                input=prompt,
                max_output_tokens=self._config.openai_max_tokens,
            )
        except Exception as exc:
            logger.error("OpenAI request failed: %s", exc)
            return None

        content = getattr(response, "output_text", "")
        if not content:
            try:
                content = response.output[0].content[0].text  # type: ignore[attr-defined]
            except Exception as exc:  # pragma: no cover - structure can vary
                logger.error("Unexpected OpenAI response format: %s", exc)
                return None

        meta = getattr(response, "usage", None)
        if meta:
            self._usage.prompt_tokens += getattr(meta, "input_tokens", 0)
            self._usage.completion_tokens += getattr(meta, "output_tokens", 0)

        try:
            import json

            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")
            return {
                "quote": str(payload.get("quote", "")),
                "caption": str(payload.get("caption", "")),
                "keywords": ", ".join(payload.get("keywords", [])),
            }
        except Exception as exc:
            logger.error("Failed to parse OpenAI payload: %s", exc)
            return None


__all__ = ["OpenAIClient", "OpenAIUsage", "PRICE_PER_1K_TOKENS"]
