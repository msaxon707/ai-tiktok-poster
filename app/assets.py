"""Asset acquisition helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import requests

logger = logging.getLogger(__name__)


def download_pexels_videos(api_key: str, target_dir: Path, query: str = "motivation", count: int = 5) -> List[Path]:
    if not api_key:
        return []
    target_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": api_key}
    params = {"query": query, "orientation": "portrait", "per_page": count}

    try:
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=20)
        response.raise_for_status()
    except Exception as exc:
        logger.error("Failed to fetch Pexels videos: %s", exc)
        return []

    data = response.json().get("videos", [])
    downloaded: List[Path] = []

    for video in data:
        video_id = video.get("id")
        files = video.get("video_files", [])
        if not files or video_id is None:
            continue
        portrait_files = [f for f in files if (f.get("height") or 0) >= 1280]
        selected = portrait_files[0] if portrait_files else files[0]
        url = selected.get("link")
        if not url:
            continue
        output_path = target_dir / f"pexels_{video_id}.mp4"
        if output_path.exists():
            downloaded.append(output_path)
            continue
        try:
            logger.info("Downloading Pexels video %s", video_id)
            file_bytes = requests.get(url, timeout=60)
            file_bytes.raise_for_status()
            output_path.write_bytes(file_bytes.content)
            downloaded.append(output_path)
        except Exception as exc:
            logger.warning("Unable to download Pexels video %s: %s", video_id, exc)

    return downloaded


__all__ = ["download_pexels_videos"]
