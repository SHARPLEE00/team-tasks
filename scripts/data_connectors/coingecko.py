"""
CoinGecko API — 加密货币价格/市场数据
https://www.coingecko.com/en/api

免费层: 无需 Key，30次/分钟。
覆盖 14,000+ 币种，含市值/交易量/历史价格。
(跨境支付/crypto结算调研用)
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class CoinGeckoConnector(BaseConnector):
    name = "coingecko"
    cost_tier = "free"
    requires_key = False
    base_url = "https://api.coingecko.com/api/v3"
    rate_limit_per_min = 25  # 保守

    def query(
        self,
        ids: str = "bitcoin,ethereum,tether",
        vs_currencies: str = "usd,cny,vnd",
    ) -> DataResult:
        """获取加密货币当前价格。"""
        url = f"{self.base_url}/simple/price"
        params = {
            "ids": ids,
            "vs_currencies": vs_currencies,
            "include_24hr_change": "true",
            "include_market_cap": "true",
        }
        query_desc = {"ids": ids, "vs_currencies": vs_currencies}
        try:
            raw = self._get(url, params=params)
            return DataResult(source=self.name, query=query_desc, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data={}, error=str(e))

    def trending(self) -> DataResult:
        """获取热门加密货币。"""
        url = f"{self.base_url}/search/trending"
        try:
            raw = self._get(url)
            return DataResult(source=self.name, query={"action": "trending"}, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query={"action": "trending"}, data={}, error=str(e))

    def global_market(self) -> DataResult:
        """获取全球加密市场总览。"""
        url = f"{self.base_url}/global"
        try:
            raw = self._get(url)
            return DataResult(source=self.name, query={"action": "global"}, data=raw.get("data", raw))
        except Exception as e:
            return DataResult(source=self.name, query={"action": "global"}, data={}, error=str(e))
