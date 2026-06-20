"""
OECD Data API — OECD国家经济/贸易数据
https://data-explorer.oecd.org/

完全免费，无需 API Key。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class OECDConnector(BaseConnector):
    name = "oecd"
    cost_tier = "free"
    requires_key = False
    base_url = "https://sdmx.oecd.org/public/rest/data"
    rate_limit_per_min = 20

    # 常用数据集
    TRADE_IN_GOODS = "MEI_TRD"              # 月度贸易指标
    BILATERAL_TRADE = "BATIS"               # 双边贸易服务
    INDUSTRY_PRODUCTION = "MEI_REAL"        # 工业生产
    CONSUMER_PRICES = "PRICES_CPI"          # 消费者价格指数

    def query(
        self,
        dataset: str = "MEI_TRD",
        filter_expression: str = "",
        start_period: str = "2023-01",
        end_period: str = "2024-12",
    ) -> DataResult:
        """
        查询OECD数据。

        Args:
            dataset: 数据集ID
            filter_expression: SDMX filter (如 "CHN+USA.XTEXVA01.CXMLSA.M")
            start_period: 起始期间
            end_period: 结束期间
        """
        url = f"{self.base_url}/{dataset}/{filter_expression}"
        params = {
            "startPeriod": start_period,
            "endPeriod": end_period,
            "dimensionAtObservation": "AllDimensions",
        }
        headers = {"Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd"}

        query_desc = {
            "dataset": dataset,
            "filter": filter_expression,
            "start_period": start_period,
            "end_period": end_period,
        }

        try:
            raw = self._get(url, params=params, headers=headers)
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
