
"""Content generation utilities."""

from __future__ import annotations

import logging
import random
from typing import Dict, Optional

from .auth import OpenAIClient
from .config import AppConfig

logger = logging.getLogger(__name__)

FALLBACK_QUOTES = [
    "Success is the sum of small efforts repeated day in and day out.",
    "Discipline beats motivation when motivation disappears.",
    "Dream big, start small, but start today.",
    "Consistency is what transforms average into excellence.",
    "Your only limit is the actions you take right now.",
    "Winners are ordinary people with extraordinary determination.",
]


PROMPT_TEMPLATE = """
You are an expert motivational content creator. Generate JSON with keys quote, caption, keywords.
- quote: A short motivational statement under 20 words.
- caption: TikTok caption with compelling hook, CTA, and 4-6 SEO-rich hashtags related to motivation and inspiration.
- keywords: array of 5 SEO keywords focused on motivation and life inspiration.
Ensure the JSON is valid and concise.
""".strip()


def build_hashtag_block(config: AppConfig) -> str:
    hashtags = config.caption.hashtags
    return " ".join(sorted(set(hashtags)))


def generate_content(config: AppConfig, openai_client: Optional[OpenAIClient]) -> Dict[str, str]:
    if openai_client is None:
        logger.info("OpenAI unavailable - using local fallback quote.")
        return _fallback_content(config)

    payload = openai_client.generate_post_payload(PROMPT_TEMPLATE)
    if not payload or not payload.get("quote"):
        logger.warning("Falling back to local quote content.")
        return _fallback_content(config)

    quote = payload["quote"].strip()
    caption = payload.get("caption", "").strip()
    keywords = payload.get("keywords", "").strip()

    hashtags = build_hashtag_block(config)
    if "#" not in caption:
        caption = config.caption.template.format(quote=quote, hashtags=hashtags)

    return {"quote": quote, "caption": caption, "keywords": keywords}


def _fallback_content(config: AppConfig) -> Dict[str, str]:
    quote = random.choice(FALLBACK_QUOTES)
    hashtags = build_hashtag_block(config)
    caption = config.caption.template.format(quote=quote, hashtags=hashtags)
    return {"quote": quote, "caption": caption, "keywords": ", ".join(config.caption.seo_keywords)}


__all__ = ["generate_content", "build_hashtag_block"]
