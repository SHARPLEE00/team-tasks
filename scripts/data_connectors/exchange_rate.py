"""
ExchangeRate-API — 汇率数据
https://open.er-api.com/

免费层: 无需Key，每日更新，支持150+货币。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class ExchangeRateConnector(BaseConnector):
    name = "exchange_rate"
    cost_tier = "free"
    requires_key = False
    base_url = "https://open.er-api.com/v6/latest"
    rate_limit_per_min = 30

    # 常用货币
    USD = "USD"
    CNY = "CNY"
    VND = "VND"
    EUR = "EUR"

    def query(
        self,
        base_currency: str = "USD",
        target_currencies: list[str] | None = None,
    ) -> DataResult:
        """
        获取实时汇率。

        Args:
            base_currency: 基准货币 (USD/CNY/VND 等)
            target_currencies: 目标货币列表 (None=全部)
        """
        url = f"{self.base_url}/{base_currency}"

        query_desc = {
            "base_currency": base_currency,
            "target_currencies": target_currencies,
        }

        try:
            raw = self._get(url)
            if raw.get("result") == "success":
                rates = raw.get("rates", {})
                if target_currencies:
                    rates = {k: v for k, v in rates.items() if k in target_currencies}
                return DataResult(
                    source=self.name,
                    query=query_desc,
                    data=rates,
                    metadata={
                        "base": base_currency,
                        "time_last_update": raw.get("time_last_update_utc"),
                    },
                )
            return DataResult(
                source=self.name,
                query=query_desc,
                data={},
                error=f"API error: {raw.get('error-type', 'unknown')}",
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data={},
                error=str(e),
            )

    def convert(self, amount: float, from_currency: str, to_currency: str) -> DataResult:
        """快捷：货币换算。"""
        result = self.query(base_currency=from_currency, target_currencies=[to_currency])
        if result.ok and to_currency in result.data:
            rate = result.data[to_currency]
            converted = amount * rate
            result.data = {
                "from": from_currency,
                "to": to_currency,
                "amount": amount,
                "rate": rate,
                "converted": converted,
            }
        return result
