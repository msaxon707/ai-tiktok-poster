"""Compatibility shim for the legacy module path."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

def upload_to_tiktok(video_path: str, caption: str, session_id: Optional[str] = None) -> bool:
    config = load_config()
    if session_id:
        config.tiktok_session_id = session_id  # type: ignore[attr-defined]
    uploader = VideoUploader(config)
    return uploader.upload(Path(video_path), caption)
