"""State handling for duplicate/repost control."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class PostHistory:
    last_post_date: str = ""
    posts_today: int = 0
    used_videos: List[str] = field(default_factory=list)
    used_quotes: List[str] = field(default_factory=list)

    def reset_if_new_day(self) -> None:
        today = date.today().isoformat()
        if self.last_post_date != today:
            logger.debug("Resetting post history for new day %s", today)
            self.last_post_date = today
            self.posts_today = 0
            self.used_videos.clear()
            self.used_quotes.clear()


class StateManager:
    def __init__(self, state_file: Path, backup_dir: Path):
        self.state_file = state_file
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> PostHistory:
        if not self.state_file.exists():
            logger.info("State file %s not found. Initialising new state.", self.state_file)
            return PostHistory(last_post_date=date.today().isoformat())
        try:
            data = json.loads(self.state_file.read_text())
            history = PostHistory(**data)
            history.reset_if_new_day()
            return history
        except Exception as exc:
            logger.error("Failed to read state file %s: %s", self.state_file, exc)
            return PostHistory(last_post_date=date.today().isoformat())

    def save(self, history: PostHistory) -> None:
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(history.__dict__, indent=2)
            self.state_file.write_text(payload)
            self._create_backup(payload)
        except Exception as exc:
            logger.exception("Unable to persist state: %s", exc)

    def _create_backup(self, payload: str) -> None:
        try:
            backup_file = self.backup_dir / f"state_{date.today().isoformat()}.json"
            backup_file.write_text(payload)
        except Exception as exc:
            logger.warning("Failed to create state backup: %s", exc)


__all__ = ["StateManager", "PostHistory"]
