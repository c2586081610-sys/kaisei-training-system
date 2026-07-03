"""活动追踪查询：步数/距离/能量/站立/爬楼/锻炼。"""
from __future__ import annotations
from typing import Optional
from datetime import date, timedelta
import sys
from pathlib import Path
_sig = Path(__file__).parent.parent.parent / "kaisei-physiological-signals" / "queries"
sys.path.insert(0, str(_sig))
import _loader


def get_activity(days: int = 7) -> list:
    """最近 N 天活动。返回 [{date, steps, distance_km, active_energy_kcal, ...}, ...]"""
    data = _loader.get("activity")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}):
            result.append({"date": d, **data["days"][d]})
    return result


def get_activity_latest() -> Optional[dict]:
    data = _loader.get("activity")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    return {"date": latest_date, **days_dict[latest_date]}


def get_workouts(days: int = 14) -> list:
    """最近 N 天有 workout 的日期 + workout 详情。"""
    data = _loader.get("activity")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}) and data["days"][d].get("workouts"):
            for w in data["days"][d]["workouts"]:
                result.append({"date": d, **w})
    return result


def get_activity_summary(days: int = 7) -> dict:
    """活动汇总。"""
    records = get_activity(days)
    if not records:
        return {"days_count": 0}
    total_steps = sum(r.get("steps", 0) or 0 for r in records)
    total_distance = sum(r.get("distance_km", 0) or 0 for r in records)
    total_energy = sum(r.get("active_energy_kcal", 0) or 0 for r in records)
    total_exercise = sum(r.get("exercise_min", 0) or 0 for r in records)
    total_flights = sum(r.get("flights_climbed", 0) or 0 for r in records)
    return {
        "days_count": len(records),
        "avg_steps": round(total_steps / len(records)),
        "total_steps": total_steps,
        "total_distance_km": round(total_distance, 1),
        "total_active_energy_kcal": round(total_energy),
        "total_exercise_min": round(total_exercise),
        "total_flights_climbed": total_flights,
    }
