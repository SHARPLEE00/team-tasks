"""
UN Comtrade API v1 (new) — 全球贸易数据
https://comtradeapi.un.org/

免费层 (preview endpoint): 无需Key，每次最多500条。
注册Key后: 500次/天, 最多100,000条/次。
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class UNComtradeConnector(BaseConnector):
    name = "un_comtrade"
    cost_tier = "free"
    requires_key = False
    base_url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    rate_limit_per_min = 10

    # 常用报告国代码 (UN M49)
    CHINA = "156"
    USA = "842"
    VIETNAM = "704"
    WORLD = "0"

    # 常用HS编码 (前4位)
    HS_ELECTRONICS = "8471"            # 计算机
    HS_AUTO_PARTS = "8708"             # 汽车配件
    HS_SEMICONDUCTORS = "8541"         # 半导体
    HS_WHITE_GOODS_FRIDGE = "8418"     # 冰箱
    HS_WASHING_MACHINE = "8450"        # 洗衣机
    HS_AIR_CONDITIONER = "8415"        # 空调
    HS_CAMERAS = "8525"                # 摄像机
    HS_SOLAR_CELLS = "8541.40"         # 太阳能电池

    def query(
        self,
        reporter: str = "156",
        partner: str = "0",
        hs_code: str = "8471",
        year: str = "2023",
        trade_flow: str = "X",
        max_records: int = 500,
    ) -> DataResult:
        """
        查询全球贸易数据。

        Args:
            reporter: 报告国代码 (156=中国, 842=美国, 704=越南)
            partner: 贸易伙伴 (0=世界)
            hs_code: HS编码
            year: 年份
            trade_flow: X=出口, M=进口
            max_records: 最大返回记录数
        """
        params = {
            "cmdCode": hs_code,
            "reporterCode": reporter,
            "period": year,
            "flowCode": trade_flow,
            "partnerCode": partner,
            "maxRecords": str(max_records),
        }

        headers = {}
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key

        query_desc = {
            "reporter": reporter,
            "partner": partner,
            "hs_code": hs_code,
            "year": year,
            "trade_flow": trade_flow,
        }

        try:
            raw = self._get(self.base_url, params=params, headers=headers)
            records = raw.get("data", [])
            return DataResult(
                source=self.name,
                query=query_desc,
                data=records,
                metadata={
                    "total_records": raw.get("count", len(records)),
                    "elapsed_time": raw.get("elapsedTime"),
                },
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data=[],
                error=str(e),
            )

    def get_china_exports(self, hs_code: str, year: str = "2023") -> DataResult:
        """快捷：查中国出口某品类到全球的数据。"""
        return self.query(
            reporter=self.CHINA,
            partner=self.WORLD,
            hs_code=hs_code,
            year=year,
            trade_flow="X",
        )

    def get_top_exporters(self, hs_code: str, year: str = "2023") -> DataResult:
        """快捷：查全球某品类各国出口到世界。"""
        return self.query(
            reporter="",  # all reporters
            partner=self.WORLD,
            hs_code=hs_code,
            year=year,
            trade_flow="X",
        )
