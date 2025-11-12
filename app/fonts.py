"""Google Fonts download helper."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

CSS_URL = "https://fonts.googleapis.com/css2"


def ensure_google_font(
    fonts_dir: Path,
    family: str,
    weight: str = "400",
) -> Optional[Path]:
    fonts_dir.mkdir(parents=True, exist_ok=True)
    normalized_family = family.replace(" ", "+")
    css_params = {"family": f"{normalized_family}:wght@{weight}"}

    try:
        response = requests.get(CSS_URL, params=css_params, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch Google Fonts CSS for %s: %s", family, exc)
        return None

    ttf_url = None
    for line in response.text.splitlines():
        line = line.strip()
        if line.startswith("src:") and "https://" in line:
            start = line.find("https://")
            end = line.find(")", start)
            ttf_url = line[start:end]
            break

    if not ttf_url:
        logger.warning("No TTF URL found in Google Fonts CSS for %s", family)
        return None

    font_filename = f"{family.replace(' ', '_')}_{weight}.ttf"
    font_path = fonts_dir / font_filename

    if font_path.exists():
        return font_path

    try:
        logger.info("Downloading Google Font %s (%s)", family, weight)
        font_bytes = requests.get(ttf_url, timeout=30)
        font_bytes.raise_for_status()
        font_path.write_bytes(font_bytes.content)
        return font_path
    except Exception as exc:
        logger.warning("Unable to download font %s: %s", family, exc)
        return None


__all__ = ["ensure_google_font"]
