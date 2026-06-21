"""
智能数据路由引擎 (Smart Data Router)
====================================
根据调研主题自动路由到最优数据源组合。

设计原则:
  1. 免费优先 — 先用免费源，付费源做补充/验证
  2. 并行采集 — 同一主题的多个数据源并行查询
  3. 成本控制 — 按量计费的源仅在需要时调用
  4. 结果聚合 — 多源数据合并到统一 DataResult

路由规则:
  主题 → 匹配 tag → 查路由表 → 返回 (数据源, 查询方法, 优先级)

用法:
    from data_connectors.router import ResearchRouter

    router = ResearchRouter()

    # 自动路由
    plan = router.plan("solar camera 出口美国的市场规模")
    results = router.execute(plan)

    # 查看路由计划（不执行）
    router.explain(plan)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable
from .base import DataResult
from .registry import get_registry


# ── 研究主题分类 ────────────────────────────────────────

TOPIC_TAGS = {
    # 宏观贸易
    "trade_macro": {
        "keywords": [
            "贸易", "进出口", "出口", "进口", "关税", "trade", "export", "import",
            "tariff", "海关", "customs", "顺差", "逆差", "balance",
        ],
        "desc": "宏观贸易数据（进出口额/贸易伙伴/关税）",
    },
    # 品类/产品调研
    "product_research": {
        "keywords": [
            "选品", "产品", "品类", "product", "category", "爆品", "trending",
            "热销", "best seller", "niche", "利基", "蓝海",
        ],
        "desc": "产品/品类市场调研",
    },
    # 电商平台
    "ecommerce": {
        "keywords": [
            "amazon", "亚马逊", "shopee", "tiktok shop", "lazada", "ebay",
            "电商", "ecommerce", "e-commerce", "独立站", "d2c", "dtc",
            "shopify", "listing", "asin", "sku",
        ],
        "desc": "电商平台数据（产品/排名/价格/评分）",
    },
    # 社媒/内容
    "social_media": {
        "keywords": [
            "tiktok", "抖音", "douyin", "小红书", "xhs", "red note", "instagram",
            "youtube", "达人", "网红", "kol", "influencer", "creator",
            "视频", "内容", "话题", "hashtag", "热搜", "trending",
            "直播", "live", "带货",
        ],
        "desc": "社交媒体趋势/达人/内容分析",
    },
    # 竞品分析
    "competitor": {
        "keywords": [
            "竞品", "竞争", "competitor", "对手", "benchmark", "对标",
            "广告", "ad", "投放", "素材", "creative", "meta ads",
        ],
        "desc": "竞品分析/广告素材监控",
    },
    # 宏观经济
    "macro_economy": {
        "keywords": [
            "gdp", "cpi", "通胀", "inflation", "汇率", "exchange rate",
            "利率", "interest rate", "经济", "economy", "人口", "population",
            "消费", "consumer", "就业", "employment",
        ],
        "desc": "宏观经济指标",
    },
    # 制造业/供应链
    "manufacturing": {
        "keywords": [
            "制造", "manufacturing", "产量", "production", "工厂", "factory",
            "供应链", "supply chain", "1688", "采购", "sourcing",
            "OEM", "ODM", "MOQ", "白牌", "white label",
            "空调", "洗衣机", "冰箱", "电子", "electronics", "半导体",
            "semiconductor", "汽配", "auto parts", "家电", "appliance",
        ],
        "desc": "制造业产量/供应链/采购",
    },
    # 物流/运费
    "logistics": {
        "keywords": [
            "物流", "logistics", "运费", "freight", "海运", "shipping",
            "空运", "air freight", "快递", "express", "港口", "port",
            "集装箱", "container", "仓储", "warehouse", "FBA",
        ],
        "desc": "物流/运费/港口数据",
    },
    # 搜索趋势
    "search_trends": {
        "keywords": [
            "搜索趋势", "search trend", "google trends", "关键词", "keyword",
            "搜索量", "search volume", "SEO", "SEM",
        ],
        "desc": "搜索引擎趋势/关键词分析",
    },
    # 国家/市场
    "market_country": {
        "keywords": [
            "越南", "vietnam", "东南亚", "southeast asia", "美国", "usa",
            "欧洲", "europe", "日本", "japan", "韩国", "korea",
            "中东", "middle east", "非洲", "africa", "巴西", "brazil",
            "印度", "india", "墨西哥", "mexico",
        ],
        "desc": "特定国家/区域市场分析",
    },
    # 大宗商品/期货
    "commodities": {
        "keywords": [
            "大宗", "commodity", "commodities", "期货", "futures",
            "石油", "oil", "wti", "brent", "原油", "crude",
            "铜", "copper", "铝", "aluminum", "黄金", "gold",
            "小麦", "wheat", "玉米", "corn", "棉花", "cotton",
            "大豆", "soybean", "糖", "sugar", "咖啡", "coffee",
            "天然气", "natural gas", "铁矿", "iron ore",
        ],
        "desc": "大宗商品价格/期货/原材料",
    },
    # 金融/股票
    "finance_stock": {
        "keywords": [
            "股票", "stock", "stocks", "个股", "equity", "equities",
            "市值", "market cap", "pe", "eps", "财报", "earnings",
            "k线", "k-line", "技术指标", "technical", "macd", "rsi",
            "etf", "基金", "fund", "指数", "index", "标普", "s&p",
            "纳斯达克", "nasdaq", "道琼斯", "dow jones",
            "ipo", "上市", "分红", "dividend",
        ],
        "desc": "股票行情/财报/技术指标/ETF",
    },
}


# ── 路由表: tag → [(数据源, 方法名, 优先级, 成本层)] ────

ROUTE_TABLE: dict[str, list[tuple[str, str, int, str]]] = {
    #                  (connector,         method,                    priority, tier)
    "trade_macro": [
        ("china_data_portal", "get_trade_monthly",           1, "free"),
        ("china_data_portal", "get_trade_partners",          1, "free"),
        ("un_comtrade",       "get_china_exports",           2, "free"),
        ("wto",               "get_data",                    2, "free"),
        ("world_bank",        "query",                       3, "free"),
        ("oecd",              "query",                       4, "free"),
    ],
    "product_research": [
        ("tikhub",            "tiktok_search_video",         1, "low_cost"),
        ("tikhub",            "tiktok_trending_keywords",    1, "low_cost"),
        ("dataforseo",        "query",                       2, "low_cost"),
        ("tikhub",            "xhs_search",                  3, "low_cost"),
        ("google_trends",     "query",                       3, "free"),
        ("china_data_portal", "search",                      4, "free"),
    ],
    "ecommerce": [
        ("dataforseo",        "query",                       1, "low_cost"),
        ("dataforseo",        "serp_search",                 1, "low_cost"),
        ("tikhub",            "tiktok_search_video",         2, "low_cost"),
        ("google_trends",     "query",                       3, "free"),
    ],
    "social_media": [
        ("tikhub",            "tiktok_trending_keywords",    1, "low_cost"),
        ("tikhub",            "tiktok_trending_videos",      1, "low_cost"),
        ("tikhub",            "tiktok_search_video",         2, "low_cost"),
        ("tikhub",            "douyin_trending",             2, "low_cost"),
        ("tikhub",            "xhs_search",                  3, "low_cost"),
        ("tikhub",            "youtube_search",              3, "low_cost"),
        ("google_trends",     "query",                       4, "free"),
    ],
    "competitor": [
        ("dataforseo",        "serp_search",                 1, "low_cost"),
        ("dataforseo",        "query",                       1, "low_cost"),
        ("tikhub",            "tiktok_search_video",         2, "low_cost"),
        ("tikhub",            "instagram_search",            3, "low_cost"),
        ("google_trends",     "query",                       4, "free"),
    ],
    "macro_economy": [
        ("world_bank",        "query",                       1, "free"),
        ("exchange_rate",     "query",                       1, "free"),
        ("fred",              "query",                       1, "free"),
        ("alpha_vantage",     "econ_cpi",                    1, "free"),
        ("china_data_portal", "query",                       2, "free"),
        ("oecd",              "query",                       3, "free"),
    ],
    "manufacturing": [
        ("china_data_portal", "get_manufacturing",           1, "free"),
        ("china_data_portal", "search",                      1, "free"),
        ("un_comtrade",       "get_china_exports",           2, "free"),
        ("world_bank",        "query",                       3, "free"),
        ("dataforseo",        "query",                       4, "low_cost"),
    ],
    "logistics": [
        ("china_data_portal", "get_port_throughput",         1, "free"),
        ("china_data_portal", "query",                       2, "free"),
        ("exchange_rate",     "query",                       3, "free"),
    ],
    "search_trends": [
        ("google_trends",     "query",                       1, "free"),
        ("google_trends",     "related_queries",             1, "free"),
        ("tikhub",            "tiktok_keyword_suggest",      2, "low_cost"),
        ("dataforseo",        "serp_search",                 3, "low_cost"),
    ],
    "market_country": [
        ("world_bank",        "query",                       1, "free"),
        ("fred",              "search",                      1, "free"),
        ("un_comtrade",       "query",                       2, "free"),
        ("china_data_portal", "get_trade_monthly",           2, "free"),
        ("exchange_rate",     "query",                       3, "free"),
        ("google_trends",     "query",                       3, "free"),
        ("tikhub",            "tiktok_search_video",         4, "low_cost"),
    ],
    "commodities": [
        ("alpha_vantage",     "commodity_wti",               1, "free"),
        ("alpha_vantage",     "commodity_copper",            1, "free"),
        ("alpha_vantage",     "commodity_all_index",         1, "free"),
        ("alpha_vantage",     "fx_rate",                     2, "free"),
        ("world_bank",        "query",                       3, "free"),
        ("google_trends",     "query",                       4, "free"),
    ],
    "finance_stock": [
        ("alpha_vantage",     "stock_quote",                 1, "free"),
        ("alpha_vantage",     "stock_overview",              1, "free"),
        ("alpha_vantage",     "stock_search",                1, "free"),
        ("alpha_vantage",     "econ_treasury_yield",         2, "free"),
        ("alpha_vantage",     "econ_fed_funds_rate",         2, "free"),
        ("google_trends",     "query",                       3, "free"),
        ("dataforseo",        "serp_search",                 4, "low_cost"),
    ],
}


@dataclass
class RouteStep:
    """Single step in a routing plan."""
    connector_name: str
    method_name: str
    priority: int       # 1=最高, 数字越大优先级越低
    cost_tier: str      # free / low_cost / paid
    params: dict = field(default_factory=dict)
    tag: str = ""


@dataclass
class RoutePlan:
    """Complete routing plan for a research query."""
    query: str
    matched_tags: list[str]
    steps: list[RouteStep]
    free_steps: list[RouteStep] = field(default_factory=list)
    paid_steps: list[RouteStep] = field(default_factory=list)

    def __post_init__(self):
        self.free_steps = [s for s in self.steps if s.cost_tier == "free"]
        self.paid_steps = [s for s in self.steps if s.cost_tier != "free"]


class ResearchRouter:
    """
    智能数据路由引擎。

    根据自然语言调研主题，自动:
      1. 识别主题标签 (trade / product / social / macro / ...)
      2. 查路由表选择最优数据源组合
      3. 按优先级排序（免费优先）
      4. 可选: 直接执行并聚合结果

    用法:
        router = ResearchRouter()
        plan = router.plan("solar camera 出口美国的市场")
        router.explain(plan)
        results = router.execute(plan, keyword="solar camera")
    """

    def __init__(self, free_only: bool = False):
        """
        Args:
            free_only: True = 只使用免费数据源
        """
        self.registry = get_registry()
        self.free_only = free_only

    def classify(self, query: str) -> list[str]:
        """
        将自然语言查询分类到主题标签。

        Args:
            query: 调研主题描述

        Returns:
            匹配到的 tag 列表（按匹配度排序）
        """
        query_lower = query.lower()
        scores: dict[str, int] = {}

        for tag, info in TOPIC_TAGS.items():
            score = 0
            for kw in info["keywords"]:
                if kw.lower() in query_lower:
                    # 长关键词权重更高
                    score += len(kw)
            if score > 0:
                scores[tag] = score

        # 按分数排序
        sorted_tags = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
        return sorted_tags if sorted_tags else ["product_research"]  # 默认

    def plan(self, query: str) -> RoutePlan:
        """
        根据调研主题生成路由计划。

        Args:
            query: 自然语言调研描述

        Returns:
            RoutePlan 包含所有推荐的数据源和方法
        """
        tags = self.classify(query)
        steps: list[RouteStep] = []
        seen: set[tuple[str, str]] = set()  # 去重 (connector, method)

        for tag in tags:
            routes = ROUTE_TABLE.get(tag, [])
            for conn_name, method, priority, tier in routes:
                key = (conn_name, method)
                if key in seen:
                    continue
                if self.free_only and tier != "free":
                    continue
                # 检查connector是否可用（有key）
                if conn_name in self.registry:
                    conn = self.registry.get(conn_name)
                    if conn.requires_key and not conn.api_key:
                        continue  # 跳过没有key的付费源
                    if hasattr(conn, method):
                        seen.add(key)
                        steps.append(RouteStep(
                            connector_name=conn_name,
                            method_name=method,
                            priority=priority,
                            cost_tier=tier,
                            tag=tag,
                        ))

        # 按 (cost_tier=free优先, priority) 排序
        tier_order = {"free": 0, "low_cost": 1, "paid": 2}
        steps.sort(key=lambda s: (tier_order.get(s.cost_tier, 9), s.priority))

        return RoutePlan(query=query, matched_tags=tags, steps=steps)

    def explain(self, plan: RoutePlan) -> str:
        """
        生成路由计划的可读说明。

        Returns:
            Markdown 格式的路由说明
        """
        lines = [
            f"## 调研路由计划",
            f"**主题**: {plan.query}",
            f"**匹配标签**: {', '.join(plan.matched_tags)}",
            f"**数据源数**: {len(plan.steps)} ({len(plan.free_steps)} 免费 + {len(plan.paid_steps)} 付费)",
            "",
            "### 执行步骤",
            "| # | 数据源 | 方法 | 优先级 | 成本 | 主题 |",
            "|---|--------|------|--------|------|------|",
        ]
        for i, step in enumerate(plan.steps, 1):
            cost = "🆓" if step.cost_tier == "free" else "💰"
            lines.append(
                f"| {i} | {step.connector_name} | {step.method_name} "
                f"| P{step.priority} | {cost} {step.cost_tier} | {step.tag} |"
            )

        output = "\n".join(lines)
        print(output)
        return output

    def execute(
        self,
        plan: RoutePlan,
        keyword: str | None = None,
        max_steps: int | None = None,
        free_only: bool | None = None,
        **extra_params,
    ) -> dict[str, DataResult]:
        """
        执行路由计划，采集所有数据源。

        Args:
            plan: 路由计划
            keyword: 搜索关键词（自动传给需要的方法）
            max_steps: 最多执行几步（None=全部）
            free_only: 只执行免费步骤
            **extra_params: 额外参数（如 year, country 等）

        Returns:
            dict: {step_key: DataResult}
        """
        use_free_only = free_only if free_only is not None else self.free_only
        results: dict[str, DataResult] = {}

        steps = plan.steps
        if use_free_only:
            steps = plan.free_steps
        if max_steps:
            steps = steps[:max_steps]

        for step in steps:
            step_key = f"{step.connector_name}.{step.method_name}"
            try:
                conn = self.registry.get(step.connector_name)
                method = getattr(conn, step.method_name)

                # 智能参数注入
                params = self._build_params(method, keyword, step, extra_params)
                result = method(**params)
                results[step_key] = result

            except Exception as e:
                results[step_key] = DataResult(
                    source=step.connector_name,
                    query={"method": step.method_name},
                    data=[],
                    error=str(e),
                )

        return results

    def _build_params(
        self,
        method: Callable,
        keyword: str | None,
        step: RouteStep,
        extra: dict,
    ) -> dict:
        """智能构建方法参数。"""
        import inspect
        sig = inspect.signature(method)
        params: dict[str, Any] = {}

        param_names = list(sig.parameters.keys())

        # 关键词参数注入
        if keyword:
            for name in ["keyword", "keywords"]:
                if name in param_names:
                    if name == "keywords":
                        params[name] = [keyword]
                    else:
                        params[name] = keyword

        # step 预设参数
        params.update(step.params)

        # 额外参数匹配
        for k, v in extra.items():
            if k in param_names:
                params[k] = v

        # 特殊处理：某些方法需要特定参数格式
        if step.connector_name == "china_data_portal" and step.method_name == "get_manufacturing":
            # 从keyword推断产品类型
            if keyword and "product" not in params:
                product = self._infer_product(keyword)
                if product:
                    params["product"] = product

        if step.connector_name == "un_comtrade" and step.method_name == "get_china_exports":
            if "hs_code" not in params:
                hs = self._infer_hs_code(keyword or "")
                if hs:
                    params["hs_code"] = hs

        return params

    def _infer_product(self, keyword: str) -> str | None:
        """从关键词推断制造业产品类别。"""
        kw = keyword.lower()
        mappings = {
            "air_conditioners": ["空调", "air conditioner", "ac unit", "hvac"],
            "washing_machines": ["洗衣机", "washing machine", "laundry"],
            "smartphones": ["手机", "smartphone", "phone", "mobile"],
            "semiconductors": ["半导体", "semiconductor", "chip", "芯片", "ic"],
            "solar_panels": ["太阳能", "solar panel", "solar cell", "光伏"],
            "batteries": ["电池", "battery", "lithium", "锂电"],
            "led": ["led", "照明", "lighting"],
            "textiles": ["纺织", "textile", "fabric", "面料"],
            "footwear": ["鞋", "shoe", "footwear", "sneaker"],
            "furniture": ["家具", "furniture"],
            "toys": ["玩具", "toy"],
            "steel": ["钢", "steel", "iron"],
            "glass": ["玻璃", "glass"],
        }
        for product, keywords in mappings.items():
            for k in keywords:
                if k in kw:
                    return product
        return None

    def _infer_hs_code(self, keyword: str) -> str | None:
        """从关键词推断 HS 编码。"""
        kw = keyword.lower()
        mappings = {
            "8471": ["computer", "计算机", "laptop", "电脑"],
            "8708": ["auto parts", "汽配", "汽车配件", "car parts"],
            "8541": ["semiconductor", "半导体", "chip", "芯片"],
            "8418": ["refrigerator", "冰箱", "fridge", "冷柜"],
            "8450": ["washing machine", "洗衣机"],
            "8415": ["air conditioner", "空调"],
            "8525": ["camera", "摄像", "摄影", "监控"],
            "8528": ["tv", "television", "电视", "显示器", "monitor"],
            "8517": ["phone", "手机", "telephone", "smartphone"],
            "9405": ["led", "lighting", "灯", "照明"],
            "8507": ["battery", "电池", "蓄电池"],
            "8541.40": ["solar cell", "太阳能电池", "光伏"],
            "9503": ["toy", "玩具"],
            "6402": ["shoe", "鞋", "footwear"],
            "9401": ["furniture", "家具", "椅"],
        }
        for hs, keywords in mappings.items():
            for k in keywords:
                if k in kw:
                    return hs
        return None

    def quick_research(
        self,
        topic: str,
        keyword: str | None = None,
        max_steps: int = 6,
        **params,
    ) -> dict[str, DataResult]:
        """
        一键调研：自动规划 + 执行 + 返回结果。

        Args:
            topic: 调研主题描述
            keyword: 搜索关键词（可选，从topic中提取）
            max_steps: 最多查询几个数据源
            **params: 额外参数

        Returns:
            {step_key: DataResult}

        Example:
            router = ResearchRouter()
            results = router.quick_research(
                "solar camera 出口美国的市场规模",
                keyword="solar camera",
            )
        """
        plan = self.plan(topic)
        return self.execute(plan, keyword=keyword, max_steps=max_steps, **params)
