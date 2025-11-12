"""Airtable logging utilities for TikTok posts."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from requests import Response
from urllib.parse import quote

from .config import AppConfig

logger = logging.getLogger(__name__)


class AirtableLogger:
    """Simple client that records post metadata to Airtable."""

    def __init__(self, config: AppConfig):
        airtable_cfg = config.airtable
        self.api_key: Optional[str] = airtable_cfg.api_key
        self.base_id: Optional[str] = airtable_cfg.base_id
        self.table_name: Optional[str] = airtable_cfg.table_name
        self._enabled = bool(self.api_key and self.base_id and self.table_name)

        if not self._enabled:
            logger.info("Airtable logging disabled - missing configuration values.")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def log_post(self, fields: Dict[str, Any]) -> bool:
        """Send a record to Airtable. Returns True if the request succeeded."""

        if not self.enabled:
            return False

        payload = {"fields": self._serialise_fields(fields)}

        try:
            response = self._post(payload)
        except Exception as exc:  # pragma: no cover - requests exceptions
            logger.warning("Failed to reach Airtable API: %s", exc)
            return False

        if 200 <= response.status_code < 300:
            logger.info("Logged TikTok post to Airtable table '%s'.", self.table_name)
            return True

        try:
            detail = response.json()
        except Exception:  # pragma: no cover - non JSON error
            detail = response.text
        logger.warning(
            "Airtable logging request failed with status %s: %s",
            response.status_code,
            detail,
        )
        return False

    def _post(self, payload: Dict[str, Any]) -> Response:
        url = f"https://api.airtable.com/v0/{self.base_id}/{quote(self.table_name, safe='')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)

    @staticmethod
    def _serialise_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
        serialised: Dict[str, Any] = {}
        for key, value in fields.items():
            if isinstance(value, datetime):
                serialised[key] = value.isoformat().replace("+00:00", "Z")
            elif value is None:
                continue
            else:
                serialised[key] = value
        return serialised


__all__ = ["AirtableLogger"]
