"""饮水量查询。"""
from __future__ import annotations
from typing import Optional
from datetime import date, timedelta
import sys
from pathlib import Path
_sig = Path(__file__).parent.parent.parent / "kaisei-physiological-signals" / "queries"
sys.path.insert(0, str(_sig))
import _loader


def get_hydration(days: int = 7) -> list:
    """最近 N 天饮水量。"""
    data = _loader.get("hydration")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}):
            result.append({"date": d, **data["days"][d]})
    return result


def get_hydration_latest() -> Optional[dict]:
    data = _loader.get("hydration")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    return {"date": latest_date, **days_dict[latest_date]}


def get_hydration_summary(days: int = 7) -> dict:
    """饮水量汇总。"""
    records = get_hydration(days)
    if not records:
        return {"days_count": 0, "avg_ml": None}
    total = sum(r.get("water_ml", 0) for r in records)
    return {
        "days_count": len(records),
        "avg_ml": round(total / len(records), 1),
        "total_ml": round(total, 1),
    }
