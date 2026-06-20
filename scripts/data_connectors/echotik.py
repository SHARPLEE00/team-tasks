"""
EchoTik API — TikTok Shop 数据
https://echotik.live/zh/api-service

低成本层: $9.9/月起，有免费版。API 低延迟实时数据。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class EchoTikConnector(BaseConnector):
    name = "echotik"
    cost_tier = "low_cost"
    requires_key = True
    base_url = "https://api.echotik.live"
    rate_limit_per_min = 30

    def query(
        self,
        endpoint: str = "/api/v1/products/trending",
        region: str = "US",
        category: str | None = None,
        limit: int = 20,
    ) -> DataResult:
        """
        查询TikTok Shop数据。

        Args:
            endpoint: API端点
            region: 地区 (US/VN/TH/PH/MY/SG/GB/ES/MX)
            category: 品类筛选
            limit: 返回数量
        """
        url = f"{self.base_url}{endpoint}"
        params = {"region": region, "limit": str(limit)}
        if category:
            params["category"] = category

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        query_desc = {
            "endpoint": endpoint,
            "region": region,
            "category": category,
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

    def trending_products(self, region: str = "US", category: str | None = None) -> DataResult:
        """获取TikTok Shop热销产品。"""
        return self.query(
            endpoint="/api/v1/products/trending",
            region=region,
            category=category,
        )

    def creator_search(self, keyword: str, region: str = "US") -> DataResult:
        """搜索TikTok创作者/达人。"""
        return self.query(
            endpoint="/api/v1/creators/search",
            region=region,
            category=keyword,
        )
