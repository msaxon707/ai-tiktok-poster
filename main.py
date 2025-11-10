import os, time, random, textwrap
import openai
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, CompositeAudioClip
)

# -------------------------------
# ENVIRONMENT CONFIG
# -------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 180))  # minutes
NICHE = os.getenv("NICHE", "motivation")
MIN_VIDEO_LENGTH = int(os.getenv("MIN_VIDEO_LENGTH", 10))
MAX_VIDEO_LENGTH = int(os.getenv("MAX_VIDEO_LENGTH", 30))
CAPTION_COLOR = os.getenv("CAPTION_COLOR", "white")
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", 40))
VOICE_STYLE = os.getenv("VOICE_STYLE", "alloy")
MAX_RUNS = int(os.getenv("MAX_RUNS", 24))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

openai.api_key = OPENAI_API_KEY


# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def safe_openai_call(func, *args, retries=3, delay=3, **kwargs):
    """Retries OpenAI calls to prevent runaway charges"""
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ OpenAI error (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)
    print("❌ Giving up after multiple errors.")
    return None


def generate_script(niche, duration):
    """Generate short motivational or true-crime script"""
    prompt = (
        f"Write a short {duration}-second TikTok script in the {niche} niche. "
        f"It should sound natural when spoken aloud and end with a strong or emotional line. "
        f"Keep it clean and under {duration * 10} characters."
    )
    resp = safe_openai_call(
        openai.ChatCompletion.create,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        timeout=20
    )
    if not resp:
        return None
    return resp.choices[0].message["content"].strip()


def generate_hashtags(niche):
    """Auto-generate trending hashtags for your content"""
    prompt = f"List 5 trending TikTok hashtags for {niche} videos. Only output hashtags."
    resp = safe_openai_call(
        openai.ChatCompletion.create,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        timeout=10
    )
    if not resp:
        return "#motivation #fyp"
    return resp.choices[0].message["content"].replace("\n", " ")


def generate_voice(script):
    """Generate voice using GPT-4o-mini TTS"""
    if not script:
        print("⚠️ No script provided.")
        return None
    path = "voice.mp3"
    result = safe_openai_call(
        openai.audio.speech.create,
        model="gpt-4o-mini-tts",
        voice=VOICE_STYLE,
        input=script,
        timeout=30
    )
    if result:
        with open(path, "wb") as f:
            f.write(result)
        return path
    return None


def make_video(script, audio_path, duration):
    """Combine video, captions, and background music"""
    try:
        video_path = "assets/backgrounds/stock.mp4"
        music_path = "assets/music/calm_loop.mp3"

        clip = VideoFileClip(video_path).subclip(0, min(duration, clip.duration))
        voice_audio = AudioFileClip(audio_path)
        music = AudioFileClip(music_path).volumex(0.15).set_duration(duration)

        combined_audio = CompositeAudioClip([voice_audio, music])
        clip = clip.set_audio(combined_audio)

        # captions
        wrapped = textwrap.wrap(script, width=40)
        caption_clips = []
        per_line = duration / max(len(wrapped), 1)
        start_time = 0

        for line in wrapped:
            txt = TextClip(
                line,
                fontsize=CAPTION_FONT_SIZE,
                color=CAPTION_COLOR,
                font="assets/fonts/Roboto-Regular.ttf",
            ).set_position(("center", "bottom")).set_duration(per_line).set_start(start_time)
            caption_clips.append(txt)
            start_time += per_line

        final = CompositeVideoClip([clip, *caption_clips])
        final.write_videofile("final.mp4", codec="libx264", audio_codec="aac", verbose=False, logger=None)
        return "final.mp4"
    except Exception as e:
        print(f"❌ Error making video: {e}")
        return None


def upload_video(video_path, caption):
    """Placeholder for TikTok upload logic"""
    print(f"Uploading {video_path} with caption: {caption[:150]}...")
    return True


# -------------------------------
# MAIN BOT LOOP
# -------------------------------
def main():
    print("🚀 AI TikTok Poster started using GPT-4o-mini")
    for run in range(MAX_RUNS):
        try:
            print(f"\n🎬 Run {run+1}/{MAX_RUNS}")
            duration = random.randint(MIN_VIDEO_LENGTH, MAX_VIDEO_LENGTH)
            print(f"⏱️ Target duration: {duration}s")

            script = generate_script(NICHE, duration)
            if not script:
                continue

            hashtags = generate_hashtags(NICHE)
            caption = f"{script[:150]}... {hashtags}"

            voice = generate_voice(script)
            if not voice:
                continue

            video = make_video(script, voice, duration)
            if not video:
                continue

            if not DEBUG_MODE:
                upload_video(video, caption)
                print("✅ Posted successfully!")
            else:
                print("🧪 Debug mode active — video saved but not posted.")

        except Exception as e:
            print(f"❌ Fatal error: {e}")
            time.sleep(5)

        print(f"⏳ Waiting {POST_INTERVAL} minutes until next post...")
        time.sleep(POST_INTERVAL * 60)

    print("\n✅ Finished daily limit. Stopping safely.")


if __name__ == "__main__":
    main()
