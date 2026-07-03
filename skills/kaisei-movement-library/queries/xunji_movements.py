"""Xunji 标准动作名（1092 个），用于写回训练时按名匹配。

注：Xunji 动作库与 PW 动作库是两个独立数据源：
- PW 508 条：含详细描述+动画+多语言，用于"选动作+教学"
- Xunji 1092 条：含标准中文名，用于"写回训记时按名匹配"
"""

from __future__ import annotations
from typing import Optional
import _loader


def list_xunji_movements(keyword: str = "", category: str = "", limit: int = 50) -> list:
    """
    参数:
        keyword: 关键词
        category: 'cardio' / 'strength' / 'stretch' / '' 全部
    """
    data = _loader.load_xunji_movements()
    movements = data["movements"]

    if category:
        cat_set = set(data["categories"].get(category, []))
        movements = [m for m in movements if m["name"] in cat_set]

    if keyword:
        movements = [m for m in movements if keyword in m["name"]]

    return movements[:limit]


def get_xunji_rules() -> dict:
    """返回写回特殊训练规则（休息日/有氧）。"""
    return _loader.load_xunji_movements().get("rules", {})


def is_valid_xunji_name(name: str) -> bool:
    """校验某个中文名是否在 Xunji 动作名表里。"""
    if not name:
        return False
    data = _loader.load_xunji_movements()
    return any(m["name"] == name for m in data["movements"])
