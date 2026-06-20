"""
China Data Portal API v2 — 中国海关/经济/制造业数据
https://chinadata.live/api/docs/

完全免费，无需 API Key，无需注册。
建议请求频率 < 100次/分钟。
覆盖 118+ 数据集：贸易、GDP、制造业、能源、科技等。

API v2 端点:
  GET /api/v2/datasets           — 列出所有数据集(元数据)
  GET /api/v2/data/:dataset_id   — 获取指定数据集的完整数据
  GET /api/v2/search?q=keyword   — 全文搜索数据集

来源: https://chinadata.live/api/docs/
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class ChinaDataPortalConnector(BaseConnector):
    name = "china_data_portal"
    cost_tier = "free"
    requires_key = False
    base_url = "https://chinadata.live/api/v2"
    rate_limit_per_min = 60

    # ── 出海调研高频数据集 slug ──────────────────────────

    # 贸易类
    TRADE_MONTHLY = "china-trade-monthly"                    # 月度进出口总额 (USD Million)
    TRADE_TOP_PARTNERS = "china-trade-top-partners"          # 主要贸易伙伴 (ASEAN/USA/EU)
    TRADE_AFRICA = "china-africa-trade"                      # 中非贸易
    TRADE_JAPAN = "china-japan-trade"                         # 中日贸易
    TRADE_KOREAS = "china-koreas-trade"                      # 中韩/朝贸易
    TRADE_CUBA = "china-cuba-trade"                           # 中古贸易
    TRADE_USA = "trade-volume-comparison"                     # 中美贸易额
    TRADE_BRAZIL = "china-usa-brazil-trade"                   # 中美巴贸易

    # 制造业类 (与出海品类直接相关)
    MFG_AIR_CONDITIONERS = "air-conditioners-production-china-vs-world"  # 空调产量
    MFG_WASHING_MACHINES = "washing-machines-production-china-vs-world"  # 洗衣机产量
    MFG_SMARTPHONES = "smartphone-production-china-vs-world"             # 智能手机产量
    MFG_SEMICONDUCTORS = "semiconductor-manufacturing-china-vs-world"    # 半导体制造
    MFG_SOLAR_PANELS = "solar-panel-manufacturing-china-vs-world"        # 太阳能板制造
    MFG_BATTERIES = "battery-production-china-vs-world"                  # 电池产量
    MFG_LED = "led-production-china-vs-world"                            # LED产量
    MFG_TEXTILES = "textile-production-china-vs-world"                   # 纺织品产量
    MFG_FOOTWEAR = "footwear-production-china-vs-world"                  # 鞋类产量
    MFG_FURNITURE = "furniture-production-china-vs-world"                # 家具产量
    MFG_TOYS = "toys-production-china-vs-world"                          # 玩具产量
    MFG_STEEL = "steel-production-china-vs-world"                        # 钢铁产量
    MFG_GLASS = "glass-production-china-vs-world"                        # 玻璃产量

    # 汽车类
    AUTO_EXPORTS_REGION = "china-vehicle-exports-by-region"   # 汽车出口(按地区)
    AUTO_PRODUCTION = "automobile-production-china-vs-world"   # 汽车产量
    AUTO_PRODUCTION_MONTHLY = "china-car-production-monthly"   # 月度汽车产量
    AUTO_EXPORTS_VS_JAPAN = "car-exports-china-japan"          # 中日汽车出口对比
    AUTO_EV_SALES = "ev-sales-china-vs-world"                  # 新能源车销量
    AUTO_NEV_SALES = "china-nev-sales"                         # 中国NEV销量

    # 宏观经济
    GDP = "china-gdp"
    GDP_USD = "china-gdp-usd"
    GDP_GROWTH = "china-gdp-growth"
    CPI = "china-cpi"
    FX_RESERVES = "china-foreign-exchange-reserves"
    RMB_USD = "china-rmb-usd-rate"
    ECOMMERCE = "ecommerce-market-china-vs-world"

    # 物流/基建
    PORT_THROUGHPUT = "china-port-throughput"                   # 港口吞吐量
    CONTAINER_PORT = "container-port-traffic-china-vs-world"   # 集装箱港口
    MARITIME_FLEET = "china-maritime-fleet-tonnage"             # 商船吨位
    SHIPBUILDING = "china-shipbuilding-orders"                  # 造船订单

    # ── API 方法 ──────────────────────────────────────────

    def query(
        self,
        dataset_slug: str = "china-trade-monthly",
    ) -> DataResult:
        """
        获取指定数据集的完整数据。

        Args:
            dataset_slug: 数据集标识符 (如 "china-trade-monthly")
                         使用类常量更方便, 如 ChinaDataPortalConnector.TRADE_MONTHLY

        Returns:
            DataResult，其中 data 字段为时间序列数组，每条记录含 date + 各指标值
        """
        url = f"{self.base_url}/data/{dataset_slug}"

        query_desc = {"dataset": dataset_slug}

        try:
            raw = self._get(url)
            ds = raw.get("data", raw) if isinstance(raw, dict) else raw
            records = ds.get("data", []) if isinstance(ds, dict) else []
            metadata = {}
            if isinstance(ds, dict):
                metadata = {
                    "title": ds.get("title"),
                    "unit": ds.get("unit"),
                    "frequency": ds.get("frequency"),
                    "source": ds.get("source"),
                    "category": ds.get("category"),
                    "is_comparison": ds.get("isComparison", False),
                    "total_points": len(records),
                }
            return DataResult(
                source=self.name,
                query=query_desc,
                data=records,
                metadata=metadata,
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data=[],
                error=str(e),
            )

    def list_datasets(self) -> DataResult:
        """列出所有可用数据集（仅元数据，不含数据点）。"""
        url = f"{self.base_url}/datasets"
        try:
            raw = self._get(url)
            datasets = raw.get("data", raw) if isinstance(raw, dict) else raw
            if not isinstance(datasets, list):
                datasets = [datasets]
            return DataResult(
                source=self.name,
                query={"action": "list_datasets"},
                data=datasets,
                metadata={"total": len(datasets)},
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query={"action": "list_datasets"},
                data=[],
                error=str(e),
            )

    def search(self, keyword: str) -> DataResult:
        """
        全文搜索数据集。

        Args:
            keyword: 搜索关键词 (如 "trade", "energy", "vehicle")
        """
        url = f"{self.base_url}/search"
        params = {"q": keyword}
        try:
            raw = self._get(url, params=params)
            results = raw.get("results", []) if isinstance(raw, dict) else raw
            return DataResult(
                source=self.name,
                query={"action": "search", "keyword": keyword},
                data=results,
                metadata={
                    "count": raw.get("count", len(results)),
                    "fallback": raw.get("fallback", False),
                },
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query={"action": "search", "keyword": keyword},
                data=[],
                error=str(e),
            )

    # ── 快捷方法 (出海调研高频场景) ──────────────────────

    def get_trade_monthly(self) -> DataResult:
        """获取中国月度进出口数据。返回含 total/export/import/balance 的月度序列。"""
        return self.query(self.TRADE_MONTHLY)

    def get_trade_partners(self) -> DataResult:
        """获取中国主要贸易伙伴年度数据 (ASEAN/USA/EU)。"""
        return self.query(self.TRADE_TOP_PARTNERS)

    def get_manufacturing(self, product: str) -> DataResult:
        """
        获取中国 vs 全球的制造业产量对比。

        Args:
            product: 产品类别，可选值:
                air_conditioners, washing_machines, smartphones,
                semiconductors, solar_panels, batteries, led,
                textiles, footwear, furniture, toys, steel, glass
        """
        slug_map = {
            "air_conditioners": self.MFG_AIR_CONDITIONERS,
            "washing_machines": self.MFG_WASHING_MACHINES,
            "smartphones": self.MFG_SMARTPHONES,
            "semiconductors": self.MFG_SEMICONDUCTORS,
            "solar_panels": self.MFG_SOLAR_PANELS,
            "batteries": self.MFG_BATTERIES,
            "led": self.MFG_LED,
            "textiles": self.MFG_TEXTILES,
            "footwear": self.MFG_FOOTWEAR,
            "furniture": self.MFG_FURNITURE,
            "toys": self.MFG_TOYS,
            "steel": self.MFG_STEEL,
            "glass": self.MFG_GLASS,
        }
        slug = slug_map.get(product)
        if not slug:
            return DataResult(
                source=self.name,
                query={"product": product},
                data=[],
                error=f"Unknown product '{product}'. Available: {', '.join(slug_map.keys())}",
            )
        return self.query(slug)

    def get_auto_exports(self) -> DataResult:
        """获取中国汽车出口（按地区分）。"""
        return self.query(self.AUTO_EXPORTS_REGION)

    def get_port_throughput(self) -> DataResult:
        """获取中国港口货物吞吐量。"""
        return self.query(self.PORT_THROUGHPUT)

    def get_exchange_rate(self) -> DataResult:
        """获取人民币/美元汇率历史。"""
        return self.query(self.RMB_USD)

    def get_ecommerce(self) -> DataResult:
        """获取中国电商市场规模 vs 全球。"""
        return self.query(self.ECOMMERCE)
