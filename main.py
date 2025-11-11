import os
import time
import random
import logging
from upload import upload_video, generate_hashtags

# -------------------- SETTINGS --------------------
logging.basicConfig(
    filename="poster.log",  # also saves logs in file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

OUTPUT_PATH = os.getenv("OUTPUT_PATH", "/app/videos")
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 180))  # seconds between posts
NICHE = os.getenv("NICHE", "motivation")

# Sample motivational quotes (local to avoid API costs)
QUOTES = [
    "You are stronger than you think.",
    "Push yourself, because no one else will do it for you.",
    "Discipline beats motivation every time.",
    "Every day is a new opportunity to grow.",
    "Don’t stop until you’re proud.",
    "Dream big, work hard, stay humble.",
    "Small steps every day lead to big changes.",
    "Focus on progress, not perfection."
]

# -------------------- MAIN AUTO POST LOOP --------------------
def get_random_video():
    """
    Grabs a random video file from OUTPUT_PATH
    """
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    videos = [f for f in os.listdir(OUTPUT_PATH) if f.endswith(('.mp4', '.mov', '.mkv'))]
    if not videos:
        logging.warning("⚠️ No videos found in folder. Add files to /videos.")
        return None
    return os.path.join(OUTPUT_PATH, random.choice(videos))

def generate_caption():
    """
    Builds a motivational caption with hashtags.
    """
    quote = random.choice(QUOTES)
    hashtags = generate_hashtags(NICHE)
    return f"{quote}\n\n{hashtags}"

def main():
    logging.info("🚀 Starting AI TikTok Auto Poster...")
    while True:
        video = get_random_video()
        if not video:
            logging.warning("No videos found. Retrying in 10 minutes.")
            time.sleep(600)
            continue

        caption = generate_caption()
        logging.info(f"🎬 Uploading video: {video}")
        logging.info(f"📝 Caption: {caption}")

        success = upload_video(video, caption)
        if success:
            logging.info(f"✅ Successfully posted video: {video}")
        else:
            logging.error(f"❌ Failed to post video: {video}")

        logging.info(f"🕒 Waiting {POST_INTERVAL} seconds before next upload...")
        time.sleep(POST_INTERVAL)

if __name__ == "__main__":
    main()
