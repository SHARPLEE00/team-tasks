"""
DataForSEO Merchant API — 电商产品/SERP数据
https://dataforseo.com/apis/merchant-api

低成本层: $0.001/次 (标准队列), $50 最低充值, 无月费。
需要 API Key (login + password)。
"""

from __future__ import annotations
import base64
from .base import BaseConnector, DataResult


class DataForSEOConnector(BaseConnector):
    name = "dataforseo"
    cost_tier = "low_cost"
    requires_key = True
    base_url = "https://api.dataforseo.com/v3"
    rate_limit_per_min = 60

    def __init__(self, api_key: str | None = None, password: str | None = None):
        """
        Args:
            api_key: DataForSEO login email
            password: DataForSEO password
        """
        super().__init__(api_key)
        self.password = password

    def _auth_header(self) -> dict:
        if not self.api_key or not self.password:
            raise ValueError(
                "DataForSEO requires api_key (login) and password. "
                "Sign up at https://dataforseo.com/"
            )
        creds = base64.b64encode(
            f"{self.api_key}:{self.password}".encode()
        ).decode()
        return {"Authorization": f"Basic {creds}"}

    def query(
        self,
        keyword: str = "solar camera",
        location_code: int = 2840,  # US
        language_code: str = "en",
        search_engine: str = "google",
        depth: int = 20,
    ) -> DataResult:
        """
        搜索产品数据。

        Args:
            keyword: 搜索关键词
            location_code: 地区代码 (2840=US, 2704=Vietnam, 2156=China)
            language_code: 语言代码
            search_engine: 搜索引擎 (google/amazon)
            depth: 返回结果数
        """
        query_desc = {
            "keyword": keyword,
            "location_code": location_code,
            "search_engine": search_engine,
        }

        try:
            url = f"{self.base_url}/merchant/{search_engine}/products/task_post"
            payload = [
                {
                    "keyword": keyword,
                    "location_code": location_code,
                    "language_code": language_code,
                    "depth": depth,
                }
            ]
            raw = self._post(url, payload, headers=self._auth_header())
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

    def serp_search(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        depth: int = 10,
    ) -> DataResult:
        """Google SERP 搜索结果。"""
        query_desc = {"keyword": keyword, "type": "serp", "location": location_code}
        try:
            url = f"{self.base_url}/serp/google/organic/live/advanced"
            payload = [
                {
                    "keyword": keyword,
                    "location_code": location_code,
                    "language_code": language_code,
                    "depth": depth,
                }
            ]
            raw = self._post(url, payload, headers=self._auth_header())
            return DataResult(source=self.name, query=query_desc, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))
