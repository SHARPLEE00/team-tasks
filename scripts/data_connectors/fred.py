"""
FRED API — 美联储经济数据 (Federal Reserve Economic Data)
https://fred.stlouisfed.org/docs/api/fred/

免费，需注册获取 Key（无调用上限）。
覆盖 816,000+ 经济时间序列：利率/CPI/GDP/就业/通胀/汇率等。

环境变量: FRED_API_KEY
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class FREDConnector(BaseConnector):
    name = "fred"
    cost_tier = "free"
    requires_key = True
    base_url = "https://api.stlouisfed.org/fred"
    rate_limit_per_min = 120

    # ── 常用经济指标 Series ID ────────────────────────

    # 利率
    FED_FUNDS_RATE = "FEDFUNDS"              # 联邦基金利率
    TREASURY_10Y = "DGS10"                   # 10年期国债收益率
    TREASURY_2Y = "DGS2"                     # 2年期国债收益率

    # 通胀/物价
    CPI_ALL = "CPIAUCSL"                     # 消费者价格指数(CPI)
    CPI_CORE = "CPILFESL"                    # 核心CPI(不含食品能源)
    PCE = "PCEPI"                            # 个人消费支出价格指数
    PPI = "PPIACO"                           # 生产者价格指数

    # GDP
    GDP_US = "GDP"                           # 美国GDP
    GDP_REAL = "GDPC1"                       # 美国实际GDP
    GDP_GROWTH = "A191RL1Q225SBEA"           # GDP增速(季度年化)

    # 就业
    UNEMPLOYMENT = "UNRATE"                  # 失业率
    NONFARM_PAYROLL = "PAYEMS"               # 非农就业人数
    INITIAL_CLAIMS = "ICSA"                  # 首次申领失业金人数

    # 贸易
    TRADE_BALANCE = "BOPGSTB"               # 贸易差额
    EXPORTS = "BOPGEXP"                      # 商品出口
    IMPORTS = "BOPGIMP"                      # 商品进口

    # 汇率
    USD_CNY = "DEXCHUS"                      # 美元/人民币
    USD_EUR = "DEXUSEU"                      # 美元/欧元
    USD_JPY = "DEXJPUS"                      # 日元/美元

    # 消费
    RETAIL_SALES = "RSAFS"                   # 零售销售额
    CONSUMER_SENTIMENT = "UMCSENT"           # 密歇根消费者信心

    # 房地产
    HOUSING_STARTS = "HOUST"                 # 新屋开工
    CASE_SHILLER = "CSUSHPISA"              # Case-Shiller房价指数

    # ── API 方法 ──────────────────────────────────────

    def _params(self, **kwargs) -> dict:
        """Add API key and default format."""
        params = {"api_key": self.api_key, "file_type": "json"}
        params.update(kwargs)
        return params

    def query(
        self,
        series_id: str = "FEDFUNDS",
        observation_start: str | None = None,
        observation_end: str | None = None,
        limit: int = 100,
        sort_order: str = "desc",
    ) -> DataResult:
        """
        获取经济指标的观测数据。

        Args:
            series_id: 指标ID (如 FEDFUNDS, CPIAUCSL, GDP 等)
            observation_start: 开始日期 "2024-01-01"
            observation_end: 结束日期
            limit: 返回条数
            sort_order: "desc" 最新在前, "asc" 最早在前
        """
        url = f"{self.base_url}/series/observations"
        params = self._params(
            series_id=series_id,
            limit=str(limit),
            sort_order=sort_order,
        )
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        query_desc = {"series_id": series_id, "start": observation_start, "end": observation_end}

        try:
            raw = self._get(url, params=params)
            observations = raw.get("observations", [])
            return DataResult(
                source=self.name,
                query=query_desc,
                data=observations,
                metadata={
                    "count": raw.get("count", len(observations)),
                    "realtime_start": raw.get("realtime_start"),
                    "realtime_end": raw.get("realtime_end"),
                },
            )
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def series_info(self, series_id: str) -> DataResult:
        """获取指标的元数据（标题/频率/单位/来源等）。"""
        url = f"{self.base_url}/series"
        params = self._params(series_id=series_id)
        try:
            raw = self._get(url, params=params)
            serieses = raw.get("seriess", [])
            return DataResult(
                source=self.name,
                query={"action": "series_info", "series_id": series_id},
                data=serieses[0] if serieses else {},
            )
        except Exception as e:
            return DataResult(source=self.name, query={"series_id": series_id}, data={}, error=str(e))

    def search(self, search_text: str, limit: int = 20) -> DataResult:
        """
        搜索经济指标。

        Args:
            search_text: 搜索关键词 (如 "china trade", "inflation", "GDP")
            limit: 返回条数
        """
        url = f"{self.base_url}/series/search"
        params = self._params(search_text=search_text, limit=str(limit))
        try:
            raw = self._get(url, params=params)
            serieses = raw.get("seriess", [])
            return DataResult(
                source=self.name,
                query={"action": "search", "keyword": search_text},
                data=serieses,
                metadata={"count": raw.get("count", len(serieses))},
            )
        except Exception as e:
            return DataResult(source=self.name, query={"keyword": search_text}, data=[], error=str(e))

    # ── 快捷方法 ──────────────────────────────────────

    def get_fed_rate(self, limit: int = 12) -> DataResult:
        """获取联邦基金利率。"""
        return self.query(self.FED_FUNDS_RATE, limit=limit)

    def get_cpi(self, limit: int = 12) -> DataResult:
        """获取消费者价格指数(CPI)。"""
        return self.query(self.CPI_ALL, limit=limit)

    def get_unemployment(self, limit: int = 12) -> DataResult:
        """获取美国失业率。"""
        return self.query(self.UNEMPLOYMENT, limit=limit)

    def get_gdp(self, limit: int = 12) -> DataResult:
        """获取美国GDP。"""
        return self.query(self.GDP_US, limit=limit)

    def get_trade_balance(self, limit: int = 12) -> DataResult:
        """获取美国贸易差额。"""
        return self.query(self.TRADE_BALANCE, limit=limit)

    def get_usd_cny(self, limit: int = 30) -> DataResult:
        """获取美元/人民币汇率。"""
        return self.query(self.USD_CNY, limit=limit)

    def get_retail_sales(self, limit: int = 12) -> DataResult:
        """获取美国零售销售额。"""
        return self.query(self.RETAIL_SALES, limit=limit)

    def get_consumer_sentiment(self, limit: int = 12) -> DataResult:
        """获取消费者信心指数。"""
        return self.query(self.CONSUMER_SENTIMENT, limit=limit)
