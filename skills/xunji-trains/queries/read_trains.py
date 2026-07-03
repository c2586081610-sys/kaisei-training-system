"""读取某一天的训练记录。

接口：POST /api_trains_for_llm_v2
默认 include_full_data=false（轻量，接近 v1）。
需要 RPE/左右侧重量/实练秒数/每组休息秒数时传 include_full_data=True。
缓存策略：按 datestr 缓存到 caches/trains/{datestr}_full.json 或 {datestr}.json。
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import _client


def read_trains(datestr: str, include_full_data: bool = False, force_refresh: bool = False) -> dict:
    """
    参数:
        datestr: YYYY-MM-DD
        include_full_data: 是否取完整数据（含 RPE/备注/左右侧/秒数/休息）
        force_refresh: True 跳过缓存直接调 API
    返回:
        {"success": bool, "res": {"trains": [...]}, "from_cache": bool, "ts": str}
    """
    cfg = _client._load_config()
    rl = cfg["rate_limits"]
    cooldown = rl["trains_read_full"] if include_full_data else rl["trains_read"]
    bucket = "trains_read_full" if include_full_data else "trains_read"

    cache_name = f"{datestr}_full.json" if include_full_data else f"{datestr}.json"
    cache_path = _client._cache_path("trains", cache_name)

    if not force_refresh:
        cached = _client._read_cache(cache_path)
        if cached is not None:
            cached["from_cache"] = True
            return cached

    body = {
        "schema_version": "train_open_api_v2",
        "datestr": datestr,
        "include_full_data": include_full_data,
    }
    resp = _client.call_trains("/api_trains_for_llm_v2", body, cooldown=cooldown, bucket=bucket)

    # Xunji 训练 API 成功判定：返回 dict 含 "res" 字段
    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        payload = {
            "success": True,
            "res": resp["res"],
            "from_cache": False,
            "ts": _client.datetime.now().isoformat(),
        }
        _client._write_cache(cache_path, payload)
        return payload
    # 失败：透出错误
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp
