# upload.py
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

def upload_to_tiktok(video_path: str, caption: str, session_id: Optional[str] = None) -> bool:
    """
    Placeholder TikTok uploader.

    Right now this function:
      - Logs what it *would* upload
      - Returns True to let the pipeline continue

    To actually upload, replace this body with real TikTok uploading logic,
    using your session cookie or a proper TikTok API/client.
    """
    if session_id is None:
        session_id = os.getenv("TIKTOK_SESSION_ID")

    logger.info("---- TikTok UPLOAD (SIMULATED) ----")
    logger.info(f"Video:   {video_path}")
    logger.info(f"Caption: {caption}")
    logger.info(f"Session: {'SET' if session_id else 'NOT SET'}")
    logger.info("No real upload is being performed (stub function).")
    return True
