"""
WTO Timeseries API v1 — 世界贸易组织数据
https://apiportal.wto.org/

需注册获取免费 Key（Azure API Management）。
覆盖: 关税/贸易壁垒/贸易统计/服务贸易/数量限制等。

认证: Header `Ocp-Apim-Subscription-Key`
环境变量: WTO_API_KEY

官方 API 端点 (来源: apiportal.wto.org/api-details#api=version1):

  GET  01. Timeseries datapoints    /timeseries/v1/data
  POST 02. Timeseries datapoints    /timeseries/v1/data  (URL长度超限时)
  GET  03. Timeseries data count    /timeseries/v1/data/count
  GET  04. Timeseries metadata      /timeseries/v1/data/metadata
  GET  05. Topics                   /timeseries/v1/topics
  GET  06. Frequencies              /timeseries/v1/frequencies
  GET  07. Periods                  /timeseries/v1/periods
  GET  08. Units                    /timeseries/v1/units
  GET  09. Indicator categories     /timeseries/v1/indicator_categories
  GET  10. Indicators               /timeseries/v1/indicators
  GET  11. Geographical regions     /timeseries/v1/territory/regions
  GET  12. Economic groups          /timeseries/v1/territory/groups
  GET  13. Reporting economies      /timeseries/v1/reporting_economies
  GET  14. Partner economies        /timeseries/v1/partner_economies
  GET  15. Classifications          /timeseries/v1/product_classifications
  GET  16. Products/sectors         /timeseries/v1/products
  GET  17. Years                    /timeseries/v1/years
  GET  18. Value flags              /timeseries/v1/value_flags

  数据端点参数 (01):
    i     (required) Indicator code
    r     Reporting economies (comma separated)
    p     Partner economies (comma separated)
    ps    Time period (YYYY or YYYYQn or YYYYMnn, default=last 8 years)
    pc    Product classification
    spc   Product/sector code
    fmt   json / csv
    mode  full / codes
    dec   Number of decimals
    off   Offset for pagination
    max   Max records (default 500)
    head  Column heading style
    lang  1=English, 2=French, 3=Spanish
    meta  Include metadata (true/false)
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

    # ── 01. 时间序列数据 (核心端点) ──────────────────

    def query(self, endpoint: str = "topics", **params) -> DataResult:
        """通用查询任意端点。"""
        query_desc = {"endpoint": endpoint, **params}
        try:
            raw = self._api_get(endpoint, params=params if params else None)
            data = raw if isinstance(raw, list) else raw.get("Dataset", raw)
            return DataResult(source=self.name, query=query_desc, data=data)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_data(
        self,
        indicator_code: str = "HS_M_0010",
        reporting_economy: str | None = "156",
        partner_economy: str | None = None,
        time_period: str | None = None,
        product_classification: str | None = None,
        product_sector: str | None = None,
        fmt: str = "json",
        mode: str = "full",
        max_records: int = 500,
        offset: int | None = None,
        decimals: int | None = None,
        include_metadata: bool = False,
        lang: int = 1,
    ) -> DataResult:
        """
        获取时间序列数据点 (端点 01)。

        官方 URL: GET /timeseries/v1/data?i=...&r=...&p=...&ps=...

        Args:
            indicator_code (i): 指标代码 (必填, 如 HS_M_0010)
            reporting_economy (r): 报告经济体 (逗号分隔, 如 "156" 或 "156,842")
            partner_economy (p): 贸易伙伴 (逗号分隔, 可选)
            time_period (ps): 时间 (YYYY/YYYYQn/YYYYMnn, 默认最近8年)
            product_classification (pc): 产品分类
            product_sector (spc): 产品/部门代码
            fmt: json / csv
            mode: full / codes
            max_records (max): 最大记录数
            offset (off): 分页偏移
            decimals (dec): 小数位数
            include_metadata (meta): 是否包含元数据
            lang: 1=English, 2=French, 3=Spanish
        """
        params = {
            "i": indicator_code,
            "fmt": fmt,
            "mode": mode,
            "max": str(max_records),
            "lang": str(lang),
        }
        if reporting_economy:
            params["r"] = reporting_economy
        if partner_economy:
            params["p"] = partner_economy
        if time_period:
            params["ps"] = time_period
        if product_classification:
            params["pc"] = product_classification
        if product_sector:
            params["spc"] = product_sector
        if offset is not None:
            params["off"] = str(offset)
        if decimals is not None:
            params["dec"] = str(decimals)
        if include_metadata:
            params["meta"] = "true"

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

    # ── 03. 数据记录计数 ────────────────────────────

    def get_data_count(
        self,
        indicator_code: str = "HS_M_0010",
        reporting_economy: str | None = "156",
        partner_economy: str | None = None,
        time_period: str | None = None,
    ) -> DataResult:
        """获取查询结果记录数（不返回数据）。"""
        params = {"i": indicator_code}
        if reporting_economy:
            params["r"] = reporting_economy
        if partner_economy:
            params["p"] = partner_economy
        if time_period:
            params["ps"] = time_period
        return self.query("data/count", **params)

    # ── 04. 元数据 ──────────────────────────────────

    def get_metadata(
        self,
        indicator_code: str = "HS_M_0010",
        reporting_economy: str | None = "156",
        lang: int = 1,
    ) -> DataResult:
        """获取数据的元数据信息。"""
        params = {"i": indicator_code, "lang": str(lang)}
        if reporting_economy:
            params["r"] = reporting_economy
        return self.query("data/metadata", **params)

    # ── 05-18. 参考数据端点 ─────────────────────────

    def get_topics(self, lang: int = 1) -> DataResult:
        """05. 获取指标主题分类。"""
        return self.query("topics", lang=str(lang))

    def get_frequencies(self, lang: int = 1) -> DataResult:
        """06. 获取数据频率列表 (月度/季度/年度)。"""
        return self.query("frequencies", lang=str(lang))

    def get_periods(self, lang: int = 1) -> DataResult:
        """07. 获取可用时间段。"""
        return self.query("periods", lang=str(lang))

    def get_units(self, lang: int = 1) -> DataResult:
        """08. 获取计量单位。"""
        return self.query("units", lang=str(lang))

    def get_indicator_categories(self, lang: int = 1) -> DataResult:
        """09. 获取指标分类。"""
        return self.query("indicator_categories", lang=str(lang))

    def get_indicators(self, topic_id: str | None = None, lang: int = 1) -> DataResult:
        """
        10. 获取可用指标列表。

        Args:
            topic_id: 主题ID（可选）
            lang: 1=English, 2=French, 3=Spanish
        """
        params = {"lang": str(lang)}
        if topic_id:
            params["t"] = topic_id
        return self.query("indicators", **params)

    def get_geographical_regions(self, lang: int = 1) -> DataResult:
        """11. 获取地理区域列表。"""
        return self.query("territory/regions", lang=str(lang))

    def get_economic_groups(self, lang: int = 1) -> DataResult:
        """12. 获取经济体分组。"""
        return self.query("territory/groups", lang=str(lang))

    def get_reporting_economies(self, lang: int = 1) -> DataResult:
        """13. 获取报告经济体列表。"""
        return self.query("reporting_economies", lang=str(lang))

    def get_partner_economies(self, lang: int = 1) -> DataResult:
        """14. 获取贸易伙伴列表。"""
        return self.query("partner_economies", lang=str(lang))

    def get_product_classifications(self, lang: int = 1) -> DataResult:
        """15. 获取产品分类标准列表。"""
        return self.query("product_classifications", lang=str(lang))

    def get_products(self, pc: str = "HS", lang: int = 1) -> DataResult:
        """
        16. 获取产品/部门列表。

        Args:
            pc: 分类标准 (HS/SITC/BEC等)
        """
        return self.query("products", pc=pc, lang=str(lang))

    def get_years(self, lang: int = 1) -> DataResult:
        """17. 获取可用年份列表。"""
        return self.query("years", lang=str(lang))

    def get_value_flags(self, lang: int = 1) -> DataResult:
        """18. 获取数据质量标记。"""
        return self.query("value_flags", lang=str(lang))

    # ── QR (数量限制) API ──────────────────────────

    def get_qr_notifications(
        self,
        member_code: str | None = None,
        product: str | None = None,
    ) -> DataResult:
        """获取数量限制通知。"""
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

    # ── 常用指标代码 ────────────────────────────────

    IND_MERCHANDISE_IMPORTS = "HS_M_0010"      # 商品进口额
    IND_MERCHANDISE_EXPORTS = "HS_M_0020"      # 商品出口额
    IND_TARIFF_APPLIED_SIMPLE = "HS_A_0010"    # 简单平均适用关税
    IND_TARIFF_MFN_SIMPLE = "HS_M_0050"        # MFN简单平均关税
    IND_SERVICES_IMPORTS = "S_M_0010"          # 服务进口
    IND_SERVICES_EXPORTS = "S_M_0020"          # 服务出口

    # ── 快捷方法 ────────────────────────────────────

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
