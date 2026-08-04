from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from config.settings import settings
from notifications.telegram import TelegramNotifier
from providers.registry import ProviderRegistry
from utils.http import HttpClient
from utils.models import Company, Job, SourceUrl


class Engine:
    def __init__(self) -> None:
        http = HttpClient()
        self.registry, self.notifier = ProviderRegistry(http), TelegramNotifier(http)
        self.seen = self._load_state()

    def run(self) -> int:
        matches = 0
        for company in self.load_companies():
            if not company.enabled:
                continue
            for source in company.urls:
                try:
                    for job in self.registry.fetch(company, source):
                        if self._matches(job) and job.identity not in self.seen:
                            matches += 1
                            if not settings.dry_run:
                                self.notifier.send_job(job)
                                self.seen.add(job.identity)
                except Exception as error:
                    print(f"WARNING: {company.name} {source.url}: {error}")
        if not settings.dry_run:
            self._save_state()
        self.notifier.send_status(matches, settings.dry_run)
        return matches

    @staticmethod
    def load_companies(path: Path = Path("config/companies.yaml")) -> list[Company]:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return [Company(item["name"], tuple(SourceUrl(entry["url"], entry.get("provider")) for entry in item.get("urls", [])), item.get("priority", "NORMAL"), item.get("enabled", True)) for item in data.get("companies", [])]

    def _matches(self, job: Job) -> bool:
        text = f"{job.title} {job.description}".casefold()
        location = job.location.casefold()
        return any(word in text for word in settings.keywords) and (job.remote or any(place in location for place in settings.locations)) and self._experience_ok(text)

    @staticmethod
    def _experience_ok(text: str) -> bool:
        years = [int(value) for value in re.findall(r"\b(\d{1,2})\s*(?:\+|years?|yrs?)", text)]
        return not years or min(years) <= settings.max_experience and max(years) >= settings.min_experience

    def _load_state(self) -> set[str]:
        try: return set(json.loads(settings.state_file.read_text(encoding="utf-8")).get("seen", []))
        except (FileNotFoundError, json.JSONDecodeError): return set()

    def _save_state(self) -> None:
        settings.state_file.write_text(json.dumps({"seen": sorted(self.seen)}, indent=2), encoding="utf-8")

