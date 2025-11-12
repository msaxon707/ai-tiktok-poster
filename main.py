# main.py
import os
import sys
import json
import time
import random
import logging
from datetime import date
from pathlib import Path
from typing import List, Optional

import requests
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont

from upload import upload_to_tiktok

# --------------------
# Config from env
# --------------------
ASSETS_DIR = Path(os.getenv("ASSETS_DIR", "/app/assets"))
VIDEOS_DIR = Path(os.getenv("VIDEOS_DIR", "/app/videos"))          # background videos
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUT_DIR = Path(os.getenv("OUTPUT_PATH", "/app/output"))
STATE_FILE = Path(os.getenv("STATE_FILE", "/app/state.json"))

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")  # optional

MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "6"))
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "1"))
MIN_VIDEO_LENGTH = int(os.getenv("MIN_VIDEO_LENGTH", "15"))  # seconds
MAX_VIDEO_LENGTH = int(os.getenv("MAX_VIDEO_LENGTH", "30"))  # seconds

CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", "40"))
CAPTION_COLOR = os.getenv("CAPTION_COLOR", "white")
CAPTION_FONT_PATH = os.getenv("CAPTION_FONT_PATH", "")  # optional TTF path
NICHE = os.getenv("NICHE", "motivation")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --------------------
# Logging
# --------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------
# Local motivational quotes (no OpenAI required)
# --------------------
MOTIVATIONAL_QUOTES: List[str] = [
    "Success is the sum of small efforts repeated day in and day out.",
    "Discipline beats motivation when motivation disappears.",
    "You don’t need to be extreme, just consistent.",
    "One year from now you’ll wish you had started today.",
    "Small progress is still progress. Keep going.",
    "Your future self is watching you right now through your memories.",
    "Dream big, start small, but most of all, start.",
    "Stay consistent. Your future is built in the boring days.",
    "You’re not behind. You’re just getting started.",
    "The difference between who you are and who you want to be is what you do.",
]


def get_today() -> str:
    return date.today().isoformat()


# --------------------
# State handling (caps posts per day)
# --------------------
def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_post_date": None, "posts_today": 0}
    try:
        with STATE_FILE.open("r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read state file {STATE_FILE}: {e}")
        return {"last_post_date": None, "posts_today": 0}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        json.dump(state, f)


# --------------------
# Pexels helpers (optional)
# --------------------
def fetch_pexels_videos(
    api_key: str,
    target_dir: Path,
    query: str = "motivation",
    count: int = 3,
) -> List[Path]:
    """Download up to `count` portrait videos from Pexels into target_dir."""
    logger.info("No local videos found. Trying to fetch from Pexels...")
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": count, "orientation": "portrait"}

    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Failed to query Pexels videos: {e}")
        return []

    videos = data.get("videos", [])
    downloaded: List[Path] = []

    for video in videos:
        video_files = video.get("video_files", [])
        if not video_files:
            continue

        # pick a portrait-ish file, prefer smaller height to keep file size reasonable
        portrait_files = [vf for vf in video_files if (vf.get("height") or 0) >= 1280]
        if portrait_files:
            best = sorted(portrait_files, key=lambda x: x.get("height") or 99999)[0]
        else:
            best = video_files[0]

        url = best.get("link")
        if not url:
            continue

        video_id = video.get("id", "unknown")
        out_path = target_dir / f"pexels_{video_id}.mp4"
        if out_path.exists():
            downloaded.append(out_path)
            continue

        try:
            logger.info(f"Downloading Pexels video {video_id}...")
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            with out_path.open("wb") as f:
                f.write(r.content)
            downloaded.append(out_path)
        except Exception as e:
            logger.error(f"Failed to download Pexels video {video_id}: {e}")

    logger.info(f"Downloaded {len(downloaded)} videos from Pexels.")
    return downloaded


# --------------------
# Assets loaders
# --------------------
def list_videos(dir_path: Path) -> List[Path]:
    return sorted(
        [p for p in dir_path.glob("*.mp4")] +
        [p for p in dir_path.glob("*.mov")] +
        [p for p in dir_path.glob("*.mkv")]
    )


def list_music(dir_path: Path) -> List[Path]:
    if not dir_path.exists():
        return []
    return sorted(
        [p for p in dir_path.glob("*.mp3")] +
        [p for p in dir_path.glob("*.wav")] +
        [p for p in dir_path.glob("*.m4a")]
    )


def pick_random_quote() -> str:
    return random.choice(MOTIVATIONAL_QUOTES)


def pick_random_video(videos: List[Path], used: List[str]) -> Optional[Path]:
    remaining = [v for v in videos if v.name not in used]
    if not remaining:
        return None
    return random.choice(remaining)


def pick_random_music() -> Optional[Path]:
    tracks = list_music(MUSIC_DIR)
    return random.choice(tracks) if tracks else None


