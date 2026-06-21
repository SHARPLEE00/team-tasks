"""
UN Comtrade — 全球贸易数据 (基于官方 comtradeapicall 库)
https://github.com/uncomtrade/comtradeapicall
https://comtradeapi.un.org/

免费层 (preview): 无需Key，每次最多500条
注册Key后: 500次/天, 最多250K条/次, 含贸易矩阵/双边/批量下载

依赖: pip install comtradeapicall pandas
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class UNComtradeConnector(BaseConnector):
    name = "un_comtrade"
    cost_tier = "free"
    requires_key = False
    base_url = "https://comtradeapi.un.org"
    rate_limit_per_min = 10

    # ── 常用国家代码 ────────────────────────────────

    CHINA = "156"
    USA = "842"
    VIETNAM = "704"
    WORLD = "0"

    # ── 常用HS编码 ──────────────────────────────────

    HS_ELECTRONICS = "8471"            # 计算机
    HS_AUTO_PARTS = "8708"             # 汽车配件
    HS_SEMICONDUCTORS = "8541"         # 半导体
    HS_WHITE_GOODS_FRIDGE = "8418"     # 冰箱
    HS_WASHING_MACHINE = "8450"        # 洗衣机
    HS_AIR_CONDITIONER = "8415"        # 空调
    HS_CAMERAS = "8525"                # 摄像机
    HS_TV_MONITOR = "8528"             # 电视/显示器
    HS_PHONE = "8517"                  # 电话/手机
    HS_LED_LIGHTING = "9405"           # LED/照明
    HS_BATTERY = "8507"                # 电池
    HS_SOLAR_CELL = "8541.40"          # 太阳能电池
    HS_TOYS = "9503"                   # 玩具
    HS_FOOTWEAR = "6402"               # 鞋类
    HS_FURNITURE = "9401"              # 家具

    def _get_lib(self):
        """Lazy import comtradeapicall."""
        try:
            import comtradeapicall
            return comtradeapicall
        except ImportError:
            raise ImportError(
                "comtradeapicall not installed. Run: pip install comtradeapicall pandas"
            )

    def _df_to_records(self, df) -> list[dict]:
        """Convert DataFrame to list of dicts."""
        if df is None:
            return []
        try:
            return df.to_dict(orient="records")
        except Exception:
            return []

    # ── 核心查询 (无需Key) ──────────────────────────

    def query(
        self,
        reporter: str = "156",
        partner: str | None = None,
        hs_code: str = "8471",
        period: str = "2023",
        trade_flow: str = "X",
        freq: str = "A",
        max_records: int = 500,
        include_desc: bool = True,
    ) -> DataResult:
        """
        查询全球贸易数据（Preview模式，无需Key，最多500条）。

        Args:
            reporter: 报告国代码 (156=中国, 842=美国, 704=越南)
            partner: 贸易伙伴 (None=全部, "0"=世界合计)
            hs_code: HS编码 (如 "8525" 或 "85" 或 "8525,8471")
            period: 时间 (年度:"2023", 月度:"202305")
            trade_flow: X=出口, M=进口
            freq: A=年度, M=月度
            max_records: 最大返回 (免费版上限500)
            include_desc: 是否包含描述文字
        """
        lib = self._get_lib()

        query_desc = {
            "reporter": reporter,
            "partner": partner,
            "hs_code": hs_code,
            "period": period,
            "trade_flow": trade_flow,
        }

        try:
            df = lib.previewFinalData(
                typeCode="C",
                freqCode=freq,
                clCode="HS",
                period=period,
                reporterCode=reporter,
                cmdCode=hs_code,
                flowCode=trade_flow,
                partnerCode=partner,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=max_records,
                format_output="JSON",
                breakdownMode="classic",
                countOnly=None,
                includeDesc=include_desc,
            )
            records = self._df_to_records(df)
            return DataResult(
                source=self.name,
                query=query_desc,
                data=records,
                metadata={"total_records": len(records), "mode": "preview"},
            )
        except Exception as e:
            return DataResult(
                source=self.name,
                query=query_desc,
                data=[],
                error=str(e),
            )

    # ── 高级查询 (需Key) ───────────────────────────

    def query_full(
        self,
        reporter: str = "156",
        partner: str | None = None,
        hs_code: str = "8525",
        period: str = "2023",
        trade_flow: str = "X",
        freq: str = "A",
        max_records: int = 2500,
        include_desc: bool = True,
    ) -> DataResult:
        """
        完整查询（需Key，最多250K条，支持多编码/多年份）。
        """
        if not self.api_key:
            return DataResult(
                source=self.name,
                query={"error": "需要 UN Comtrade subscription key"},
                data=[],
                error="No subscription key. Set UN_COMTRADE_KEY env var. "
                      "Register at https://comtradeplus.un.org/",
            )

        lib = self._get_lib()
        query_desc = {
            "reporter": reporter, "partner": partner,
            "hs_code": hs_code, "period": period,
            "trade_flow": trade_flow, "mode": "full",
        }

        try:
            df = lib.getFinalData(
                self.api_key,
                typeCode="C",
                freqCode=freq,
                clCode="HS",
                period=period,
                reporterCode=reporter,
                cmdCode=hs_code,
                flowCode=trade_flow,
                partnerCode=partner,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=max_records,
                format_output="JSON",
                breakdownMode="classic",
                countOnly=None,
                includeDesc=include_desc,
            )
            records = self._df_to_records(df)
            return DataResult(
                source=self.name,
                query=query_desc,
                data=records,
                metadata={"total_records": len(records), "mode": "full"},
            )
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_trade_balance(
        self,
        reporter: str = "156",
        partner: str | None = None,
        hs_code: str = "TOTAL",
        period: str = "2023",
        freq: str = "A",
    ) -> DataResult:
        """
        贸易差额（出口和进口并排显示），需Key。
        """
        if not self.api_key:
            return DataResult(
                source=self.name, query={}, data=[],
                error="Needs subscription key",
            )
        lib = self._get_lib()
        query_desc = {"reporter": reporter, "hs_code": hs_code, "period": period, "type": "trade_balance"}
        try:
            df = lib.getTradeBalance(
                self.api_key, typeCode="C", freqCode=freq, clCode="HS",
                period=period, reporterCode=reporter, cmdCode=hs_code,
                partnerCode=partner,
            )
            records = self._df_to_records(df)
            return DataResult(source=self.name, query=query_desc, data=records,
                              metadata={"total_records": len(records)})
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_trade_matrix(
        self,
        hs_code: str = "TOTAL",
        period: str = "2023",
        trade_flow: str = "X",
    ) -> DataResult:
        """
        贸易矩阵（全球出口/进口估算），需Key。
        """
        if not self.api_key:
            return DataResult(
                source=self.name, query={}, data=[],
                error="Needs subscription key",
            )
        lib = self._get_lib()
        query_desc = {"hs_code": hs_code, "period": period, "type": "trade_matrix"}
        try:
            df = lib.getTradeMatrix(
                self.api_key, typeCode="C", freqCode="A",
                period=period, reporterCode="0", cmdCode=hs_code,
                flowCode=trade_flow, partnerCode="0",
                aggregateBy=None, includeDesc=True,
            )
            records = self._df_to_records(df)
            return DataResult(source=self.name, query=query_desc, data=records,
                              metadata={"total_records": len(records)})
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    # ── Tools API v1 ─────────────────────────────────

    def get_bilateral(
        self,
        reporter: str = "156",
        partner: str = "842",
        hs_code: str = "8525",
        period: str = "2023",
        trade_flow: str = "X",
        freq: str = "A",
    ) -> DataResult:
        """
        双边贸易对比（报告方数据 vs 镜像伙伴方数据），需Key。
        Tools API v1: /tools/v1/getBilateralData/

        Args:
            reporter: 报告国
            partner: 伙伴国
            hs_code: HS编码
            period: 时间
            trade_flow: X=出口, M=进口
        """
        if not self.api_key:
            return DataResult(
                source=self.name, query={}, data=[],
                error="Needs subscription key. Register: https://comtradedeveloper.un.org/",
            )
        lib = self._get_lib()
        query_desc = {
            "reporter": reporter, "partner": partner,
            "hs_code": hs_code, "period": period, "type": "bilateral",
        }
        try:
            df = lib.getBilateralData(
                self.api_key, typeCode="C", freqCode=freq, clCode="HS",
                period=period, reporterCode=reporter, cmdCode=hs_code,
                flowCode=trade_flow, partnerCode=partner,
                includeDesc=True,
            )
            records = self._df_to_records(df)
            return DataResult(source=self.name, query=query_desc, data=records,
                              metadata={"total_records": len(records)})
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_suv(
        self,
        hs_code: str = "010391",
        period: str = "2022",
        reporter: str | None = None,
    ) -> DataResult:
        """
        标准单位值 (Standard Unit Value)，需Key。

        Args:
            hs_code: HS编码 (6位)
            period: 年份
            reporter: 报告国 (None=全球)
        """
        if not self.api_key:
            return DataResult(source=self.name, query={}, data=[], error="Needs subscription key")
        lib = self._get_lib()
        query_desc = {"hs_code": hs_code, "period": period, "type": "suv"}
        try:
            df = lib.getSUV(
                self.api_key, typeCode="C", freqCode="A", clCode="HS",
                cmdCode=hs_code, period=period, reporterCode=reporter,
                includeDesc=True,
            )
            records = self._df_to_records(df)
            return DataResult(source=self.name, query=query_desc, data=records,
                              metadata={"total_records": len(records)})
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    def get_live_updates(self) -> DataResult:
        """获取最近发布的数据更新，需Key。"""
        if not self.api_key:
            return DataResult(source=self.name, query={}, data=[], error="Needs subscription key")
        lib = self._get_lib()
        try:
            df = lib.getLiveUpdate(self.api_key)
            records = self._df_to_records(df)
            return DataResult(source=self.name, query={"action": "live_updates"}, data=records)
        except Exception as e:
            return DataResult(source=self.name, query={}, data=[], error=str(e))

    # ── 工具方法 ────────────────────────────────────

    def convert_country(self, iso3_codes: str) -> str:
        """
        ISO3国家代码转Comtrade代码。

        Args:
            iso3_codes: 逗号分隔的ISO3码 (如 "USA,VNM,CHN")

        Returns:
            Comtrade 数字代码 (如 "842,704,156")
        """
        lib = self._get_lib()
        return lib.convertCountryIso3ToCode(iso3_codes)

    def list_references(self) -> DataResult:
        """列出所有参考表（国家/商品分类/运输方式等）。"""
        lib = self._get_lib()
        try:
            df = lib.listReference()
            records = self._df_to_records(df)
            return DataResult(
                source=self.name,
                query={"action": "list_references"},
                data=records,
            )
        except Exception as e:
            return DataResult(source=self.name, query={}, data=[], error=str(e))

    def get_reference(self, table: str = "reporter") -> DataResult:
        """
        获取参考表内容（国家列表/HS编码表等）。

        Args:
            table: 表名 (reporter/partner/cmd:HS/flow/freq 等)
        """
        lib = self._get_lib()
        try:
            df = lib.getReference(table)
            records = self._df_to_records(df)
            return DataResult(
                source=self.name,
                query={"action": "get_reference", "table": table},
                data=records,
                metadata={"total": len(records)},
            )
        except Exception as e:
            return DataResult(source=self.name, query={"table": table}, data=[], error=str(e))

    def count_records(
        self,
        reporter: str = "156",
        hs_code: str = "85",
        period: str = "2023",
        trade_flow: str = "X",
        partner: str = "0",
    ) -> DataResult:
        """预估记录数（无需Key）。"""
        lib = self._get_lib()
        query_desc = {"reporter": reporter, "hs_code": hs_code, "period": period, "type": "count"}
        try:
            df = lib.previewCountFinalData(
                typeCode="C", freqCode="A", clCode="HS",
                period=period, reporterCode=reporter, cmdCode=hs_code,
                flowCode=trade_flow, partnerCode=partner,
                partner2Code=None, customsCode=None, motCode=None,
                aggregateBy=None, breakdownMode="classic",
            )
            records = self._df_to_records(df)
            return DataResult(source=self.name, query=query_desc, data=records)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data=[], error=str(e))

    # ── 快捷方法 ────────────────────────────────────

    def get_china_exports(self, hs_code: str = "8525", year: str = "2023") -> DataResult:
        """快捷：查中国出口某品类到全球各国。"""
        return self.query(reporter=self.CHINA, partner=None, hs_code=hs_code, period=year, trade_flow="X")

    def get_china_imports(self, hs_code: str = "8525", year: str = "2023") -> DataResult:
        """快捷：查中国进口某品类来源国。"""
        return self.query(reporter=self.CHINA, partner=None, hs_code=hs_code, period=year, trade_flow="M")

    def get_bilateral(self, reporter: str = "156", partner: str = "842", hs_code: str = "TOTAL", year: str = "2023") -> DataResult:
        """快捷：查两国双边贸易。"""
        return self.query(reporter=reporter, partner=partner, hs_code=hs_code, period=year, trade_flow="X")

    def get_vietnam_trade(self, hs_code: str = "TOTAL", year: str = "2023") -> DataResult:
        """快捷：查越南贸易数据。"""
        return self.query(reporter=self.VIETNAM, partner=None, hs_code=hs_code, period=year, trade_flow="X")
