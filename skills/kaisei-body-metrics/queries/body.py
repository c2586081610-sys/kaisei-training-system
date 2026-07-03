"""身体成分查询：体重/BMI/趋势。

数据源：~/Documents/kaisei-data/private/body_metrics.json
注意：BMI/体脂 Apple Health 不直接导出（需手算或用户输入）。
"""
from __future__ import annotations
from typing import Optional
from datetime import date, timedelta
import sys
from pathlib import Path
_sig = Path(__file__).parent.parent.parent / "kaisei-physiological-signals" / "queries"
sys.path.insert(0, str(_sig))
import _loader


def get_weight_history(days: int = 90) -> list:
    """最近 N 天的体重记录。"""
    data = _loader.get("body_metrics")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}):
            rec = data["days"][d]
            result.append({
                "date": d,
                "weight_kg": rec.get("weight_kg"),
                "source": rec.get("source", ""),
            })
    return result


def get_weight_latest() -> Optional[dict]:
    data = _loader.get("body_metrics")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    rec = days_dict[latest_date]
    return {"date": latest_date, **rec}


def get_weight_trend() -> dict:
    """体重总览。"""
    data = _loader.get("body_metrics")
    return {
        "first_weight_kg": data.get("first_weight_kg"),
        "first_weight_date": data.get("first_weight_date"),
        "last_weight_kg": data.get("last_weight_kg"),
        "last_weight_date": data.get("last_weight_date"),
        "recent_7_avg_kg": data.get("recent_7_avg_kg"),
        "total_records": data.get("days_count", 0),
    }


def calc_bmi(weight_kg: float, height_m: float) -> float:
    """计算 BMI（用户需提供身高）。"""
    if height_m <= 0:
        raise ValueError("身高必须 > 0")
    return round(weight_kg / (height_m ** 2), 1)
