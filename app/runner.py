"""Primary workflow orchestration."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .auth import OpenAIClient
from .config import AppConfig, load_config
from .assets import download_pexels_videos
from .content import generate_content
from .logging_utils import configure_logging
from .state import StateManager
from .upload import VideoUploader
from .video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class AutoPoster:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        configure_logging(self.config.paths.logs_dir)
        self.state_manager = StateManager(self.config.paths.state_file, self.config.paths.backups_dir)
        self.video_processor = VideoProcessor(self.config)
        self.uploader = VideoUploader(self.config)

        for path in [
            self.config.paths.assets_dir,
            self.config.paths.videos_dir,
            self.config.paths.music_dir,
            self.config.paths.fonts_dir,
            self.config.paths.featured_images_dir,
            self.config.paths.inline_images_dir,
            self.config.paths.output_dir,
            self.config.paths.logs_dir,
            self.config.paths.backups_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        self.openai_client: Optional[OpenAIClient]
        if self.config.openai_api_key:
            try:
                self.openai_client = OpenAIClient(self.config)
            except Exception as exc:
                logger.warning("Failed to initialise OpenAI client: %s", exc)
                self.openai_client = None
        else:
            self.openai_client = None

    def run_once(self) -> Optional[Path]:
        history = self.state_manager.load()
        history.reset_if_new_day()

        if history.posts_today >= self.config.max_posts_per_day:
            logger.info(
                "Daily post limit of %s reached. Skipping run.",
                self.config.max_posts_per_day,
            )
            return None

        background = self.video_processor.pick_background(history.used_videos)
        if not background:
            if self.config.pexels_api_key:
                downloads = download_pexels_videos(
                    self.config.pexels_api_key,
                    self.config.paths.videos_dir,
                    query="motivation inspiration",
                )
                if downloads:
                    background = self.video_processor.pick_background(history.used_videos)

        if not background:
            logger.error("No background videos available. Please add files to %s", self.config.paths.videos_dir)
            return None

        content = generate_content(self.config, self.openai_client)
        quote = content["quote"]
        caption = content["caption"]
        if content.get("keywords"):
            logger.info("SEO keywords: %s", content["keywords"])

        if quote in history.used_quotes:
            logger.info("Quote already used today - selecting fallback.")
            history.used_quotes = [q for q in history.used_quotes if q != quote]
            fallback = generate_content(self.config, None)
            quote = fallback["quote"]
            caption = fallback["caption"]

        music = self.video_processor.pick_music()
        featured_image = self.video_processor.pick_featured_image()
        inline_images = self.video_processor.pick_inline_images()

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = self.config.paths.output_dir / f"motivation_{timestamp}.mp4"

        render = self.video_processor.render_video(
            quote=quote,
            caption=caption,
            background_path=background,
            output_path=output_path,
            music_path=music,
            featured_image=featured_image,
            inline_images=inline_images,
        )

        backup_path = self._backup_video(render.output_path)
        logger.info("Backup saved to %s", backup_path)

        uploaded = self.uploader.upload(render.output_path, caption)
        if uploaded:
            history.posts_today += 1
            history.used_videos.append(background.name)
            history.used_quotes.append(quote)
            self.state_manager.save(history)
            logger.info("Successfully processed post #%s", history.posts_today)
        else:
            logger.warning("Upload skipped for %s", render.output_path)

        return render.output_path

    def _backup_video(self, video_path: Path) -> Path:
        self.config.paths.backups_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.config.paths.backups_dir / video_path.name
        try:
            shutil.copy2(video_path, backup_path)
        except Exception as exc:
            logger.warning("Failed to copy video to backup: %s", exc)
        return backup_path


__all__ = ["AutoPoster"]
