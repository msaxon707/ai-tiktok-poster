"""Configuration management for the TikTok poster service."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv(override=False)


def _read_config_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    values: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@dataclass
class ScheduleConfig:
    interval_hours: int = 3
    timezone: str = "UTC"
    jitter_minutes: int = 5
    start_immediately: bool = True


@dataclass
class CaptionConfig:
    template: str = "{quote}\n\n{hashtags}"
    hashtags: List[str] = field(default_factory=lambda: ["#motivation", "#inspiration", "#mindset", "#dailyquote"])
    seo_keywords: List[str] = field(default_factory=lambda: ["motivation", "success", "inspiration", "life lessons"])


@dataclass
class PathConfig:
    base_dir: Path
    assets_dir: Path
    videos_dir: Path
    music_dir: Path
    fonts_dir: Path
    featured_images_dir: Path
    inline_images_dir: Path
    output_dir: Path
    logs_dir: Path
    backups_dir: Path
    state_file: Path


@dataclass
class AirtableConfig:
    api_key: Optional[str] = None
    base_id: Optional[str] = None
    table_name: Optional[str] = None


@dataclass
class AppConfig:
    paths: PathConfig
    schedule: ScheduleConfig
    caption: CaptionConfig
    openai_api_key: Optional[str]
    openai_model: str
    openai_max_tokens: int
    openai_max_cost: float
    pexels_api_key: Optional[str]
    tiktok_session_id: Optional[str]
    google_font_family: str
    google_font_weight: str
    max_posts_per_day: int
    airtable: AirtableConfig

    @property
    def config_json(self) -> str:
        """Useful for debugging."""
        payload = {
            "schedule": self.schedule.__dict__,
            "caption": {
                "template": self.caption.template,
                "hashtags": self.caption.hashtags,
                "seo_keywords": self.caption.seo_keywords,
            },
            "paths": {k: str(v) for k, v in self.paths.__dict__.items()},
            "openai_model": self.openai_model,
            "openai_max_tokens": self.openai_max_tokens,
            "openai_max_cost": self.openai_max_cost,
            "max_posts_per_day": self.max_posts_per_day,
            "airtable_configured": bool(
                self.airtable.api_key and self.airtable.base_id and self.airtable.table_name
            ),
        }
        return json.dumps(payload, indent=2)


DEFAULT_CONFIG_FILE = Path(os.getenv("CONFIG_FILE", "config.txt"))


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    config_path = config_path or DEFAULT_CONFIG_FILE
    file_values = _read_config_file(config_path)

    def _get(key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, file_values.get(key, default))

    base_dir = Path(_get("DATA_ROOT", str(Path.cwd() / "data")))
    assets_dir = Path(_get("ASSETS_DIR", str(base_dir / "assets")))
    videos_dir = Path(_get("VIDEOS_DIR", "/app/videos"))
    music_dir = Path(_get("MUSIC_DIR", str(assets_dir / "music")))
    fonts_dir = Path(_get("FONTS_DIR", str(assets_dir / "fonts")))
    featured_dir = Path(_get("FEATURED_IMAGES_DIR", str(assets_dir / "featured")))
    inline_dir = Path(_get("INLINE_IMAGES_DIR", str(assets_dir / "inline")))
    output_dir = Path(_get("OUTPUT_DIR", str(base_dir / "output")))
    logs_dir = Path(_get("LOGS_DIR", str(base_dir / "logs")))
    backups_dir = Path(_get("BACKUPS_DIR", str(base_dir / "backups")))
    state_file = Path(_get("STATE_FILE", str(base_dir / "state.json")))

    openai_api_key = _get("OPENAI_API_KEY")
    openai_model = _get("OPENAI_MODEL", "gpt-4.0-mini")
    openai_max_tokens = int(_get("OPENAI_MAX_TOKENS", "400"))
    openai_max_cost = float(_get("OPENAI_MAX_COST", "0.75"))

    pexels_api_key = _get("PEXELS_API_KEY")
    tiktok_session_id = _get("TIKTOK_SESSION_ID")

    hashtags = [h.strip() for h in _get("CAPTION_HASHTAGS", "#motivation,#inspiration,#mindset").split(",") if h.strip()]
    seo_keywords = [k.strip() for k in _get("SEO_KEYWORDS", "motivation,success,inspiration").split(",") if k.strip()]
    caption_template = _get("CAPTION_TEMPLATE", "{quote}\n\n{hashtags}")

    schedule_interval = int(_get("SCHEDULE_INTERVAL_HOURS", "3"))
    timezone = _get("SCHEDULE_TIMEZONE", "UTC")
    jitter_minutes = int(_get("SCHEDULE_JITTER_MINUTES", "8"))
    max_posts_per_day = int(_get("MAX_POSTS_PER_DAY", "8"))

    google_font_family = _get("GOOGLE_FONT_FAMILY", "Poppins")
    google_font_weight = _get("GOOGLE_FONT_WEIGHT", "600")

    paths = PathConfig(
        base_dir=base_dir,
        assets_dir=assets_dir,
        videos_dir=videos_dir,
        music_dir=music_dir,
        fonts_dir=fonts_dir,
        featured_images_dir=featured_dir,
        inline_images_dir=inline_dir,
        output_dir=output_dir,
        logs_dir=logs_dir,
        backups_dir=backups_dir,
        state_file=state_file,
    )

    schedule_cfg = ScheduleConfig(
        interval_hours=max(1, schedule_interval),
        timezone=timezone,
        jitter_minutes=max(0, jitter_minutes),
        start_immediately=_get("SCHEDULE_START_IMMEDIATELY", "true").lower() in {"1", "true", "yes"},
    )

    caption_cfg = CaptionConfig(
        template=caption_template,
        hashtags=hashtags,
        seo_keywords=seo_keywords,
    )

    airtable_cfg = AirtableConfig(
        api_key=_get("AIRTABLE_API_KEY"),
        base_id=_get("AIRTABLE_BASE_ID"),
        table_name=_get("AIRTABLE_TABLE_NAME", "tiktok posts"),
    )

    return AppConfig(
        paths=paths,
        schedule=schedule_cfg,
        caption=caption_cfg,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_max_tokens=openai_max_tokens,
        openai_max_cost=openai_max_cost,
        pexels_api_key=pexels_api_key,
        tiktok_session_id=tiktok_session_id,
        google_font_family=google_font_family,
        google_font_weight=google_font_weight,
        max_posts_per_day=max_posts_per_day,
        airtable=airtable_cfg,
    )


__all__ = [
    "AppConfig",
    "ScheduleConfig",
    "CaptionConfig",
    "PathConfig",
    "AirtableConfig",
    "load_config",
]
