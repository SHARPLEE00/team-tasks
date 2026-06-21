"""
Alpha Vantage API — 股票/外汇/大宗商品/加密货币/经济指标
https://www.alphavantage.co/documentation/

免费层: 25次/天, 需注册Key。
覆盖: 个股行情/技术指标/外汇/大宗商品(石油/铜/铝/小麦等)/加密货币/美国经济指标

环境变量: ALPHA_VANTAGE_KEY

补齐大宗商品+金融股票调研的最大缺口。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class AlphaVantageConnector(BaseConnector):
    name = "alpha_vantage"
    cost_tier = "free"
    requires_key = True
    base_url = "https://www.alphavantage.co/query"
    rate_limit_per_min = 5  # 免费版 25次/天，保守限速

    def _params(self, **kwargs) -> dict:
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage requires an API key. "
                "Get one free at https://www.alphavantage.co/support/#api-key"
            )
        params = {"apikey": self.api_key}
        params.update(kwargs)
        return params

    def query(self, function: str = "TIME_SERIES_DAILY", **kwargs) -> DataResult:
        """通用查询。"""
        query_desc = {"function": function, **kwargs}
        try:
            params = self._params(function=function, **kwargs)
            raw = self._get(self.base_url, params=params)
            if "Error Message" in raw:
                return DataResult(source=self.name, query=query_desc, data={},
                                  error=raw["Error Message"])
            if "Note" in raw:
                return DataResult(source=self.name, query=query_desc, data={},
                                  error=f"Rate limited: {raw['Note'][:100]}")
            return DataResult(source=self.name, query=query_desc, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data={}, error=str(e))

    # ── 股票行情 ────────────────────────────────────

    def stock_daily(self, symbol: str = "AAPL", outputsize: str = "compact") -> DataResult:
        """
        个股日线行情。

        Args:
            symbol: 股票代码 (如 AAPL, MSFT, BABA, JD)
            outputsize: compact=最近100天, full=20年+
        """
        return self.query("TIME_SERIES_DAILY", symbol=symbol, outputsize=outputsize)

    def stock_weekly(self, symbol: str = "AAPL") -> DataResult:
        """个股周线行情。"""
        return self.query("TIME_SERIES_WEEKLY", symbol=symbol)

    def stock_monthly(self, symbol: str = "AAPL") -> DataResult:
        """个股月线行情。"""
        return self.query("TIME_SERIES_MONTHLY", symbol=symbol)

    def stock_quote(self, symbol: str = "AAPL") -> DataResult:
        """个股实时报价（最新价/涨跌/成交量）。"""
        return self.query("GLOBAL_QUOTE", symbol=symbol)

    def stock_search(self, keywords: str = "solar") -> DataResult:
        """搜索股票/ETF代码。"""
        return self.query("SYMBOL_SEARCH", keywords=keywords)

    def stock_overview(self, symbol: str = "AAPL") -> DataResult:
        """公司基本面概览（市值/PE/EPS/营收/利润等）。"""
        return self.query("OVERVIEW", symbol=symbol)

    # ── 外汇 ────────────────────────────────────────

    def fx_rate(self, from_currency: str = "USD", to_currency: str = "CNY") -> DataResult:
        """实时汇率。"""
        return self.query("CURRENCY_EXCHANGE_RATE",
                          from_currency=from_currency, to_currency=to_currency)

    def fx_daily(self, from_symbol: str = "USD", to_symbol: str = "CNY",
                 outputsize: str = "compact") -> DataResult:
        """外汇日线历史。"""
        return self.query("FX_DAILY",
                          from_symbol=from_symbol, to_symbol=to_symbol,
                          outputsize=outputsize)

    # ── 大宗商品 ────────────────────────────────────

    def commodity_wti(self, interval: str = "monthly") -> DataResult:
        """WTI原油价格。interval: daily/weekly/monthly"""
        return self.query("WTI", interval=interval)

    def commodity_brent(self, interval: str = "monthly") -> DataResult:
        """布伦特原油价格。"""
        return self.query("BRENT", interval=interval)

    def commodity_natural_gas(self, interval: str = "monthly") -> DataResult:
        """天然气价格。"""
        return self.query("NATURAL_GAS", interval=interval)

    def commodity_copper(self, interval: str = "monthly") -> DataResult:
        """铜价。"""
        return self.query("COPPER", interval=interval)

    def commodity_aluminum(self, interval: str = "monthly") -> DataResult:
        """铝价。"""
        return self.query("ALUMINUM", interval=interval)

    def commodity_wheat(self, interval: str = "monthly") -> DataResult:
        """小麦价格。"""
        return self.query("WHEAT", interval=interval)

    def commodity_corn(self, interval: str = "monthly") -> DataResult:
        """玉米价格。"""
        return self.query("CORN", interval=interval)

    def commodity_cotton(self, interval: str = "monthly") -> DataResult:
        """棉花价格。"""
        return self.query("COTTON", interval=interval)

    def commodity_sugar(self, interval: str = "monthly") -> DataResult:
        """糖价格。"""
        return self.query("SUGAR", interval=interval)

    def commodity_coffee(self, interval: str = "monthly") -> DataResult:
        """咖啡价格。"""
        return self.query("COFFEE", interval=interval)

    def commodity_all_index(self, interval: str = "monthly") -> DataResult:
        """全球大宗商品指数 (IMF)。"""
        return self.query("ALL_COMMODITIES", interval=interval)

    # ── 经济指标 ────────────────────────────────────

    def econ_gdp(self, interval: str = "annual") -> DataResult:
        """美国实际GDP。interval: quarterly/annual"""
        return self.query("REAL_GDP", interval=interval)

    def econ_gdp_per_capita(self) -> DataResult:
        """美国人均实际GDP。"""
        return self.query("REAL_GDP_PER_CAPITA")

    def econ_cpi(self, interval: str = "monthly") -> DataResult:
        """美国CPI。"""
        return self.query("CPI", interval=interval)

    def econ_inflation(self) -> DataResult:
        """美国通胀率。"""
        return self.query("INFLATION")

    def econ_fed_funds_rate(self, interval: str = "monthly") -> DataResult:
        """联邦基金利率。"""
        return self.query("FEDERAL_FUNDS_RATE", interval=interval)

    def econ_treasury_yield(self, interval: str = "monthly", maturity: str = "10year") -> DataResult:
        """美国国债收益率。maturity: 3month/2year/5year/7year/10year/30year"""
        return self.query("TREASURY_YIELD", interval=interval, maturity=maturity)

    def econ_unemployment(self) -> DataResult:
        """美国失业率。"""
        return self.query("UNEMPLOYMENT")

    def econ_nonfarm_payroll(self) -> DataResult:
        """美国非农就业。"""
        return self.query("NONFARM_PAYROLL")

    def econ_retail_sales(self) -> DataResult:
        """美国零售销售。"""
        return self.query("RETAIL_SALES")

    # ── 加密货币 ────────────────────────────────────

    def crypto_rate(self, from_currency: str = "BTC", to_currency: str = "USD") -> DataResult:
        """加密货币实时汇率。"""
        return self.query("CURRENCY_EXCHANGE_RATE",
                          from_currency=from_currency, to_currency=to_currency)

    def crypto_daily(self, symbol: str = "BTC", market: str = "USD") -> DataResult:
        """加密货币日线。"""
        return self.query("DIGITAL_CURRENCY_DAILY", symbol=symbol, market=market)
