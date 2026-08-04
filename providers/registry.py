from __future__ import annotations

from collections import Counter
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils.http import HttpClient
from utils.models import Company, Job, SourceUrl


class ProviderRegistry:
    SUPPORTED = {
        "greenhouse",
        "lever",
        "ashby",
        "smartrecruiters",
    }

    DETECTION_STATS = Counter()

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def fetch(self, company: Company, source: SourceUrl) -> list[Job]:
        provider = source.provider or self._detect(source.url)

        self.DETECTION_STATS[provider] += 1

        endpoint, params = self._endpoint(provider, source.url)

        if endpoint is None:
            self._log_unsupported(company.name, source.url, provider)
            return []

        print(
            f"INFO: {company.name}\n"
            f"      Provider : {provider}\n"
            f"      Endpoint : {endpoint}"
        )

        data = self.http.get_json(endpoint, params=params)

        records = (
            data
            if isinstance(data, list)
            else next(
                (
                    data.get(key, [])
                    for key in ("jobs", "postings", "results")
                    if isinstance(data.get(key), list)
                ),
                [],
            )
        )

        jobs = [
            job
            for item in records
            if isinstance(item, dict)
            and (job := self._parse(provider, company.name, item))
        ]

        print(
            f"INFO: Fetched {len(jobs)} job(s) for {company.name} via {provider}"
        )

        return jobs

    @classmethod
    def print_summary(cls) -> None:
        print()
        print("=" * 60)
        print("Provider Detection Summary")
        print("=" * 60)

        for provider, count in sorted(cls.DETECTION_STATS.items()):
            status = (
                "SUPPORTED"
                if provider in cls.SUPPORTED
                else "NOT IMPLEMENTED"
            )

            print(
                f"{provider:<20} {count:>4} source(s)   {status}"
            )

        print("=" * 60)
        print()

    @staticmethod
    def _log_unsupported(company: str, url: str, provider: str) -> None:

        if provider == "unknown":
            status = "UNKNOWN PLATFORM"
        else:
            status = "NOT IMPLEMENTED"

        print(
            f"INFO: Company  : {company}\n"
            f"      URL      : {url}\n"
            f"      Provider : {provider}\n"
            f"      Status   : {status}"
        )

    @staticmethod
    def _detect(url: str) -> str:
        host = urlparse(url).netloc.casefold()
        full = url.casefold()

        markers = {
            "greenhouse.io": "greenhouse",
            "boards.greenhouse.io": "greenhouse",

            "lever.co": "lever",

            "ashbyhq.com": "ashby",

            "smartrecruiters.com": "smartrecruiters",

            "myworkdayjobs": "workday",
            "workday": "workday",

            "successfactors": "successfactors",

            "oracle": "oracle",

            "icims": "icims",

            "taleo": "taleo",
            "phh.tbe": "taleo",

            "eightfold": "eightfold",

            "dayforce": "dayforce",
        }

        for marker, provider in markers.items():
            if marker in host or marker in full:
                return provider

        return "unknown"

    @staticmethod
    def _endpoint(provider: str, url: str) -> tuple[str | None, dict]:
        parts = [part for part in urlparse(url).path.split("/") if part]

        if not parts:
            return None, {}

        if provider == "greenhouse":
            token = (
                parts[parts.index("boards") + 1]
                if "boards" in parts
                and parts.index("boards") + 1 < len(parts)
                else parts[0]
            )

            return (
                f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
                {"content": "true"},
            )

        if provider == "lever":
            return (
                f"https://api.lever.co/v0/postings/{parts[0]}",
                {"mode": "json"},
            )

        if provider == "ashby":
            return (
                f"https://api.ashbyhq.com/posting-api/job-board/{parts[0]}",
                {"includeCompensation": "true"},
            )

        if provider == "smartrecruiters":
            return (
                f"https://api.smartrecruiters.com/v1/companies/{parts[0]}/postings",
                {"limit": 100},
            )

        return None, {}

    @staticmethod
    def _parse(provider: str, company: str, item: dict) -> Job | None:
        title = str(item.get("title") or item.get("name") or "").strip()

        if not title:
            return None

        location = item.get("location", "")

        if isinstance(location, dict):
            location = location.get("name", "")

        if isinstance(location, list):
            location = ", ".join(map(str, location))

        description = (
            item.get("content")
            or item.get("descriptionHtml")
            or item.get("description")
            or item.get("text")
            or ""
        )

        description = BeautifulSoup(
            unescape(str(description)),
            "html.parser",
        ).get_text(" ", strip=True)

        url = str(
            item.get("absolute_url")
            or item.get("hostedUrl")
            or item.get("applyUrl")
            or item.get("ref")
            or item.get("url")
            or ""
        )

        text = f"{title} {location}"

        return Job(
            title,
            company,
            str(location),
            description,
            url,
            provider,
            "remote" in text.casefold(),
            item,
        )