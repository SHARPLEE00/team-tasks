"""
Aximora 出海数据采集统一接口
===========================
免费 / 低成本第三方数据 API 封装，供调研报告自动调用。

已对接数据源（按成本分层）：

免费层 (无需注册，无需 Key，直接可用):
  - UN Comtrade      全球贸易数据 (HS编码级别)
  - World Bank       宏观经济指标 (200+国, 200+指标)
  - OECD             OECD国家经济/贸易数据
  - China Data Portal 中国海关 + 118个数据集
  - Google Trends    搜索趋势 (via pytrends)
  - ExchangeRate API 汇率数据 (150+货币)
  - Frankfurter      ECB官方汇率 (30+货币，含历史)
  - CoinGecko        加密货币价格/市场 (14000+币种)

低成本层 (需 API Key):
  - DataForSEO       电商产品/SERP数据 ($0.001/次)
  - EchoTik          TikTok Shop 数据 ($9.9/月起)
  - TikHub           16+社媒平台数据 (TikTok/抖音/小红书/IG/YT)

智能路由:
  - ResearchRouter   根据调研主题自动选择最优数据源组合
"""

from .un_comtrade import UNComtradeConnector
from .world_bank import WorldBankConnector
from .oecd_data import OECDConnector
from .china_data_portal import ChinaDataPortalConnector
from .google_trends import GoogleTrendsConnector
from .exchange_rate import ExchangeRateConnector
from .frankfurter import FrankfurterConnector
from .coingecko import CoinGeckoConnector
from .fred import FREDConnector
from .wto import WTOConnector
from .alpha_vantage import AlphaVantageConnector
from .dataforseo import DataForSEOConnector
from .echotik import EchoTikConnector
from .tikhub import TikHubConnector
from .registry import ConnectorRegistry, get_registry
from .router import ResearchRouter

__all__ = [
    "UNComtradeConnector",
    "WorldBankConnector",
    "OECDConnector",
    "ChinaDataPortalConnector",
    "GoogleTrendsConnector",
    "ExchangeRateConnector",
    "FrankfurterConnector",
    "CoinGeckoConnector",
    "FREDConnector",
    "WTOConnector",
    "AlphaVantageConnector",
    "DataForSEOConnector",
    "EchoTikConnector",
    "TikHubConnector",
    "ConnectorRegistry",
    "get_registry",
    "ResearchRouter",
]