# --------------------
# Caption image with Pillow (no ImageMagick)
# --------------------
def create_caption_image(
    text: str,
    video_size: tuple[int, int],
    font_size: int,
    color: str,
) -> Image.Image:
    width, height = video_size
    img_width = int(width * 0.9)
    img_height = int(height * 0.3)

    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try custom font if provided; else default
    font = None
    if CAPTION_FONT_PATH and Path(CAPTION_FONT_PATH).exists():
        try:
            font = ImageFont.truetype(CAPTION_FONT_PATH, font_size)
        except Exception as e:
            logger.warning(f"Could not load font at {CAPTION_FONT_PATH}: {e}")

    if font is None:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # simple word-wrap
    words = text.split()
    lines: List[str] = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width > img_width - 40 and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lh = bbox[3] - bbox[1]
        line_heights.append(lh)
        total_height += lh

    y = (img_height - total_height) // 2
    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (img_width - lw) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += lh

    return img


# --------------------
# Video creation
# --------------------
def make_video(
    background_path: Path,
    quote: str,
    music_path: Optional[Path],
    output_path: Path,
) -> None:
    logger.info(f"Creating video from {background_path.name}")
    with VideoFileClip(str(background_path)) as clip:
        # Ensure duration within limits
        duration = clip.duration or MAX_VIDEO_LENGTH
        if duration < MIN_VIDEO_LENGTH:
            logger.warning(
                f"Background {background_path.name} too short ({duration:.1f}s). Skipping."
            )
            return

        if duration > MAX_VIDEO_LENGTH:
            start = 0
            end = start + MAX_VIDEO_LENGTH
            clip = clip.subclip(start, end)
            duration = clip.duration

        # Resize to standard TikTok 1080x1920
        clip = clip.resize(height=1920)
        if clip.w != 1080:
            clip = clip.resize(width=1080)

        # Caption overlay
        caption_img = create_caption_image(
            quote, (clip.w, clip.h), CAPTION_FONT_SIZE, CAPTION_COLOR
        )
        caption_clip = (
            ImageClip(np.array(caption_img))
            .set_duration(duration)
            .set_position(("center", "bottom"))
            .margin(bottom=int(clip.h * 0.08), opacity=0)
        )

        final = CompositeVideoClip([clip, caption_clip])

        # Background music if available
        if music_path:
            try:
                logger.info(f"Adding music: {music_path.name}")
                audio_clip = AudioFileClip(str(music_path)).volumex(0.6)
                audio_clip = audio_clip.set_duration(duration)
                final = final.set_audio(audio_clip)
            except Exception as e:
                logger.warning(f"Failed to load music {music_path}: {e}")

        # Export
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Writing final video to {output_path}")
        final.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=30,
            threads=4,
            verbose=False,
            logger=None,
        )


# --------------------
# Main flow
# --------------------
def main():
    logger.info("🚀 Starting TikTok auto poster (NO OpenAI calls).")

    # Ensure directories
    for d in [ASSETS_DIR, VIDEOS_DIR, MUSIC_DIR, OUTPUT_DIR, STATE_FILE.parent]:
        d.mkdir(parents=True, exist_ok=True)

    state = load_state()
    today = get_today()

    # Reset daily count if date changed
    if state.get("last_post_date") != today:
        state["last_post_date"] = today
        state["posts_today"] = 0
        state["used_videos"] = []

    posts_today = state.get("posts_today", 0)
    used_videos = state.get("used_videos", [])

    if posts_today >= MAX_POSTS_PER_DAY:
        logger.info(
            f"Already reached MAX_POSTS_PER_DAY={MAX_POSTS_PER_DAY}. Exiting without posting."
        )
        return

    # Load or fetch background videos
    videos = list_videos(VIDEOS_DIR)

    if not videos and PEXELS_API_KEY:
        videos = fetch_pexels_videos(PEXELS_API_KEY, VIDEOS_DIR, query=NICHE, count=3)

    if not videos:
        logger.warning(
            f"No background videos found in {VIDEOS_DIR} and Pexels not available. "
            "Add .mp4 files to the videos folder."
        )
        return

    remaining_today = MAX_POSTS_PER_DAY - posts_today
    if remaining_today <= 0:
        logger.info("No remaining posts allowed today.")
        return

    posts_this_run = min(MAX_POSTS_PER_RUN, remaining_today)
    logger.info(
        f"Can still post {remaining_today} times today. Will create up to {posts_this_run} video(s) this run."
    )

    for i in range(posts_this_run):
        bg = pick_random_video(videos, used_videos)
        if not bg:
            logger.warning("No unused background videos left.")
            break

        quote = pick_random_quote()
        music = pick_random_music()

        output_file = OUTPUT_DIR / f"tiktok_{today}_{posts_today + 1}.mp4"
        make_video(bg, quote, music, output_file)

        # Upload (placeholder)
        success = upload_to_tiktok(str(output_file), quote)
        if success:
            posts_today += 1
            used_videos.append(bg.name)
            logger.info(
                f"✅ Posted video #{posts_today} for {today} using {bg.name}: {quote}"
            )
        else:
            logger.warning("Upload failed or not implemented; keeping state unchanged.")

        # Update state after each attempt
        state["posts_today"] = posts_today
        state["used_videos"] = used_videos
        save_state(state)

    logger.info("✨ Run finished. Exiting.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Fatal error in main(): {e}")
        sys.exit(1)
