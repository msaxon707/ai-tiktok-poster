"""Video creation utilities."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
)
from PIL import Image, ImageDraw, ImageFont

from .config import AppConfig
from .fonts import ensure_google_font

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv")
SUPPORTED_AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a")
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


@dataclass
class RenderResult:
    output_path: Path
    background_video: Path
    music_track: Optional[Path]
    featured_image: Optional[Path]
    inline_images: List[Path]


class VideoProcessor:
    def __init__(self, config: AppConfig):
        self.config = config
        self.font_path = ensure_google_font(
            config.paths.fonts_dir, config.google_font_family, config.google_font_weight
        )

    # ----------------------------
    # Asset discovery helpers
    # ----------------------------
    def _iter_files(self, directory: Path, extensions: Iterable[str]) -> List[Path]:
        if not directory.exists():
            return []
        return sorted(
            [p for p in directory.glob("*") if p.suffix.lower() in extensions and p.is_file()]
        )

    def list_background_videos(self) -> List[Path]:
        return self._iter_files(self.config.paths.videos_dir, SUPPORTED_VIDEO_EXTENSIONS)

    def list_music_tracks(self) -> List[Path]:
        return self._iter_files(self.config.paths.music_dir, SUPPORTED_AUDIO_EXTENSIONS)

    def list_featured_images(self) -> List[Path]:
        return self._iter_files(self.config.paths.featured_images_dir, SUPPORTED_IMAGE_EXTENSIONS)

    def list_inline_images(self) -> List[Path]:
        return self._iter_files(self.config.paths.inline_images_dir, SUPPORTED_IMAGE_EXTENSIONS)

    def pick_background(self, used: List[str]) -> Optional[Path]:
        candidates = [p for p in self.list_background_videos() if p.name not in used]
        if not candidates:
            candidates = self.list_background_videos()
        if not candidates:
            return None
        return random.choice(candidates)

    def pick_music(self) -> Optional[Path]:
        tracks = self.list_music_tracks()
        return random.choice(tracks) if tracks else None

    def pick_featured_image(self) -> Optional[Path]:
        images = self.list_featured_images()
        return random.choice(images) if images else None

    def pick_inline_images(self, max_images: int = 3) -> List[Path]:
        images = self.list_inline_images()
        random.shuffle(images)
        return images[:max_images]

    # ----------------------------
    # Rendering
    # ----------------------------
    def render_video(
        self,
        quote: str,
        caption: str,
        background_path: Path,
        output_path: Path,
        music_path: Optional[Path] = None,
        featured_image: Optional[Path] = None,
        inline_images: Optional[List[Path]] = None,
    ) -> RenderResult:
        inline_images = inline_images or []
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Rendering video using %s", background_path.name)

        with VideoFileClip(str(background_path)) as clip:
            clip = self._prepare_background(clip)
            duration = clip.duration or 30

            caption_clip = self._build_caption_clip(quote, clip.w, clip.h, duration)

            overlays = [clip, caption_clip]

            if featured_image:
                overlays.append(self._build_featured_clip(featured_image, duration, clip.w, clip.h))

            if inline_images:
                overlays.extend(self._build_inline_clips(inline_images, duration, clip.w, clip.h))

            video = CompositeVideoClip(overlays)

            if music_path:
                audio = self._build_audio_track(music_path, duration)
                if audio:
                    video = video.set_audio(audio)

            logger.info("Writing rendered video to %s", output_path)
            video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=30,
                threads=4,
                verbose=False,
                logger=None,
            )

        return RenderResult(
            output_path=output_path,
            background_video=background_path,
            music_track=music_path,
            featured_image=featured_image,
            inline_images=inline_images,
        )

    # ----------------------------
    # Helpers
    # ----------------------------
    def _prepare_background(self, clip: VideoFileClip) -> VideoFileClip:
        clip = clip.resize(height=1920)
        if clip.w != 1080:
            clip = clip.resize(width=1080)
        max_length = 60
        if clip.duration and clip.duration > max_length:
            clip = clip.subclip(0, max_length)
        return clip

    def _build_caption_clip(self, text: str, width: int, height: int, duration: float) -> ImageClip:
        img = self._create_caption_image(text, width, height)
        clip = ImageClip(np.array(img))
        return clip.set_duration(duration).set_position(("center", "bottom")).margin(
            bottom=int(height * 0.08), opacity=0
        )

    def _create_caption_image(self, text: str, width: int, height: int) -> Image.Image:
        img_width = int(width * 0.9)
        img_height = int(height * 0.28)
        image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        font = self._load_font(size=int(height * 0.045))

        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > img_width - 40 and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        total_height = 0
        line_heights: List[int] = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            height = bbox[3] - bbox[1]
            total_height += height
            line_heights.append(height)

        y = (img_height - total_height) // 2
        for line, line_height in zip(lines, line_heights):
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (img_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=font, fill="white")
            y += line_height
        return image

    def _load_font(self, size: int) -> ImageFont.ImageFont:
        if self.font_path and Path(self.font_path).exists():
            try:
                return ImageFont.truetype(str(self.font_path), size)
            except Exception as exc:
                logger.warning("Failed to load custom font: %s", exc)
        return ImageFont.truetype("DejaVuSans.ttf", size)

    def _build_featured_clip(self, image_path: Path, duration: float, width: int, height: int) -> ImageClip:
        image = Image.open(image_path).convert("RGBA")
        image.thumbnail((int(width * 0.7), int(height * 0.6)))
        clip = ImageClip(np.array(image)).set_duration(min(duration, 5))
        return clip.set_position(("center", int(height * 0.12))).crossfadeout(1)

    def _build_inline_clips(self, image_paths: List[Path], duration: float, width: int, height: int) -> List[ImageClip]:
        num_images = len(image_paths)
        if num_images == 0:
            return []
        segment = max(duration / (num_images + 1), 3)
        clips: List[ImageClip] = []
        start_time = segment
        for path in image_paths:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((int(width * 0.8), int(height * 0.5)))
            clip = (
                ImageClip(np.array(image))
                .set_duration(segment)
                .set_start(start_time)
                .set_position(("center", "center"))
                .crossfadein(0.5)
                .crossfadeout(0.5)
            )
            clips.append(clip)
            start_time += segment * 0.9
        return clips

    def _build_audio_track(self, music_path: Path, duration: float) -> Optional[CompositeAudioClip]:
        try:
            track = AudioFileClip(str(music_path)).volumex(0.6)
            track = track.set_duration(duration)
            return CompositeAudioClip([track])
        except Exception as exc:
            logger.warning("Unable to process background audio %s: %s", music_path.name, exc)
            return None


__all__ = ["VideoProcessor", "RenderResult"]
