import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# -------------------- SETTINGS --------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID")
UPLOAD_WAIT = 15           # Wait after clicking Post
MAX_RETRIES = 3            # How many times to retry
RETRY_DELAY = 600          # 10 minutes between retries
DEFAULT_NICHE = os.getenv("NICHE", "motivation")

# -------------------- DRIVER SETUP --------------------
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# -------------------- LOGIN --------------------
def tiktok_login(driver):
    logging.info("Logging into TikTok using session cookie...")
    driver.get("https://www.tiktok.com/upload?lang=en")

    driver.add_cookie({
        "name": "sessionid",
        "value": TIKTOK_SESSION_ID,
        "domain": ".tiktok.com",
        "path": "/"
    })
    driver.refresh()
    time.sleep(3)

    if "upload" in driver.current_url:
        logging.info("✅ Logged into TikTok successfully.")
        return True
    else:
        logging.warning("⚠️ TikTok login failed — check session ID or expiration.")
        return False

# -------------------- HASHTAG GENERATOR --------------------
def generate_hashtags(niche="motivation"):
    hashtag_dict = {
        "motivation": [
            "#motivation", "#success", "#inspiration", "#mindset",
            "#nevergiveup", "#goals", "#fyp", "#motivationalquotes",
            "#positivity", "#selfimprovement"
        ],
        "fitness": [
            "#fitness", "#gym", "#workout", "#fitlife", "#transformation",
            "#fyp", "#health", "#dedication", "#fitmotivation"
        ],
        "lifestyle": [
            "#lifestyle", "#dailyvibes", "#countryliving", "#happiness",
            "#selflove", "#relax", "#goodvibes", "#momlife", "#fyp"
        ],
        "dogs": [
            "#dogsoftiktok", "#puppylove", "#fyp", "#doglife", "#cutedog",
            "#dogs", "#doglover", "#petsoftiktok"
        ]
    }

    hashtags = hashtag_dict.get(niche.lower(), hashtag_dict["motivation"])
    random.shuffle(hashtags)
    return " ".join(hashtags[:6])

# -------------------- ATTEMPT UPLOAD --------------------
def attempt_upload(video_path, caption):
    driver = get_driver()
    try:
        if not tiktok_login(driver):
            return False

        driver.get("https://www.tiktok.com/upload?lang=en")
        time.sleep(5)

        upload_input = driver.find_element(By.XPATH, '//input[@type="file"]')
        upload_input.send_keys(video_path)
        logging.info("🎥 Video file loaded.")

        time.sleep(5)
        caption_box = driver.find_element(By.XPATH, '//div[@role="textbox"]')
        caption_box.send_keys(caption)
        logging.info("📝 Caption added.")

        post_button = driver.find_element(By.XPATH, '//button[contains(text(), "Post")]')
        post_button.click()
        logging.info("🚀 Video upload started... waiting to confirm.")
        time.sleep(UPLOAD_WAIT)

        logging.info("✅ Upload finished successfully!")
        return True

    except Exception as e:
        logging.error(f"❌ Upload attempt failed: {e}")
        return False

    finally:
        driver.quit()

# -------------------- RETRY HANDLER --------------------
def upload_video(video_path, quote):
    caption = f"{quote}\n\n{generate_hashtags(DEFAULT_NICHE)}"

    for attempt in range(1, MAX_RETRIES + 1):
        logging.info(f"🌀 Upload attempt {attempt}/{MAX_RETRIES}")
        if attempt_upload(video_path, caption):
            logging.info("✅ TikTok upload confirmed successful.")
            return True
        else:
            logging.warning(f"⚠️ Upload failed. Retrying in {RETRY_DELAY // 60} minutes...")
            time.sleep(RETRY_DELAY)

    logging.error("❌ All upload attempts failed. Skipping this video.")
    return False
