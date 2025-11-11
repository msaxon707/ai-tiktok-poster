import os, time, random, csv, textwrap, requests
from datetime import datetime
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TIKTOK_SESSION = os.getenv("TIKTOK_SESSION_ID")

POST_INTERVAL = int(os.getenv("POST_INTERVAL", 180))
MAX_RUNS = int(os.getenv("MAX_RUNS", 8))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", 40))
CAPTION_COLOR = os.getenv("CAPTION_COLOR", "white")

def log_event(status, caption, bg="", music="", error=""):
    log_exists = os.path.exists("log.csv")
    with open("log.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not log_exists:
            w.writerow(["timestamp", "status", "caption", "background", "music", "error"])
        w.writerow([datetime.now(), status, caption, bg, music, error])

def choose_asset(path):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return os.path.join(path, random.choice(files))

def ai_text(prompt):
    try:
        r = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return r.choices[0].message.content.strip()
    except Exception as e:
        print("AI Error:", e)
        return None

def generate_script():
    duration = random.randint(25, 45)
    prompt = f"Write a motivational TikTok script for a {duration}-second video. Make it inspiring and emotional."
    return ai_text(prompt), duration

def generate_hashtags():
    prompt = "Give me 5 trending hashtags for motivational TikToks (short list separated by spaces)."
    tags = ai_text(prompt)
    return tags if tags else "#motivation #inspiration #fyp"

def generate_voice(script):
    try:
        out_path = "voice.mp3"
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice="alloy", input=script
        ) as response:
            response.stream_to_file(out_path)
        return out_path
    except Exception as e:
        print("Voice Error:", e)
        return None

def make_video(script, audio_path, duration):
    try:
        bg_video = choose_asset("assets/backgrounds")
        music = choose_asset("assets/music")
        clip = VideoFileClip(bg_video).subclip(0, min(duration, VideoFileClip(bg_video).duration))
        voice = AudioFileClip(audio_path)
        music_audio = AudioFileClip(music).volumex(0.15).set_duration(duration)
        clip = clip.set_audio(CompositeAudioClip([voice, music_audio]))

        lines = textwrap.wrap(script, width=40)
        per_line = duration / max(len(lines), 1)
        captions = []
        t = 0
        for line in lines:
            txt = TextClip(
                line, fontsize=CAPTION_FONT_SIZE, color=CAPTION_COLOR,
                font="assets/fonts/Roboto-Regular.ttf", method="caption"
            ).set_position(("center", "bottom")).set_duration(per_line).set_start(t)
            captions.append(txt)
            t += per_line

        final = CompositeVideoClip([clip, *captions])
        final.write_videofile("final.mp4", codec="libx264", audio_codec="aac", verbose=False, logger=None)
        return "final.mp4", os.path.basename(bg_video), os.path.basename(music)
    except Exception as e:
        print("Video Error:", e)
        raise

def upload_tiktok(video_path, caption):
    if not TIKTOK_SESSION:
        print("⚠️ Missing TikTok session ID.")
        return False
    try:
        url = "https://www.tiktok.com/upload?lang=en"
        cookies = {"sessionid": TIKTOK_SESSION}
        files = {"video": open(video_path, "rb")}
        data = {"caption": caption}
        r = requests.post(url, files=files, data=data, cookies=cookies)
        print("TikTok upload status:", r.status_code)
        return r.status_code == 200
    except Exception as e:
        print("Upload error:", e)
        return False

def main():
    print("🚀 AI Motivational Video Poster started.")
    for run in range(MAX_RUNS):
        try:
            print(f"\n▶️ Run {run+1}/{MAX_RUNS}")
            script, duration = generate_script()
            if not script: continue
            hashtags = generate_hashtags()
            caption = f"{script[:150]}... {hashtags}"
            voice = generate_voice(script)
            if not voice: continue
            video, bg, music = make_video(script, voice, duration)

            if DEBUG_MODE:
                print("🧪 Debug mode: video created but not uploaded.")
            else:
                success = upload_tiktok(video, caption)
                log_event("success" if success else "fail", caption, bg, music)
                print("✅ Posted!" if success else "❌ Upload failed.")
            print(f"⏳ Sleeping {POST_INTERVAL} minutes...")
            time.sleep(POST_INTERVAL * 60)
        except Exception as e:
            log_event("error", "", "", "", str(e))
            print("Error:", e)
    print("✅ All done for today!")

if __name__ == "__main__":
    main()
