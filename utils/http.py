from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings


class HttpClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "dotnet-job-watcher-v3/3.0"
        self.session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))))

    def get_json(self, url: str, **kwargs):
        response = self.session.get(url, timeout=settings.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, url: str, **kwargs):
        response = self.session.post(url, timeout=settings.timeout, **kwargs)
        response.raise_for_status()
        return response

