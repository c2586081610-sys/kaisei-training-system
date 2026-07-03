"""按 ID/Code 取动作完整信息（PW 精简版的字段已含注意/动作细节）。"""

from __future__ import annotations
from typing import Union
import _loader


def get_movement(movement_id: Union[int, str]) -> dict | None:
    """按 PW 内部 ID 取完整动作字段（含 cautions / details / 图片）。"""
    target = int(movement_id) if isinstance(movement_id, str) and movement_id.isdigit() else movement_id
    for m in _loader.load_pw_slim():
        if m.get("id") == target or m.get("code") == movement_id:
            return m
    return None


def get_cautions(movement_id: Union[int, str]) -> list:
    """取动作的注意段（防护要点）。"""
    m = get_movement(movement_id)
    return m.get("cautions", []) if m else []


def get_details(movement_id: Union[int, str]) -> list:
    """取动作的动作细节段。"""
    m = get_movement(movement_id)
    return m.get("details", []) if m else []
