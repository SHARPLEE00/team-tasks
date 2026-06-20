"""
China Data Portal — 中国海关月度进出口数据
https://chinadata.live/

完全免费，无需 API Key。2018-2026 月度数据。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class ChinaDataPortalConnector(BaseConnector):
    name = "china_data_portal"
    cost_tier = "free"
    requires_key = False
    base_url = "https://chinadata.live/api"
    rate_limit_per_min = 30

    def query(
        self,
        endpoint: str = "trade",
        hs_code: str | None = None,
        year: str | None = None,
        month: str | None = None,
        partner: str | None = None,
    ) -> DataResult:
        """
        查询中国海关数据。

        Args:
            endpoint: API端点 (trade / indicators 等)
            hs_code: HS编码
            year: 年份
            month: 月份
            partner: 贸易伙伴国
        """
        url = f"{self.base_url}/{endpoint}"
        params = {}
        if hs_code:
            params["hs_code"] = hs_code
        if year:
            params["year"] = year
        if month:
            params["month"] = month
        if partner:
            params["partner"] = partner

        query_desc = {
            "endpoint": endpoint,
            "hs_code": hs_code,
            "year": year,
            "month": month,
            "partner": partner,
        }

        try:
            raw = self._get(url, params=params if params else None)
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
