"""睡眠数据查询。"""
from __future__ import annotations
from typing import Optional
from datetime import date, timedelta
import sys
from pathlib import Path

# 复用 physiological-signals 的 _loader
_sig = Path(__file__).parent.parent.parent / "kaisei-physiological-signals" / "queries"
sys.path.insert(0, str(_sig))
import _loader


def get_sleep(days: int = 7) -> list:
    """最近 N 天睡眠。返回 [{date, in_bed_min, asleep_min, awake_min, efficiency, stages}, ...]"""
    data = _loader.get("sleep")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}):
            rec = data["days"][d]
            result.append({
                "date": d,
                "in_bed_min": rec.get("in_bed_min"),
                "asleep_min": rec.get("asleep_min"),
                "awake_min": rec.get("awake_min"),
                "efficiency": rec.get("efficiency"),
                "stages": rec.get("stages", {}),
            })
    return result


def get_sleep_latest() -> Optional[dict]:
    """最近一晚的睡眠。"""
    data = _loader.get("sleep")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    rec = days_dict[latest_date]
    return {
        "date": latest_date,
        "in_bed_min": rec.get("in_bed_min"),
        "asleep_min": rec.get("asleep_min"),
        "awake_min": rec.get("awake_min"),
        "efficiency": rec.get("efficiency"),
        "stages": rec.get("stages", {}),
    }


def get_sleep_summary(days: int = 7) -> dict:
    """睡眠汇总：平均时长/平均效率/平均深睡比例。"""
    records = get_sleep(days)
    if not records:
        return {"days_count": 0, "avg_asleep_min": None, "avg_efficiency": None}
    avg_asleep = sum(r["asleep_min"] or 0 for r in records) / len(records)
    avg_eff = sum(r["efficiency"] or 0 for r in records) / len(records)
    deep_total = sum((r["stages"] or {}).get("deep", 0) for r in records)
    rem_total = sum((r["stages"] or {}).get("rem", 0) for r in records)
    core_total = sum((r["stages"] or {}).get("core", 0) for r in records)
    return {
        "days_count": len(records),
        "avg_asleep_min": round(avg_asleep, 1),
        "avg_efficiency": round(avg_eff, 3),
        "deep_total_min": round(deep_total, 1),
        "rem_total_min": round(rem_total, 1),
        "core_total_min": round(core_total, 1),
    }
