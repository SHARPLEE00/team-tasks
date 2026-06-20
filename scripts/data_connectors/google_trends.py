"""
Google Trends — 搜索趋势数据
通过 pytrends 库（非官方）获取。

免费，但需安装: pip install pytrends
注意：Google 可能限流，建议使用代理或间隔调用。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class GoogleTrendsConnector(BaseConnector):
    name = "google_trends"
    cost_tier = "free"
    requires_key = False
    base_url = "https://trends.google.com"
    rate_limit_per_min = 5  # Google限流严格

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)
        self._pytrends = None

    def _get_client(self):
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq
                self._pytrends = TrendReq(hl="en-US", tz=480)
            except ImportError:
                raise ImportError(
                    "pytrends not installed. Run: pip install pytrends"
                )
        return self._pytrends

    def query(
        self,
        keywords: list[str] | None = None,
        timeframe: str = "today 12-m",
        geo: str = "",
        category: int = 0,
    ) -> DataResult:
        """
        查询Google搜索趋势。

        Args:
            keywords: 关键词列表 (最多5个)
            timeframe: 时间范围 ("today 12-m", "today 3-m", "2024-01-01 2024-12-31")
            geo: 地区代码 ("US", "VN", "" 全球)
            category: 分类ID (0=全部)
        """
        if keywords is None:
            keywords = ["cross border ecommerce"]

        query_desc = {
            "keywords": keywords,
            "timeframe": timeframe,
            "geo": geo,
        }

        try:
            pt = self._get_client()
            pt.build_payload(
                keywords[:5],
                timeframe=timeframe,
                geo=geo,
                cat=category,
            )
            df = pt.interest_over_time()
            data = df.reset_index().to_dict(orient="records") if not df.empty else []
            return DataResult(
                source=self.name,
                query=query_desc,
                data=data,
                metadata={"rows": len(data)},
            )
        except ImportError as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data=[],
                error=str(e),
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data=[],
                error=f"Google Trends error: {e}",
            )

    def related_queries(self, keyword: str, geo: str = "") -> DataResult:
        """获取相关搜索词。"""
        query_desc = {"keyword": keyword, "geo": geo, "type": "related_queries"}
        try:
            pt = self._get_client()
            pt.build_payload([keyword], geo=geo)
            related = pt.related_queries()
            data = {}
            for kw, tables in related.items():
                data[kw] = {}
                for table_type, df in tables.items():
                    if df is not None and not df.empty:
                        data[kw][table_type] = df.to_dict(orient="records")
            return DataResult(source=self.name, query=query_desc, data=data)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data={}, error=str(e))

    def trending_searches(self, country: str = "united_states") -> DataResult:
        """获取当日热搜。"""
        query_desc = {"country": country, "type": "trending_searches"}
        try:
            pt = self._get_client()
            df = pt.trending_searches(pn=country)
            data = df[0].tolist() if not df.empty else []
            return DataResult(source=self.name, query=query_desc, data=data)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))
