"""Small HTTP helper with retries."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

STAC_URL = "https://data.geo.admin.ch/api/stac/v1"
USER_AGENT = "regenradar/0.1 (+https://github.com/maleanso/regenradar)"

_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        retry = Retry(total=4, backoff_factor=1.0, status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=frozenset({"GET", "POST"}))
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.headers["User-Agent"] = USER_AGENT
        _session = s
    return _session


def get_json(url: str, **kw) -> dict:
    r = session().get(url, timeout=60, **kw)
    r.raise_for_status()
    return r.json()


def post_json(url: str, body: dict) -> dict:
    r = session().post(url, json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def get_bytes(url: str) -> bytes:
    r = session().get(url, timeout=300)
    r.raise_for_status()
    return r.content
