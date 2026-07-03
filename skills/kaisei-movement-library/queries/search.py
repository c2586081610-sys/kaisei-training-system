"""搜索动作。

支持：
- 按 PW 分类（胸/背/腿/肩/臂/核心/有氧/HIIT/拳击/拉伸/瑜伽/搏击/超级组 等）
- 按主肌群 / 辅肌群（肌群 ID 如 1001=上胸）
- 按器械（5001=哑铃/5002=杠铃/...）
- 按关键词（动作中文名）
- 训练目标类型（力量/有氧/计时）
- 联合过滤
"""

from __future__ import annotations
from typing import Optional
import _loader


def search_movements(
    category: Optional[str] = None,
    main_muscle: Optional[str] = None,
    equipment: Optional[str] = None,
    keyword: Optional[str] = None,
    movement_type: Optional[int] = None,
    is_free: Optional[bool] = None,
    limit: int = 50,
) -> list:
    """
    参数:
        category: PW 分类 ID 如 '4001'=胸 / '4002'=背 / '4003'=腿（也可传中文名查）
        main_muscle: 肌群 ID 如 '1001'=上胸 / '1101'=上背
        equipment: 器械 ID 如 '5001'=哑铃 / '5002'=杠铃 / '5008'=自重
        keyword: 关键词（动作中文名包含此字符串）
        movement_type: 1=力量, 3=有氧/康复/计时
        is_free: True 只看免费动作
        limit: 返回数量上限
    返回:
        动作字典列表（精简版字段）
    """
    movements = _loader.load_pw_slim()
    cfg = _loader.load_pw_config()

    # category 可以传 ID 或中文名（自动转换）
    if category:
        # 优先当 ID
        if category not in {c for c in cfg["body_parts"]}:
            # 当中文名找 ID
            for k, v in cfg["body_parts"].items():
                if v == category:
                    category = k
                    break

    if main_muscle:
        if main_muscle not in set(cfg["muscles"]):
            # 先按肌群字典查
            found = False
            for k, v in cfg["muscles"].items():
                if v == main_muscle:
                    main_muscle = k
                    found = True
                    break
            if not found:
                # 再按大部位字典查（fall-through）— 大部位映射到 category，清空 main_muscle 避免双重过滤
                for k, v in cfg["body_parts"].items():
                    if v == main_muscle:
                        category = k
                        main_muscle = None
                        break

    if equipment:
        if equipment not in {c for c in cfg["equipments"]}:
            for k, v in cfg["equipments"].items():
                if v == equipment:
                    equipment = k
                    break

    results = []
    for m in movements:
        if category and m.get("category") != category:
            continue
        if main_muscle and main_muscle not in m.get("main_muscles", []):
            continue
        if equipment and equipment not in m.get("equipments", []):
            continue
        if movement_type is not None and m.get("type") != movement_type:
            continue
        if is_free is not None and m.get("is_free") != is_free:
            continue
        if keyword and keyword not in m.get("name", ""):
            continue
        results.append(m)
        if len(results) >= limit:
            break
    return results


def list_categories() -> dict:
    """返回训练部位字典。"""
    return _loader.load_pw_config()["body_parts"]


def list_muscles() -> dict:
    """返回主肌群字典。"""
    return _loader.load_pw_config()["muscles"]


def list_equipments() -> dict:
    """返回器械字典。"""
    return _loader.load_pw_config()["equipments"]
