"""搜索食物（官方食物库）。

接口：POST /open_agent/food/search_gzip
鉴权：XUNJI_FOOD_SEARCH_KEY（不是 XUNJI_FOOD_KEY）
返回 res.foods[]（含 ntr/units/uniquekey）和 res.d[]（压缩格式）。
"""

from __future__ import annotations
import _client


def search_food(keyword: str, limit: int = 8) -> dict:
    """
    参数:
        keyword: 搜索词
        limit: 返回数量上限（默认 8）
    返回:
        {"success": bool, "res": {"foods": [...], "d": [...]}}
    """
    if not keyword or not keyword.strip():
        return {"success": False, "error": "missing_keyword"}

    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["food_all"]
    body = {"keyword": keyword.strip(), "limit": limit}
    resp = _client.call_food(
        "/open_agent/food/search_gzip", body,
        cooldown=cooldown, bucket="food_search",
        use_search_key=True,
    )

    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        return {"success": True, "res": resp["res"], "keyword": keyword, "limit": limit}
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp
