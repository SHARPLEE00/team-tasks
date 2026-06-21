"""
WTO Timeseries API v1 — 世界贸易组织数据
https://apiportal.wto.org/

需注册获取免费 Key（Azure API Management）。
覆盖: 关税/贸易壁垒/贸易统计/服务贸易/数量限制等。

认证: Header `Ocp-Apim-Subscription-Key`
环境变量: WTO_API_KEY

API 端点 (从 wtor R库源码和 wto PyPI包逆向):
  Timeseries:
    /timeseries/v1/topics
    /timeseries/v1/indicators
    /timeseries/v1/indicator_categories
    /timeseries/v1/reporters (via territory)
    /timeseries/v1/partners (via territory)
    /timeseries/v1/products
    /timeseries/v1/product_classifications
    /timeseries/v1/frequencies
    /timeseries/v1/periods
    /timeseries/v1/units
    /timeseries/v1/years
    /timeseries/v1/value_flags
    /timeseries/v1/territory/regions
    /timeseries/v1/territory/groups
    /timeseries/v1/data (主要数据端点)
    /timeseries/v1/data/count
    /timeseries/v1/data/metadata
  QR (Quantitative Restrictions):
    /qrs/qrs
    /qrs/members
    /qrs/notifications
    /qrs/products
    /qrs/hs-versions
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class WTOConnector(BaseConnector):
    name = "wto"
    cost_tier = "free"       # 免费注册
    requires_key = True
    base_url = "https://api.wto.org/timeseries/v1"
    rate_limit_per_min = 30

    def _auth_header(self) -> dict:
        if not self.api_key:
            raise ValueError(
                "WTO API requires a subscription key. "
                "Register free at https://apiportal.wto.org/"
            )
        return {"Ocp-Apim-Subscription-Key": self.api_key}

    def _api_get(self, endpoint: str, params: dict | None = None) -> list | dict:
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith("http") else endpoint
        return self._get(url, params=params, headers=self._auth_header())

    # ── 参考数据 (Reference) ────────────────────────

    def query(self, endpoint: str = "topics", **params) -> DataResult:
        """通用查询任意端点。"""
        query_desc = {"endpoint": endpoint, **params}
        try:
            raw = self._api_get(endpoint, params=params if params else None)
            data = raw if isinstance(raw, list) else raw.get("Dataset", raw)
            return DataResult(source=self.name, query=query_desc, data=data)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_topics(self, lang: int = 1) -> DataResult:
        """获取指标主题分类。"""
        return self.query("topics", lang=str(lang))

    def get_indicators(self, topic_id: str | None = None, lang: int = 1) -> DataResult:
        """
        获取可用指标列表。

        Args:
            topic_id: 主题ID（可选，筛选特定主题下的指标）
            lang: 1=English, 2=French, 3=Spanish
        """
        params = {"lang": str(lang)}
        if topic_id:
            params["t"] = topic_id
        return self.query("indicators", **params)

    def get_reporters(self, lang: int = 1) -> DataResult:
        """获取报告经济体列表。"""
        return self.query("territory/regions", lang=str(lang))

    def get_product_classifications(self, lang: int = 1) -> DataResult:
        """获取产品分类列表。"""
        return self.query("product_classifications", lang=str(lang))

    def get_products(self, pc: str = "HS", lang: int = 1) -> DataResult:
        """
        获取产品/部门列表。

        Args:
            pc: 分类标准 (HS/SITC/BEC等)
        """
        return self.query("products", pc=pc, lang=str(lang))

    def get_frequencies(self, lang: int = 1) -> DataResult:
        """获取数据频率列表 (月度/季度/年度)。"""
        return self.query("frequencies", lang=str(lang))

    def get_years(self, lang: int = 1) -> DataResult:
        """获取可用年份列表。"""
        return self.query("years", lang=str(lang))

    # ── 时间序列数据 ────────────────────────────────

    def get_data(
        self,
        indicator_code: str = "HS_M_0010",
        reporting_economy: str = "156",
        partner_economy: str | None = None,
        product_sector: str | None = None,
        time_period: str | None = None,
        freq: str = "A",
        max_records: int = 500,
        lang: int = 1,
    ) -> DataResult:
        """
        获取时间序列数据点。

        Args:
            indicator_code: 指标代码 (如 HS_M_0010=商品进口额)
            reporting_economy: 报告经济体代码 (156=中国)
            partner_economy: 贸易伙伴 (可选)
            product_sector: 产品/部门 (可选)
            time_period: 时间 (如 "2023")
            freq: A=年度, Q=季度, M=月度
            max_records: 最大记录数
            lang: 1=English
        """
        params = {
            "i": indicator_code,
            "r": reporting_economy,
            "fmt": "json",
            "mode": "full",
            "lang": str(lang),
            "max": str(max_records),
        }
        if partner_economy:
            params["p"] = partner_economy
        if product_sector:
            params["ps"] = product_sector
        if time_period:
            params["tp"] = time_period
        if freq:
            params["frq"] = freq

        query_desc = {
            "indicator": indicator_code,
            "reporter": reporting_economy,
            "partner": partner_economy,
            "period": time_period,
        }

        try:
            raw = self._api_get("data", params=params)
            data = raw.get("Dataset", raw) if isinstance(raw, dict) else raw
            return DataResult(
                source=self.name,
                query=query_desc,
                data=data,
                metadata={"total": len(data) if isinstance(data, list) else 0},
            )
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_data_count(
        self,
        indicator_code: str = "HS_M_0010",
        reporting_economy: str = "156",
        partner_economy: str | None = None,
        time_period: str | None = None,
    ) -> DataResult:
        """获取查询结果记录数（不返回数据）。"""
        params = {
            "i": indicator_code,
            "r": reporting_economy,
        }
        if partner_economy:
            params["p"] = partner_economy
        if time_period:
            params["tp"] = time_period
        return self.query("data/count", **params)

    # ── QR (数量限制) API ──────────────────────────

    def get_qr_notifications(
        self,
        member_code: str | None = None,
        product: str | None = None,
    ) -> DataResult:
        """
        获取数量限制通知。

        Args:
            member_code: WTO成员代码
            product: HS编码
        """
        params = {}
        if member_code:
            params["member_code"] = member_code
        if product:
            params["product"] = product

        url = "https://api.wto.org/qrs/notifications"
        try:
            raw = self._get(url, params=params if params else None, headers=self._auth_header())
            data = raw if isinstance(raw, list) else raw.get("data", raw)
            return DataResult(
                source=self.name,
                query={"action": "qr_notifications", **params},
                data=data,
            )
        except Exception as e:
            return DataResult(source=self.name, query=params, data=[], error=str(e))

    def get_qr_members(self, member_code: str | None = None) -> DataResult:
        """获取WTO成员列表。"""
        url = "https://api.wto.org/qrs/members"
        params = {}
        if member_code:
            params["member_code"] = member_code
        try:
            raw = self._get(url, params=params if params else None, headers=self._auth_header())
            return DataResult(source=self.name, query={"action": "qr_members"}, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query={}, data=[], error=str(e))

    # ── 快捷方法 ────────────────────────────────────

    # 常用指标代码
    IND_MERCHANDISE_IMPORTS = "HS_M_0010"      # 商品进口额
    IND_MERCHANDISE_EXPORTS = "HS_M_0020"      # 商品出口额
    IND_TARIFF_APPLIED_SIMPLE = "HS_A_0010"    # 简单平均适用关税
    IND_TARIFF_MFN_SIMPLE = "HS_M_0050"        # MFN简单平均关税
    IND_SERVICES_IMPORTS = "S_M_0010"          # 服务进口
    IND_SERVICES_EXPORTS = "S_M_0020"          # 服务出口

    def get_china_trade(self, indicator: str = "HS_M_0020", year: str | None = None) -> DataResult:
        """快捷：查中国贸易数据。"""
        return self.get_data(indicator_code=indicator, reporting_economy="156", time_period=year)

    def get_tariffs(self, reporter: str = "156", product: str | None = None, year: str | None = None) -> DataResult:
        """快捷：查关税数据。"""
        return self.get_data(
            indicator_code=self.IND_TARIFF_APPLIED_SIMPLE,
            reporting_economy=reporter,
            product_sector=product,
            time_period=year,
        )
