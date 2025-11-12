"""Command line interface for the TikTok auto-poster."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.config import AppConfig, load_config
from app.runner import AutoPoster
from app.scheduler import SchedulerService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-powered TikTok auto poster")
    parser.add_argument(
        "command",
        choices=["run-once", "schedule", "show-config"],
        help="Action to perform.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config.txt file (overrides CONFIG_FILE env).",
    )
    return parser.parse_args()


def load_app_config(path: Path | None) -> AppConfig:
    if path:
        return load_config(path)
    return load_config()


def main() -> None:
    args = parse_args()
    config = load_app_config(args.config)

    if args.command == "show-config":
        print(config.config_json)
        return

    poster = AutoPoster(config)

    if args.command == "run-once":
        poster.run_once()
    elif args.command == "schedule":
        scheduler = SchedulerService(config)
        scheduler.start()


if __name__ == "__main__":
    main()
