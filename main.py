import os, time, random, json, requests
from openai import OpenAI
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4o-mini")
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 3600))
VIDEOS_DIR = "assets/videos"
MUSIC_DIR = "assets/music"
OUTPUT_DIR = "output"
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------
# Generate Quote Safely
# ---------------------------
def safe_generate_quote():
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You create short, positive motivational quotes."},
                {"role": "user", "content": "Write a single uplifting motivational quote for TikTok."}
            ],
            max_tokens=40
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return None

# ---------------------------
# Create Video
# ---------------------------
def create_video(quote):
    try:
        videos = [f for f in os.listdir(VIDEOS_DIR) if f.endswith(".mp4")]
        musics = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        if not videos or not musics:
            print("⚠️ No media found.")
            return None

        video_path = os.path.join(VIDEOS_DIR, random.choice(videos))
        music_path = os.path.join(MUSIC_DIR, random.choice(musics))
        output_path = os.path.join(OUTPUT_DIR, f"motiv_{int(time.time())}.mp4")

        clip = VideoFileClip(video_path)
        if clip.duration < 5 or clip.duration > 60:
            print("⚠️ Video not within TikTok time limits.")
            return None

        audio = AudioFileClip(music_path)
        text = TextClip(quote, fontsize=40, color="white", font="Roboto", method='caption',
                        size=clip.size, align='center', interline=5).set_duration(clip.duration)
        final = CompositeVideoClip([clip, text.set_position("center").set_opacity(0.9)]).set_audio(audio)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        return output_path
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        return None

# ---------------------------
# Upload to TikTok
# ---------------------------
def upload_to_tiktok(video_path, caption):
    if not TIKTOK_SESSION_ID:
        print("⚠️ Missing TikTok Session ID. Skipping upload.")
        return False

    cookies = {"sessionid": TIKTOK_SESSION_ID}
    upload_url = "https://open-api.tiktok.com/share/video/upload/"
    data = {
        "caption": caption[:2200]  # TikTok caption limit
    }

    try:
        with open(video_path, "rb") as f:
            files = {"video": f}
            r = requests.post(upload_url, files=files, data=data, cookies=cookies)
            if r.status_code == 200:
                print("✅ Video uploaded to TikTok successfully!")
                return True
            else:
                print(f"⚠️ Upload failed: {r.text}")
                return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

# ---------------------------
# Main Loop
# ---------------------------
def main():
    print("🚀 Starting AI TikTok Auto Poster")
    for i in range(3):  # Default 3 posts/day
        print(f"\n▶️ Run {i+1}/3")
        quote = safe_generate_quote()
        if not quote:
            continue

        video_path = create_video(quote)
        if not video_path:
            continue

        hashtags = "#motivation #inspiration #selfgrowth #positivity"
        caption = f"{quote}\n\n{hashtags}"
        upload_to_tiktok(video_path, caption)

        if i < 2:
            print(f"⏱ Waiting {POST_INTERVAL}s before next post...")
            time.sleep(POST_INTERVAL)
    print("✅ All done for today!")

if __name__ == "__main__":
    main()
