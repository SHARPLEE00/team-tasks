"""
Aximora 出海数据采集统一接口
===========================
免费 / 低成本第三方数据 API 封装，供调研报告自动调用。

已对接数据源（按成本分层）：

免费层:
  - UN Comtrade      全球贸易数据 (HS编码级别)
  - World Bank       宏观经济指标
  - OECD             OECD国家经济/贸易数据
  - China Data Portal 中国海关月度进出口
  - Google Trends    搜索趋势 (via pytrends)
  - ExchangeRate API 汇率数据

低成本层 (需 API Key):
  - DataForSEO       电商产品/SERP数据 ($0.001/次)
  - EchoTik          TikTok Shop 数据 ($9.9/月起)
  - Keepa            Amazon 价格历史 (€19/月)
  - Freightos        国际运费指数
"""

from .un_comtrade import UNComtradeConnector
from .world_bank import WorldBankConnector
from .oecd_data import OECDConnector
from .china_data_portal import ChinaDataPortalConnector
from .google_trends import GoogleTrendsConnector
from .exchange_rate import ExchangeRateConnector
from .dataforseo import DataForSEOConnector
from .echotik import EchoTikConnector
from .registry import ConnectorRegistry, get_registry

__all__ = [
    "UNComtradeConnector",
    "WorldBankConnector",
    "OECDConnector",
    "ChinaDataPortalConnector",
    "GoogleTrendsConnector",
    "ExchangeRateConnector",
    "DataForSEOConnector",
    "EchoTikConnector",
    "ConnectorRegistry",
    "get_registry",
]
