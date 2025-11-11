import os
import time
import random
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from tiktok_uploader.upload import upload_video

# ✅ Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
POST_INTERVAL = int(os.getenv("POST_INTERVAL", 3600))
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID")
VIDEOS_DIR = os.getenv("VIDEOS_DIR", "assets/videos")
MUSIC_DIR = os.getenv("MUSIC_DIR", "assets/music")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Basic safety log
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

# ✅ Create motivational quote
def generate_quote():
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You write short, viral motivational quotes."},
                {"role": "user", "content": "Give me one short motivational quote (10-20 words) that could go viral on TikTok."}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        log(f"⚠️ AI Error: {e}")
        if "insufficient_quota" in str(e).lower():
            log("🚫 OpenAI quota exceeded. Stopping script to avoid charges.")
            exit(1)
        return None

# ✅ Create video
def create_video(quote):
    try:
        video_path = os.path.join(VIDEOS_DIR, random.cho
