"""
World Bank Open Data API — 宏观经济指标
https://data.worldbank.org/

完全免费，无需 API Key，无限次调用。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class WorldBankConnector(BaseConnector):
    name = "world_bank"
    cost_tier = "free"
    requires_key = False
    base_url = "https://api.worldbank.org/v2"
    rate_limit_per_min = 60

    # 常用指标代码
    GDP = "NY.GDP.MKTP.CD"                    # GDP (current US$)
    GDP_GROWTH = "NY.GDP.MKTP.KD.ZG"          # GDP growth (annual %)
    EXPORTS_GDP = "NE.EXP.GNFS.ZS"           # Exports of goods/services (% of GDP)
    IMPORTS_GDP = "NE.IMP.GNFS.ZS"           # Imports of goods/services (% of GDP)
    TRADE_PCT_GDP = "NE.TRD.GNFS.ZS"         # Trade (% of GDP)
    MANUFACTURING_VA = "NV.IND.MANF.ZS"      # Manufacturing value added (% of GDP)
    HIGH_TECH_EXPORTS = "TX.VAL.TECH.MF.ZS"  # High-technology exports (% manufactured)
    POPULATION = "SP.POP.TOTL"               # Total population
    INFLATION = "FP.CPI.TOTL.ZG"             # Inflation, consumer prices (annual %)
    EXCHANGE_RATE = "PA.NUS.FCRF"             # Official exchange rate (LCU per US$)

    def query(
        self,
        country: str = "CHN",         # ISO3 country code
        indicator: str = "NY.GDP.MKTP.CD",
        date_range: str = "2019:2024",
        per_page: int = 100,
    ) -> DataResult:
        """
        查询世界银行经济指标。

        Args:
            country: ISO3国家代码 (CHN/USA/VNM 等，多国用分号分隔 "CHN;USA;VNM")
            indicator: 指标代码
            date_range: 年份范围 "2019:2024"
            per_page: 每页记录数
        """
        url = f"{self.base_url}/country/{country}/indicator/{indicator}"
        params = {
            "date": date_range,
            "format": "json",
            "per_page": str(per_page),
        }

        query_desc = {
            "country": country,
            "indicator": indicator,
            "date_range": date_range,
        }

        try:
            raw = self._get(url, params=params)
            # World Bank API returns [metadata, data_array]
            if isinstance(raw, list) and len(raw) >= 2:
                meta = raw[0]
                records = raw[1] or []
                return DataResult(
                    source=self.name,
                    query=query_desc,
                    data=records,
                    metadata={"pagination": meta},
                )
            return DataResult(
                source=self.name,
                query=query_desc,
                data=raw,
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data=[],
                error=str(e),
            )

    def compare_countries(
        self,
        countries: list[str],
        indicator: str,
        date_range: str = "2019:2024",
    ) -> DataResult:
        """对比多个国家的同一指标。"""
        country_str = ";".join(countries)
        return self.query(
            country=country_str,
            indicator=indicator,
            date_range=date_range,
        )

    def get_china_trade_overview(self, date_range: str = "2019:2024") -> dict[str, DataResult]:
        """快捷：获取中国贸易相关宏观指标。"""
        indicators = {
            "gdp": self.GDP,
            "exports_pct_gdp": self.EXPORTS_GDP,
            "imports_pct_gdp": self.IMPORTS_GDP,
            "high_tech_exports": self.HIGH_TECH_EXPORTS,
            "manufacturing_va": self.MANUFACTURING_VA,
        }
        results = {}
        for key, ind in indicators.items():
            results[key] = self.query(country="CHN", indicator=ind, date_range=date_range)
        return results
