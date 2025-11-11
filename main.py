import os
import time
import random
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from openai import OpenAI

# ───────────────────────────────
# CONFIGURATION
# ───────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 180)) * 60  # minutes → seconds
VIDEOS_DIR = "assets/videos"
MUSIC_DIR = "assets/music"
OUTPUT_DIR = "videos"
NICHE = os.getenv("NICHE", "motivation")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ───────────────────────────────
# GENERATE MOTIVATIONAL QUOTE
# ───────────────────────────────
def get_motivational_quote():
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a short-form motivational quote generator."},
                {"role": "user", "content": "Write one original motivational quote under 15 words."}
            ],
            max_tokens=50,
        )
        quote = response.choices[0].message.content.strip('" ')
        logging.info(f"Generated quote: {quote}")
        return quote
    except Exception as e:
        logging.error(f"OpenAI quote generation failed: {e}")
        return "Keep pushing forward. Great things take time."

# ───────────────────────────────
# CREATE VIDEO
# ───────────────────────────────
def create_video():
    try:
        # Pick a random video + music file
        video_file = random.choice(os.listdir(VIDEOS_DIR))
        music_file = random.choice(os.listdir(MUSIC_DIR))
        quote = get_motivational_quote()

        video_path = os.path.join(VIDEOS_DIR, video_file)
        music_path = os.path.join(MUSIC_DIR, music_file)

        logging.info(f"Using video: {video_file}, music: {music_file}")

        clip = VideoFileClip(video_path)
        music = AudioFileClip(music_path)

        # Shorten to 15–30 seconds
        duration = random.randint(15, 30)
        if clip.duration > duration:
            clip = clip.subclip(0, duration)

        # Add music
        final_audio = music.volumex(0.4)
        clip = clip.set_audio(final_audio)

        # Add quote overlay
        txt = TextClip(
            quote,
            fontsize=40,
            color="white",
            font="Arial-Bold",
            method="caption",
            size=clip.size
        ).set_position("center").set_duration(clip.duration)

        final = CompositeVideoClip([clip, txt])
        output_path = os.path.join(OUTPUT_DIR, f"motivational_{int(time.time())}.mp4")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        logging.info(f"✅ Video created: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Video creation failed: {e}")
        return None

# ───────────────────────────────
# MAIN AUTO LOOP
# ───────────────────────────────
def main():
    logging.info("🚀 Starting AI Motivational TikTok Auto Poster...")
    while True:
        video_path = create_video()
        if video_path:
            # Here’s where you’d upload to TikTok — placeholder
            logging.info(f"Pretending to upload video: {video_path}")
        else:
            logging.warning("Skipping upload due to error.")
        logging.info(f"Sleeping for {POST_INTERVAL / 60:.0f} minutes before next post...")
        time.sleep(POST_INTERVAL)

if __name__ == "__main__":
    main()
