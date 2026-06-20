"""
Frankfurter API — 欧洲央行(ECB)汇率数据
https://api.frankfurter.dev/

完全免费，无需 Key，无需注册。
数据源: 欧洲中央银行，30+ 货币，含历史数据。
比 ExchangeRate API 更权威(ECB官方源)。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class FrankfurterConnector(BaseConnector):
    name = "frankfurter"
    cost_tier = "free"
    requires_key = False
    base_url = "https://api.frankfurter.dev/v1"
    rate_limit_per_min = 60

    def query(
        self,
        base: str = "USD",
        symbols: str = "CNY,VND,EUR,JPY",
        date: str = "latest",
    ) -> DataResult:
        """
        获取汇率数据。

        Args:
            base: 基准货币
            symbols: 目标货币(逗号分隔)
            date: "latest" 或 "2024-01-01" 或 "2024-01-01..2024-12-31"
        """
        url = f"{self.base_url}/{date}"
        params = {"base": base, "symbols": symbols}
        query_desc = {"base": base, "symbols": symbols, "date": date}

        try:
            raw = self._get(url, params=params)
            return DataResult(
                source=self.name,
                query=query_desc,
                data=raw.get("rates", raw),
                metadata={"date": raw.get("date"), "base": raw.get("base")},
            )
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data={}, error=str(e))

    def history(self, base: str = "USD", symbols: str = "CNY,VND", start: str = "2024-01-01", end: str = "2024-12-31") -> DataResult:
        """获取历史汇率区间。"""
        return self.query(base=base, symbols=symbols, date=f"{start}..{end}")

    def currencies(self) -> DataResult:
        """列出所有支持的货币。"""
        url = f"{self.base_url}/currencies"
        try:
            raw = self._get(url)
            return DataResult(source=self.name, query={"action": "currencies"}, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query={"action": "currencies"}, data={}, error=str(e))
