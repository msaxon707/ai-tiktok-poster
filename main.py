import os, time, random
from helpers.generate_script import create_script
from helpers.generate_voice import make_voice
from helpers.make_video import make_video
from helpers.upload_tiktok import upload_video
from helpers.get_trending_hashtags import fetch_hashtags

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 180))
NICHE = os.getenv("NICHE", "motivation")
MIN_VIDEO_LENGTH = int(os.getenv("MIN_VIDEO_LENGTH", 10))
MAX_VIDEO_LENGTH = int(os.getenv("MAX_VIDEO_LENGTH", 30))
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
MAX_RUNS = int(os.getenv("MAX_RUNS", 24))

def main():
    for run in range(MAX_RUNS):
        try:
            print(f"\n🎬 Run {run+1}/{MAX_RUNS} — Generating new {NICHE} video...")
            video_length = random.randint(MIN_VIDEO_LENGTH, MAX_VIDEO_LENGTH)

            script = create_script(NICHE, video_length)
            if not script:
                print("⚠️ Skipping post: failed to generate script.")
                continue

            hashtags = fetch_hashtags(NICHE)
            full_caption = f"{script[:150]}... {hashtags}"

            voice_file = make_voice(script)
            video_file = make_video(script, voice_file, video_length)

            if not DEBUG_MODE:
                upload_video(video_file, full_caption)
                print("✅ Posted successfully!")
            else:
                print("🧪 Debug mode active — video saved but not posted.")

        except Exception as e:
            print(f"❌ Error during run {run+1}: {e}")
            time.sleep(5)

        time.sleep(POST_INTERVAL * 60)

    print("\n✅ Completed daily run limit — shutting down safely.")

if __name__ == "__main__":
    main()
