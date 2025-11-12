"""Job scheduling utilities."""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone

from .config import AppConfig
from .runner import AutoPoster

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.poster = AutoPoster(config)
        self.scheduler = BlockingScheduler(timezone=timezone(config.schedule.timezone))

    def start(self) -> None:
        interval_hours = max(1, self.config.schedule.interval_hours)
        trigger = IntervalTrigger(hours=interval_hours, jitter=self.config.schedule.jitter_minutes * 60)
        logger.info(
            "Scheduling auto-post job every %s hour(s) with up to %s minutes jitter.",
            interval_hours,
            self.config.schedule.jitter_minutes,
        )
        self.scheduler.add_job(self.poster.run_once, trigger=trigger, id="tiktok-auto-post", max_instances=1)

        if self.config.schedule.start_immediately:
            logger.info("Running first job immediately before entering scheduler loop.")
            self.poster.run_once()

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped by user.")
        finally:
            self.scheduler.shutdown(wait=False)


__all__ = ["SchedulerService"]
