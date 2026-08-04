from __future__ import annotations

from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils.http import HttpClient
from utils.models import Company, Job, SourceUrl


class ProviderRegistry:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def fetch(self, company: Company, source: SourceUrl) -> list[Job]:
        provider = source.provider or self._detect(source.url)
        endpoint, params = self._endpoint(provider, source.url)
        if endpoint is None:
            print(f"INFO: Skipping unsupported source for {company.name}: {source.url}")
            return []
        data = self.http.get_json(endpoint, params=params)
        records = data if isinstance(data, list) else next((data.get(key, []) for key in ("jobs", "postings", "results") if isinstance(data.get(key), list)), [])
        jobs = [job for item in records if isinstance(item, dict) and (job := self._parse(provider, company.name, item))]
        print(f"INFO: Fetched {len(jobs)} job(s) for {company.name} via {provider}")
        return jobs

    @staticmethod
    def _detect(url: str) -> str:
        host = urlparse(url).netloc.casefold()
        for fragment, name in {"greenhouse.io": "greenhouse", "lever.co": "lever", "ashbyhq.com": "ashby", "smartrecruiters.com": "smartrecruiters"}.items():
            if fragment in host:
                return name
        return "unsupported"

    @staticmethod
    def _endpoint(provider: str, url: str) -> tuple[str | None, dict]:
        parts = [part for part in urlparse(url).path.split("/") if part]
        if not parts:
            return None, {}
        if provider == "greenhouse":
            token = parts[parts.index("boards") + 1] if "boards" in parts and parts.index("boards") + 1 < len(parts) else parts[0]
            return f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", {"content": "true"}
        if provider == "lever":
            return f"https://api.lever.co/v0/postings/{parts[0]}", {"mode": "json"}
        if provider == "ashby":
            return f"https://api.ashbyhq.com/posting-api/job-board/{parts[0]}", {"includeCompensation": "true"}
        if provider == "smartrecruiters":
            return f"https://api.smartrecruiters.com/v1/companies/{parts[0]}/postings", {"limit": 100}
        return None, {}

    @staticmethod
    def _parse(provider: str, company: str, item: dict) -> Job | None:
        title = str(item.get("title") or item.get("name") or "").strip()
        if not title:
            return None
        location = item.get("location", "")
        if isinstance(location, dict): location = location.get("name", "")
        if isinstance(location, list): location = ", ".join(map(str, location))
        description = item.get("content") or item.get("descriptionHtml") or item.get("description") or item.get("text") or ""
        description = BeautifulSoup(unescape(str(description)), "html.parser").get_text(" ", strip=True)
        url = str(item.get("absolute_url") or item.get("hostedUrl") or item.get("applyUrl") or item.get("ref") or item.get("url") or "")
        text = f"{title} {location}"
        return Job(title, company, str(location), description, url, provider, "remote" in text.casefold(), item)
