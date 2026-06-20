"""Base connector class for all data sources."""

from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode


@dataclass
class DataResult:
    """Standardized result from any data connector."""
    source: str
    query: dict
    data: Any
    timestamp: float = field(default_factory=time.time)
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseConnector(ABC):
    """Abstract base for all data connectors."""

    name: str = "base"
    cost_tier: str = "free"  # free | low_cost | paid
    requires_key: bool = False
    base_url: str = ""
    rate_limit_per_min: int = 30
    _last_call: float = 0

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _rate_wait(self):
        """Simple rate limiter."""
        min_interval = 60.0 / self.rate_limit_per_min
        elapsed = time.time() - self._last_call
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_call = time.time()

    def _get(self, url: str, params: dict | None = None, headers: dict | None = None) -> Any:
        """HTTP GET with basic error handling."""
        self._rate_wait()
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        req = Request(url)
        req.add_header("User-Agent", "Aximora-DataCollector/1.0")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            raise ConnectionError(f"HTTP {e.code}: {e.reason} — {url}") from e
        except URLError as e:
            raise ConnectionError(f"URL error: {e.reason} — {url}") from e

    def _post(self, url: str, payload: dict, headers: dict | None = None) -> Any:
        """HTTP POST with JSON body."""
        self._rate_wait()
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "Aximora-DataCollector/1.0")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise ConnectionError(f"HTTP {e.code}: {body[:500]}") from e
        except URLError as e:
            raise ConnectionError(f"URL error: {e.reason}") from e

    @abstractmethod
    def query(self, **kwargs) -> DataResult:
        """Execute a query against this data source."""
        ...

    def health_check(self) -> bool:
        """Quick connectivity test."""
        try:
            self.query()
            return True
        except Exception:
            return False

    def info(self) -> dict:
        return {
            "name": self.name,
            "cost_tier": self.cost_tier,
            "requires_key": self.requires_key,
            "base_url": self.base_url,
            "rate_limit_per_min": self.rate_limit_per_min,
        }
