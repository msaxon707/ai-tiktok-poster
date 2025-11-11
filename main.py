import os, time, random, csv, textwrap
from datetime import datetime
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- ENV CONFIG ---
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 180))
MAX_RUNS = int(os.getenv("MAX_RUNS", 8))
MIN_VIDEO_LENGTH = int(os.getenv("MIN_VIDEO_LENGTH", 20))
MAX_VIDEO_LENGTH = int(os.getenv("MAX_VIDEO_LENGTH", 45))
CAPTION_COLOR = os.getenv("CAPTION_COLOR", "white")
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", 40))
VOICE_STYLE = os.getenv("VOICE_STYLE", "alloy")
NICHE = os.getenv("NICHE", "motivation")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

last_bg, last_music = None, None


def log_event(status, caption, bg="", music="", error=""):
    log_exists = os.path.exists("log.csv")
    with open("log.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not log_exists:
            w.writerow(["timestamp", "status", "caption", "background", "music", "error"])
        w.writerow([datetime.now(), status, caption, bg, music, error])


def choose_asset(path, last_used):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    if not files:
        raise FileNotFoundError(f"No files found in {path}")
    choice = random.choice(files)
    while choice == last_used and len(files) > 1:
        choice = random.choice(files)
    return os.path.join(path, choice), choice


def ai_text(prompt):
    try:
        r = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return r.choices[0].message.content.strip()
    except Exception as e:
        print("AI Error:", e)
        return None


def generate_script():
    duration = random.randint(MIN_VIDEO_LENGTH, MAX_VIDEO_LENGTH)
    prompt = f"Write a {duration}-second motivational TikTok script that sounds inspiring and powerful."
    return ai_text(prompt), duration


def generate_hashtags():
    prompt = f"Give 5 trending TikTok hashtags for {NICHE} content. Output them in one line separated by spaces."
    tags = ai_text(prompt)
    return tags if tags else "#motivation #inspiration #fyp"


def generate_voice(script):
    try:
        path = "voice.mp3"
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice=VOICE_STYLE, input=script
        ) as response:
            response.stream_to_file(path)
        return path
    except Exception as e:
        print("Voice gen error:", e)
        return None


def make_video(script, audio_path, duration):
    global last_bg, last_music
    try:
        bg_video, bg_name = choose_asset("assets/backgrounds", last_bg)
        music_file, music_name = choose_asset("assets/music", last_music)
        last_bg, last_music = bg_name, music_name

        clip = VideoFileClip(bg_video).subclip(0, min(duration, VideoFileClip(bg_video).duration))
        voice = AudioFileClip(audio_path)
        music = AudioFileClip(music_file).volumex(0.15).set_duration(duration)
        final_audio = CompositeAudioClip([voice, music])
        clip = clip.set_audio(final_audio)

        lines = textwrap.wrap(script, width=40)
        caption_clips = []
        per_line = duration / max(len(lines), 1)
        t = 0
        for line in lines:
            txt = TextClip(
                line,
                fontsize=CAPTION_FONT_SIZE,
                color=CAPTION_COLOR,
                font="assets/fonts/Roboto-Regular.ttf",
                method="caption",
            ).set_position(("center", "bottom")).set_duration(per_line).set_start(t)
            caption_clips.append(txt)
            t += per_line

        final = CompositeVideoClip([clip, *caption_clips])
        final.write_videofile("final.mp4", codec="libx264", audio_codec="aac", verbose=False, logger=None)
        return "final.mp4", bg_name, music_name
    except Exception as e:
        print("Video error:", e)
        raise


def upload_video(video_path, caption):
    # Placeholder: TikTok upload logic here if you add session ID integration later
    print(f"Uploading {video_path} with caption:\n{caption}\n")
    return True


def main():
    print("🚀 AI Motivational Video Poster started.")
    for run in range(MAX_RUNS):
        print(f"\n▶️ Run {run+1}/{MAX_RUNS}")
        try:
            script, duration = generate_script()
            if not script:
                log_event("fail", "no script")
                continue
            hashtags = generate_hashtags()
            caption = f"{script[:150]}... {hashtags}"
            voice = generate_voice(script)
            if not voice:
                log_event("fail", caption, error="voice failed")
                continue
            video, bg, music = make_video(script, voice, duration)
            if not video:
                log_event("fail", caption, bg, music, "video failed")
                continue
            if not DEBUG_MODE:
                upload_video(video, caption)
                log_event("success", caption, bg, music)
                print("✅ Posted successfully!")
            else:
                log_event("debug", caption, bg, music, "not posted (debug)")
                print("🧪 Debug mode, video saved only.")
        except Exception as e:
            log_event("error", "", "", "", str(e))
            print("❌ Error:", e)
        print(f"⏳ Sleeping {POST_INTERVAL} minutes...")
        time.sleep(POST_INTERVAL * 60)
    print("✅ Finished daily cycle.")


if __name__ == "__main__":
    main()
