"""
Connector Registry — 统一管理所有数据连接器。

用法:
    from data_connectors import get_registry

    reg = get_registry()

    # 列出所有可用连接器
    reg.list_connectors()

    # 获取单个连接器
    wb = reg.get("world_bank")
    result = wb.query(country="CHN", indicator="NY.GDP.MKTP.CD")

    # 批量健康检查
    reg.health_check_all()

    # 只获取免费的连接器
    free = reg.get_by_tier("free")
"""

from __future__ import annotations
import os
from typing import Iterator
from .base import BaseConnector
from .un_comtrade import UNComtradeConnector
from .world_bank import WorldBankConnector
from .oecd_data import OECDConnector
from .china_data_portal import ChinaDataPortalConnector
from .google_trends import GoogleTrendsConnector
from .exchange_rate import ExchangeRateConnector
from .dataforseo import DataForSEOConnector
from .echotik import EchoTikConnector


class ConnectorRegistry:
    """Central registry for all data connectors."""

    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}
        self._init_defaults()

    def _init_defaults(self):
        """Initialize all connectors, reading API keys from env vars."""
        # === 免费层 (无需 Key) ===
        self.register(UNComtradeConnector(
            api_key=os.environ.get("UN_COMTRADE_KEY"),
        ))
        self.register(WorldBankConnector())
        self.register(OECDConnector())
        self.register(ChinaDataPortalConnector())
        self.register(GoogleTrendsConnector())
        self.register(ExchangeRateConnector())

        # === 低成本层 (需 Key) ===
        dataforseo_login = os.environ.get("DATAFORSEO_LOGIN")
        dataforseo_pwd = os.environ.get("DATAFORSEO_PASSWORD")
        if dataforseo_login:
            self.register(DataForSEOConnector(
                api_key=dataforseo_login,
                password=dataforseo_pwd,
            ))
        else:
            self.register(DataForSEOConnector())

        echotik_key = os.environ.get("ECHOTIK_API_KEY")
        self.register(EchoTikConnector(api_key=echotik_key))

    def register(self, connector: BaseConnector):
        self._connectors[connector.name] = connector

    def get(self, name: str) -> BaseConnector:
        if name not in self._connectors:
            available = ", ".join(self._connectors.keys())
            raise KeyError(f"Connector '{name}' not found. Available: {available}")
        return self._connectors[name]

    def get_by_tier(self, tier: str) -> dict[str, BaseConnector]:
        """Get connectors by cost tier (free / low_cost / paid)."""
        return {
            k: v for k, v in self._connectors.items()
            if v.cost_tier == tier
        }

    def list_connectors(self) -> list[dict]:
        """List all connectors with their info."""
        return [c.info() for c in self._connectors.values()]

    def health_check_all(self) -> dict[str, bool]:
        """Run health check on all connectors."""
        results = {}
        for name, conn in self._connectors.items():
            try:
                results[name] = conn.health_check()
            except Exception:
                results[name] = False
        return results

    def __iter__(self) -> Iterator[BaseConnector]:
        return iter(self._connectors.values())

    def __len__(self) -> int:
        return len(self._connectors)

    def __contains__(self, name: str) -> bool:
        return name in self._connectors


_registry: ConnectorRegistry | None = None


def get_registry() -> ConnectorRegistry:
    """Get or create the global connector registry."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry
