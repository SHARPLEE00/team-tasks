"""
TikHub API — 多平台社媒数据 (TikTok/Douyin/小红书/Instagram/YouTube等)
https://api.tikhub.io/

按量计费，需 Bearer Token。覆盖 16+ 平台、1000+ 端点。

核心能力:
  - TikTok: 视频/用户/搜索/热门/Shop产品/广告素材
  - Douyin: 视频/用户/搜索/热门/星图达人
  - 小红书: 笔记/用户/搜索/热门
  - Instagram/YouTube/Twitter: 视频/用户/搜索
"""

from __future__ import annotations
from .base import BaseConnector, DataResult


class TikHubConnector(BaseConnector):
    name = "tikhub"
    cost_tier = "low_cost"
    requires_key = True
    base_url = "https://api.tikhub.io"
    rate_limit_per_min = 60

    def _auth_header(self) -> dict:
        if not self.api_key:
            raise ValueError(
                "TikHub requires an API token. "
                "Set TIKHUB_API_KEY env var or pass api_key. "
                "Get one at https://tikhub.io/"
            )
        return {"Authorization": f"Bearer {self.api_key}"}

    def _api_get(self, endpoint: str, params: dict | None = None) -> dict:
        """Authenticated GET to TikHub API."""
        url = f"{self.base_url}{endpoint}"
        return self._get(url, params=params, headers=self._auth_header())

    # ── 通用 ─────────────────────────────────────────────

    def query(self, endpoint: str = "/api/v1/health/check", **params) -> DataResult:
        """Generic query to any TikHub endpoint."""
        query_desc = {"endpoint": endpoint, **params}
        try:
            raw = self._api_get(endpoint, params=params if params else None)
            return DataResult(source=self.name, query=query_desc, data=raw)
        except Exception as e:
            return DataResult(source=self.name, query=query_desc, data={}, error=str(e))

    def health_check(self) -> bool:
        r = self.query("/api/v1/health/check")
        return r.ok

    def get_user_info(self) -> DataResult:
        """获取当前用户额度/用量。"""
        return self.query("/api/v1/tikhub/user/get_user_info")

    def get_daily_usage(self) -> DataResult:
        """获取当日API用量。"""
        return self.query("/api/v1/tikhub/user/get_user_daily_usage")

    # ── TikTok ───────────────────────────────────────────

    def tiktok_search_video(self, keyword: str, count: int = 20, cursor: int = 0) -> DataResult:
        """TikTok 视频搜索。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_search_video",
            keyword=keyword, count=str(count), cursor=str(cursor),
        )

    def tiktok_search_user(self, keyword: str, count: int = 20, cursor: int = 0) -> DataResult:
        """TikTok 用户搜索。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_search_user",
            keyword=keyword, count=str(count), cursor=str(cursor),
        )

    def tiktok_user_profile(self, unique_id: str) -> DataResult:
        """TikTok 用户主页数据。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_user_profile",
            uniqueId=unique_id,
        )

    def tiktok_user_posts(self, sec_uid: str, count: int = 20, cursor: int = 0) -> DataResult:
        """TikTok 用户发布的视频列表。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_user_post",
            secUid=sec_uid, count=str(count), cursor=str(cursor),
        )

    def tiktok_video_detail(self, url: str) -> DataResult:
        """TikTok 单个视频详情。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_post_detail",
            url=url,
        )

    def tiktok_video_comments(self, aweme_id: str, count: int = 20, cursor: int = 0) -> DataResult:
        """TikTok 视频评论。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_post_comment",
            aweme_id=aweme_id, count=str(count), cursor=str(cursor),
        )

    def tiktok_trending_videos(self) -> DataResult:
        """TikTok 每日热门视频。"""
        return self.query("/api/v1/tiktok/web/fetch_trending_post")

    def tiktok_trending_keywords(self) -> DataResult:
        """TikTok 热搜词。"""
        return self.query("/api/v1/tiktok/web/fetch_trending_searchwords")

    def tiktok_hashtag_detail(self, hashtag: str) -> DataResult:
        """TikTok 话题标签详情。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_tag_detail",
            hashtag_name=hashtag,
        )

    def tiktok_hashtag_posts(self, challenge_id: str, count: int = 20, cursor: int = 0) -> DataResult:
        """TikTok 话题下的内容。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_tag_post",
            challenge_id=challenge_id, count=str(count), cursor=str(cursor),
        )

    def tiktok_explore(self, count: int = 20) -> DataResult:
        """TikTok 探索/发现页。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_explore_post",
            count=str(count),
        )

    def tiktok_keyword_suggest(self, keyword: str) -> DataResult:
        """TikTok 搜索联想词。"""
        return self.query(
            "/api/v1/tiktok/web/fetch_search_keyword_suggest",
            keyword=keyword,
        )

    # ── TikTok Shop ──────────────────────────────────────

    def tiktok_shop_product(self, product_id: str) -> DataResult:
        """TikTok Shop 商品详情。"""
        return self.query(
            "/api/v1/tiktok/shop/web/product_detail",
            product_id=product_id,
        )

    # ── Douyin (抖音) ────────────────────────────────────

    def douyin_search_video(self, keyword: str, count: int = 20, offset: int = 0) -> DataResult:
        """抖音视频搜索。"""
        return self.query(
            "/api/v1/douyin/web/fetch_search_video",
            keyword=keyword, count=str(count), offset=str(offset),
        )

    def douyin_search_user(self, keyword: str, count: int = 20, offset: int = 0) -> DataResult:
        """抖音用户搜索。"""
        return self.query(
            "/api/v1/douyin/web/fetch_search_user",
            keyword=keyword, count=str(count), offset=str(offset),
        )

    def douyin_user_profile(self, sec_user_id: str) -> DataResult:
        """抖音用户主页。"""
        return self.query(
            "/api/v1/douyin/web/fetch_user_profile",
            sec_user_id=sec_user_id,
        )

    def douyin_video_detail(self, aweme_id: str) -> DataResult:
        """抖音单视频详情。"""
        return self.query(
            "/api/v1/douyin/web/fetch_one_video",
            aweme_id=aweme_id,
        )

    def douyin_trending(self) -> DataResult:
        """抖音热搜榜。"""
        return self.query("/api/v1/douyin/web/fetch_hot_search_list")

    # ── 小红书 (Xiaohongshu / RED) ───────────────────────

    def xhs_search(self, keyword: str, page: int = 1) -> DataResult:
        """小红书搜索笔记。"""
        return self.query(
            "/api/v1/xiaohongshu/web/search_note",
            keyword=keyword, page=str(page),
        )

    def xhs_note_detail(self, note_id: str) -> DataResult:
        """小红书笔记详情。"""
        return self.query(
            "/api/v1/xiaohongshu/web/fetch_note_detail",
            note_id=note_id,
        )

    def xhs_user_profile(self, user_id: str) -> DataResult:
        """小红书用户主页。"""
        return self.query(
            "/api/v1/xiaohongshu/web/fetch_user_profile",
            user_id=user_id,
        )

    # ── Instagram ────────────────────────────────────────

    def instagram_user_profile(self, username: str) -> DataResult:
        """Instagram 用户主页。"""
        return self.query(
            "/api/v1/instagram/web/fetch_user_profile",
            username=username,
        )

    def instagram_search(self, keyword: str) -> DataResult:
        """Instagram 搜索。"""
        return self.query(
            "/api/v1/instagram/web/fetch_search",
            keyword=keyword,
        )

    # ── YouTube ──────────────────────────────────────────

    def youtube_search(self, keyword: str) -> DataResult:
        """YouTube 搜索。"""
        return self.query(
            "/api/v1/youtube/web/fetch_search",
            keyword=keyword,
        )

    def youtube_video_detail(self, video_id: str) -> DataResult:
        """YouTube 视频详情。"""
        return self.query(
            "/api/v1/youtube/web/fetch_video_detail",
            video_id=video_id,
        )
