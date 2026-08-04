from __future__ import annotations

from html import escape

from config.settings import settings
from utils.http import HttpClient
from utils.models import Job


class TelegramNotifier:
    def __init__(self, http: HttpClient) -> None: self.http = http

    def send_job(self, job: Job) -> None:
        self._send(f"<b>{escape(job.title)}</b>\n{escape(job.company)} · {escape(job.location or 'Location not specified')}\n<a href=\"{escape(job.url, quote=True)}\">Apply now</a>")

    def send_status(self, matches: int, dry_run: bool, fetched: int, sources_checked: int) -> None:
        prefix = "Dry run" if dry_run else "Job watcher"
        result = f"Matching jobs found: {matches}" if dry_run else f"New jobs sent: {matches}"
        self._send(f"{prefix} completed.\nSources checked: {sources_checked}\nJobs fetched: {fetched}\n{result}")

    def _send(self, message: str) -> None:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            print("WARNING: Telegram credentials are not configured")
            return
        self.http.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage", json={"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True})
