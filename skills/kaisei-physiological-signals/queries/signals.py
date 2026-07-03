"""生理指标查询：RHR / HRV / SpO2 / 手腕温度。

数据源：~/Documents/kaisei-data/private/{rhr,hrv,spo2,wrist_temp}.json
来源：Apple Health 导出（用 scripts/parse_apple_health.py 解析）
"""
from __future__ import annotations
from typing import Optional
from datetime import date, timedelta
import _loader


def _recent(records: dict, key: str, days: int = 7) -> list:
    """取最近 N 天有数据的记录。"""
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in records:
            result.append((d, records[d].get(key)))
    return result


def get_rhr(days: int = 7) -> list:
    """最近 N 天的静息心率。返回 [(date, rhr), ...]"""
    data = _loader.get("rhr")
    return _recent(data.get("days", {}), "rhr", days)


def get_rhr_latest() -> Optional[dict]:
    """最近一天的 RHR。"""
    data = _loader.get("rhr")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    return {"date": latest_date, **days_dict[latest_date]}


def get_hrv(days: int = 7) -> list:
    """最近 N 天的 HRV SDNN（平均/最小/最大）。返回 [{date, avg, min, max, count}, ...]"""
    data = _loader.get("hrv")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}):
            rec = data["days"][d]
            result.append({
                "date": d,
                "avg": rec.get("hrv_sdnn_avg"),
                "min": rec.get("hrv_sdnn_min"),
                "max": rec.get("hrv_sdnn_max"),
                "samples_count": rec.get("hrv_samples_count"),
            })
    return result


def get_hrv_latest() -> Optional[dict]:
    """最近一天的 HRV。"""
    data = _loader.get("hrv")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    return {"date": latest_date, **days_dict[latest_date]}


def get_spo2(days: int = 7) -> list:
    """最近 N 天的血氧。"""
    data = _loader.get("spo2")
    today = date.today()
    result = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in data.get("days", {}):
            rec = data["days"][d]
            result.append({
                "date": d,
                "avg": rec.get("spo2_avg"),
                "min": rec.get("spo2_min"),
                "samples_count": rec.get("spo2_samples_count"),
            })
    return result


def get_spo2_latest() -> Optional[dict]:
    data = _loader.get("spo2")
    days_dict = data.get("days", {})
    if not days_dict:
        return None
    latest_date = max(days_dict.keys())
    return {"date": latest_date, **days_dict[latest_date]}


def get_wrist_temp(days: int = 7) -> dict:
    """手腕温度（Apple Health 不直接导出独立字段）。"""
    data = _loader.get("wrist_temp")
    return {
        "available": False,
        "note": data.get("_note", "无数据"),
        "samples": [],
    }


def get_recovery_signals(days: int = 7) -> dict:
    """聚合恢复相关信号：RHR + HRV + SpO2（用于恢复教练综合判断）。"""
    return {
        "rhr": get_rhr(days),
        "hrv": get_hrv(days),
        "spo2": get_spo2(days),
    }
