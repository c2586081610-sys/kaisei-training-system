"""查询饮食记录。

接口：POST /open/food/query_gzip
参数：start_date, end_date, include_detail
缓存策略：按 (start_date, end_date, include_detail) hash 缓存。
限制：过去 1 年 ~ 未来 3 个月。
"""

from __future__ import annotations
import hashlib
from pathlib import Path
import _client


def _cache_key(start: str, end: str, include_detail: bool) -> str:
    raw = f"{start}_{end}_{include_detail}"
    h = hashlib.md5(raw.encode()).hexdigest()[:8]
    return f"{start}_to_{end}_{h}.json"


def query_food(start_date: str, end_date: str, include_detail: bool = True, force_refresh: bool = False) -> dict:
    """
    参数:
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        include_detail: True 返回每条食物详细，False 仅汇总
        force_refresh: True 跳过缓存
    返回:
        {"success": bool, "res": {...}, "from_cache": bool}
    """
    err = _client.validate_date_range(start_date, end_date)
    if err:
        return {"success": False, "error": "date_range", "detail": err}

    cache_path = _client._cache_path(_cache_key(start_date, end_date, include_detail))
    if not force_refresh:
        cached = _client._read_cache(cache_path)
        if cached is not None:
            cached["from_cache"] = True
            return cached

    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["food_all"]
    body = {
        "start_date": start_date,
        "end_date": end_date,
        "include_detail": include_detail,
    }
    resp = _client.call_food("/open/food/query_gzip", body, cooldown=cooldown, bucket="food_query")

    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        payload = {
            "success": True,
            "res": resp["res"],
            "from_cache": False,
        }
        _client._write_cache(cache_path, payload)
        return payload
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp
