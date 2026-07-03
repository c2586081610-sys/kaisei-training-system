"""列训记标准动作中文名表。

数据来源：Xunji-movements GitHub README，已同步到本地 static/xunji_movements_full.json。
缓存策略：本地读取，调用期间内存缓存一次。
"""

from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import _client

_mem_cache = {}


def _load() -> dict:
    if "data" in _mem_cache:
        return _mem_cache["data"]
    cfg = _client._load_config()
    path = Path(cfg["data_root"]) / cfg["static"]["xunji_movements"]
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    _mem_cache["data"] = data
    return data


def list_standard_movements(
    keyword: str = "",
    category: str = "",
    limit: int = 50,
) -> list:
    """
    参数:
        keyword: 关键词（动作名包含此字符串）
        category: 'cardio' / 'strength' / 'stretch' / '' 全部
        limit: 返回数量上限
    返回:
        [{'seq': int, 'name': str}, ...]
    """
    data = _load()
    movements = data["movements"]

    if category:
        cat_set = set(data["categories"].get(category, []))
        movements = [m for m in movements if m["name"] in cat_set]

    if keyword:
        kw = keyword.strip()
        movements = [m for m in movements if kw in m["name"]]

    return movements[:limit]


def get_rules() -> dict:
    """返回写回特殊训练规则（休息日/有氧）。"""
    return _load().get("rules", {})
