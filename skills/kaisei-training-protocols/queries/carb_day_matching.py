"""碳日-训练匹配规则（凯圣王体系 5% 蒸馏内容）。

来源：凯圣王 B 站训练/碳水循环视频交叉内容。
覆盖：高/中/低碳日对应的训练强度、类型、时长。
"""

from __future__ import annotations
from typing import Optional

# 碳日类型枚举
CARB_DAYS = ["高", "中", "低"]
CARB_DAY_EN = {"高": "high", "中": "medium", "低": "low"}

# 核心匹配表（凯圣王体系蒸馏）
MATCHING_TABLE = {
    "高": {
        "carb_intake_g_per_kg": (3.0, 5.0),
        "intensity": "高",
        "training_type": "大重量复合训练、腿部日、容量日",
        "duration_min": (60, 90),
    },
    "中": {
        "carb_intake_g_per_kg": (2.0, 3.0),
        "intensity": "中",
        "training_type": "上肢推拉、中等容量训练",
        "duration_min": (45, 60),
    },
    "低": {
        "carb_intake_g_per_kg": (0.5, 1.5),
        "intensity": "低",
        "training_type": "有氧、核心训练、活动恢复",
        "duration_min": (30, 45),
    },
}


def match_training_to_carb_day(carb_day: str, user_weight_kg: Optional[float] = None) -> dict:
    """根据碳日返回训练匹配建议。

    参数:
        carb_day: "高" / "中" / "低"
        user_weight_kg: 用户体重（kg），用于计算具体碳水克数
    返回:
        {
            "carb_intake": "3-5g/kg" 或具体 "225-375g"（如果传了 user_weight_kg）,
            "intensity": "高",
            "training_type": "...",
            "duration": "60-90min"
        }
    """
    if carb_day not in MATCHING_TABLE:
        return {"error": f"未知的碳日: {carb_day}，应为 {CARB_DAYS} 之一"}

    row = MATCHING_TABLE[carb_day]
    carb_low, carb_high = row["carb_intake_g_per_kg"]

    result = {
        "carb_day": carb_day,
        "carb_intake": f"{carb_low}-{carb_high}g/kg",
        "intensity": row["intensity"],
        "training_type": row["training_type"],
        "duration": f"{row['duration_min'][0]}-{row['duration_min'][1]}min",
    }

    if user_weight_kg:
        c_low = carb_low * user_weight_kg
        c_high = carb_high * user_weight_kg
        result["carb_intake_grams"] = f"{c_low:.0f}-{c_high:.0f}g"
        # 增肌调整建议
        result["bulk_adjustment"] = (
            "增肌人群：可结合腰围和体重，以每公斤体重 1g 碳水向上递增"
        )
        result["cut_adjustment"] = (
            "减脂人群：晨脉向上波动 8-12 次、精神状态欠佳，可在高碳日内增加适当碳水"
        )

    return result


def get_all_carb_days() -> list:
    """列出所有碳日类型。"""
    return CARB_DAYS
