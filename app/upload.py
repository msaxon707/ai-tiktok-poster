"""TikTok upload management."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class UploadRecord:
    fingerprint: str
    video_path: str
    caption: str


class UploadRegistry:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._records = self._load()

    def _load(self) -> dict:
        if not self.registry_path.exists():
            return {}
        try:
            return json.loads(self.registry_path.read_text())
        except Exception as exc:
            logger.warning("Failed to read upload registry: %s", exc)
            return {}

    def save(self) -> None:
        try:
            self.registry_path.write_text(json.dumps(self._records, indent=2))
        except Exception as exc:
            logger.error("Unable to persist upload registry: %s", exc)

    def has(self, fingerprint: str) -> bool:
        return fingerprint in self._records

    def add(self, record: UploadRecord) -> None:
        self._records[record.fingerprint] = {
            "video_path": record.video_path,
            "caption": record.caption,
        }
        self.save()


class VideoUploader:
    def __init__(self, config: AppConfig):
        self.config = config
        registry_path = config.paths.backups_dir / "uploads_registry.json"
        self.registry = UploadRegistry(registry_path)

    def _fingerprint(self, video_path: Path, caption: str) -> str:
        digest = hashlib.sha256()
        digest.update(video_path.name.encode("utf-8"))
        digest.update(str(video_path.stat().st_size if video_path.exists() else 0).encode("utf-8"))
        digest.update(caption.encode("utf-8"))
        return digest.hexdigest()

    def already_uploaded(self, video_path: Path, caption: str) -> bool:
        fp = self._fingerprint(video_path, caption)
        exists = self.registry.has(fp)
        if exists:
            logger.info("Skipping upload for %s (already uploaded)", video_path.name)
        return exists

    def mark_uploaded(self, video_path: Path, caption: str) -> None:
        fp = self._fingerprint(video_path, caption)
        self.registry.add(UploadRecord(fp, str(video_path), caption))

    def upload(self, video_path: Path, caption: str) -> bool:
        if self.already_uploaded(video_path, caption):
            return False

        session_id = self.config.tiktok_session_id
        if not session_id:
            logger.warning("TIKTOK_SESSION_ID missing - skipping real upload.")
            self.mark_uploaded(video_path, caption)
            return True

        # Placeholder for real upload logic.
        logger.info("Uploading %s to TikTok with provided session.", video_path)
        # TODO: integrate with TikTok uploader or third-party library.
        self.mark_uploaded(video_path, caption)
        return True


__all__ = ["VideoUploader", "UploadRegistry", "UploadRecord"]
