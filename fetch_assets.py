"""Utility script to download fresh background videos from Pexels."""

from __future__ import annotations

import argparse
import logging

from app.assets import download_pexels_videos
from app.config import load_config
from app.logging_utils import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch portrait videos from Pexels")
    parser.add_argument("--query", default="motivation", help="Search term to use.")
    parser.add_argument("--count", type=int, default=5, help="Number of clips to download.")
    args = parser.parse_args()

    config = load_config()
    configure_logging(config.paths.logs_dir)

    if not config.pexels_api_key:
        raise SystemExit("PEXELS_API_KEY missing. Set it in config.txt or env variables.")

    downloaded = download_pexels_videos(
        config.pexels_api_key,
        config.paths.videos_dir,
        query=args.query,
        count=args.count,
    )
    logging.getLogger(__name__).info("Downloaded %s videos", len(downloaded))


if __name__ == "__main__":
    main()
