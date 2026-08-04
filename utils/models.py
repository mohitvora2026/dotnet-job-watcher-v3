from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceUrl:
    url: str
    provider: str | None = None


@dataclass(frozen=True, slots=True)
class Company:
    name: str
    urls: tuple[SourceUrl, ...]
    priority: str = "NORMAL"
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    provider: str
    remote: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> str:
        return self.url or f"{self.company}|{self.title}|{self.location}"

