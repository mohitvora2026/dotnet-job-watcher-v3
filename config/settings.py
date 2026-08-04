from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(value.strip().casefold() for value in os.getenv(name, default).split(",") if value.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    dry_run: bool = os.getenv("DRY_RUN", "false").casefold() in {"1", "true", "yes"}
    timeout: float = float(os.getenv("REQUEST_TIMEOUT", "20"))
    state_file: Path = Path(os.getenv("STATE_FILE", "state.json"))
    keywords: tuple[str, ...] = field(default_factory=lambda: _csv("TARGET_KEYWORDS", ".net,.net core,asp.net,asp.net core,c#,dotnet"))
    locations: tuple[str, ...] = field(default_factory=lambda: _csv("TARGET_LOCATIONS", "india,remote,hyderabad,bengaluru,bangalore,pune,chennai"))
    min_experience: int = int(os.getenv("MIN_EXPERIENCE", "2"))
    max_experience: int = int(os.getenv("MAX_EXPERIENCE", "5"))


settings = Settings()

