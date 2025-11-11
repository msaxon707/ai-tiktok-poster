print("🧠 Checking MoviePy import...")
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "show", "moviepy"])
from moviepy.editor import VideoFileClip
print("✅ MoviePy imported successfully.")
import os
import time
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from upload import upload_to_tiktok

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

VIDEOS_DIR = "./videos"
ASSETS_DIR = "./assets"
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 1800))  # every 30 minutes

def process_video(video_path):
    """Add caption text overlay and prepare video."""
    logging.info(f"🎬 Processing {os.path.basename(video_path)}...")

    try:
        clip = VideoFileClip(video_path)
        caption = "💭 Stay motivated — every day counts! 💪"

        text = TextClip(
            caption,
            fontsize=50,
            color='white',
            font=os.path.join(ASSETS_DIR, "fonts", "Arial.ttf") if os.path.exists(os.path.join(ASSETS_DIR, "fonts", "Arial.ttf")) else "Arial-Bold",
            stroke_color='black',
            stroke_width=2
        ).set_position(('center', 'bottom')).set_duration(clip.duration)

        final = CompositeVideoClip([clip, text])
        output_path = os.path.join(VIDEOS_DIR, f"processed_{os.path.basename(video_path)}")
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        logging.info(f"✅ Video processed and saved to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"❌ Error processing video {video_path}: {e}")
        return None


def main():
    logging.info("🚀 Starting AI TikTok Auto Poster...")

    if not os.path.exists(VIDEOS_DIR):
        logging.warning("⚠️ No videos directory found. Creating one...")
        os.makedirs(VIDEOS_DIR)
        return

    while True:
        videos = [v for v in os.listdir(VIDEOS_DIR) if v.endswith(('.mp4', '.mov')) and not v.startswith('processed_')]
        if not videos:
            logging.warning("⚠️ No videos found in folder. Add files to /videos.")
            time.sleep(600)
            continue

        for video in videos:
            path = os.path.join(VIDEOS_DIR, video)
            processed_path = process_video(path)
            if processed_path:
                upload_to_tiktok(processed_path)
                logging.info(f"✅ Successfully uploaded: {video}")
            else:
                logging.warning(f"⚠️ Skipping {video} due to processing error.")

            time.sleep(POST_INTERVAL)


if __name__ == "__main__":
    main()
