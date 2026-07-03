"""Apple Health 导出 XML → 凯圣王数据根 private/ 格式转换。

输入：Apple Health 导出的 ZIP 解压后的目录（含 导出.xml）
输出：~/Documents/kaisei-data/private/*.json

用法：
  python parse_apple_health.py /path/to/apple_health_export/
  python parse_apple_health.py /path/to/apple_health_export/ --data-root /custom/path/

支持 Apple Health 导出 v14+（HealthKit Export Version 14+）。
流式解析（iterparse），不一次加载整个 XML 到内存。
"""

from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path
try:
    from lxml import etree as ET  # 宽松解析（Apple Health 导出有未严格转义的字符）
except ImportError:
    from xml.etree import ElementTree as ET


# ---------- 日期/时间工具 ----------
def parse_dt(s: str) -> datetime:
    """解析 '2022-11-07 22:45:51 +0800' 格式。"""
    s = s.strip()
    # 格式: 2022-11-07 22:45:51 +0800
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        # 兼容无时区
        return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")


def to_local_date(dt: datetime) -> date:
    return dt.date()


def to_iso_date(d: date) -> str:
    return d.isoformat()


# ---------- 主解析器 ----------
class AppleHealthParser:
    def __init__(self, xml_path: Path):
        self.xml_path = xml_path
        self.data = {
            "schema_version": "kaisei_health_v1",
            "export_source": "apple_health",
            "schema_note": "按日聚合 + 原始值由各 Skill 查询时按需返回",
            "days": defaultdict(self._empty_day),
        }
        self.workouts = []  # 锻炼记录（不按日聚合）
        self.stats = {"total_records": 0, "skipped": 0, "errors": 0}

    def _empty_day(self) -> dict:
        return {}

    def _set_day(self, d: date, **kwargs):
        key = to_iso_date(d)
        cur = self.data["days"].get(key, {})
        cur.update({k: v for k, v in kwargs.items() if v is not None})
        self.data["days"][key] = cur

    def _add_day(self, d: date, key: str, value):
        """累加型字段（步数、距离、能量等）。"""
        iso = to_iso_date(d)
        cur = self.data["days"].get(iso, {})
        cur[key] = cur.get(key, 0) + value
        self.data["days"][iso] = cur

    def parse(self) -> dict:
        print(f"开始流式解析 {self.xml_path} ...")
        print(f"文件大小: {self.xml_path.stat().st_size:,} bytes")

        # iterparse 流式处理
        for event, elem in ET.iterparse(str(self.xml_path), events=("end",)):
            tag = elem.tag
            try:
                if tag == "Record":
                    self._handle_record(elem)
                elif tag == "Workout":
                    self._handle_workout(elem)
            except Exception as e:
                self.stats["errors"] += 1
                if self.stats["errors"] <= 3:
                    print(f"  ⚠ 解析错误（{tag}）: {e}")
            finally:
                # 关键：清空 elem 释放内存
                elem.clear()

        self.data["stats"] = self.stats
        self.data["days_count"] = len(self.data["days"])
        self.data["workouts_count"] = len(self.workouts)
        self.data["workouts"] = self.workouts  # 注入供 split_outputs 用
        print(f"✓ 解析完成：{self.stats['total_records']} 条 Record, {len(self.workouts)} 个 Workout, {len(self.data['days'])} 个日期")
        if self.stats["errors"] > 0:
            print(f"  ⚠ 错误数: {self.stats['errors']}")
        return self.data

    def _handle_record(self, r: ET.Element):
        self.stats["total_records"] += 1
        type_ = r.attrib.get("type", "")
        value = r.attrib.get("value")
        unit = r.attrib.get("unit", "")
        start = r.attrib.get("startDate", "")
        end = r.attrib.get("endDate", "")
        if not start:
            return
        try:
            start_dt = parse_dt(start)
            end_dt = parse_dt(end) if end else start_dt
        except Exception:
            return

        day = to_local_date(start_dt)
        try:
            num = float(value) if value is not None else None
        except ValueError:
            num = None

        # 按 type 分发
        if type_ == "HKQuantityTypeIdentifierRestingHeartRate" and num is not None:
            self._add_rhr(day, num)
        elif type_ == "HKQuantityTypeIdentifierHeartRateVariabilitySDNN" and num is not None:
            self._add_hrv(day, num)
        elif type_ == "HKCategoryTypeIdentifierSleepAnalysis":
            self._add_sleep(day, start_dt, end_dt, value)
        elif type_ == "HKQuantityTypeIdentifierBodyMass" and num is not None:
            self._add_weight(day, num, r.attrib.get("sourceName", ""))
        elif type_ == "HKQuantityTypeIdentifierOxygenSaturation" and num is not None:
            # Apple Health 用 0-1 表示百分比，统一 × 100
            self._add_spo2(day, num * 100)
        elif type_ == "HKQuantityTypeIdentifierStepCount" and num is not None:
            self._add_day(day, "steps", int(num))
        elif type_ == "HKQuantityTypeIdentifierDistanceWalkingRunning" and num is not None:
            cur = self.data["days"].get(to_iso_date(day), {})
            cur["distance_km"] = cur.get("distance_km", 0.0) + float(num)
            self.data["days"][to_iso_date(day)] = cur
        elif type_ == "HKQuantityTypeIdentifierActiveEnergyBurned" and num is not None:
            self._add_day(day, "active_energy_kcal", float(num))
        elif type_ == "HKQuantityTypeIdentifierBasalEnergyBurned" and num is not None:
            self._add_day(day, "basal_energy_kcal", float(num))
        elif type_ == "HKQuantityTypeIdentifierAppleExerciseTime" and num is not None:
            self._add_day(day, "exercise_min", float(num))
        elif type_ == "HKQuantityTypeIdentifierFlightsClimbed" and num is not None:
            self._add_day(day, "flights_climbed", int(num))
        elif type_ == "HKQuantityTypeIdentifierAppleStandTime" and num is not None:
            self._add_day(day, "stand_minutes", float(num))
        elif type_ == "HKQuantityTypeIdentifierAppleStandHour":
            # category 1 = stood, 0 = not. value 不重要，看时段
            self._add_day(day, "stand_hours_counted", 1)
        elif type_ == "HKQuantityTypeIdentifierTimeInDaylight" and num is not None:
            self._add_day(day, "time_in_daylight_min", float(num))
        elif type_ == "HKQuantityTypeIdentifierDietaryWater" and num is not None:
            # unit 可能是 L 或 mL
            water_ml = float(num) * 1000 if unit == "L" else float(num)
            self._add_day(day, "water_ml", water_ml)
        elif type_ == "HKQuantityTypeIdentifierRespiratoryRate" and num is not None:
            self._set_day(day, respiratory_rate=num)
        elif type_ == "HKQuantityTypeIdentifierAppleWalkingSteadiness" and num is not None:
            self._set_day(day, walking_steadiness=num)
        # 其它 type 暂时忽略

    def _add_rhr(self, day: date, val: float):
        iso = to_iso_date(day)
        cur = self.data["days"].get(iso, {})
        samples = cur.get("rhr_samples", [])
        samples.append(val)
        cur["rhr_samples"] = samples
        cur["rhr"] = sum(samples) / len(samples)
        self.data["days"][iso] = cur

    def _add_hrv(self, day: date, val: float):
        iso = to_iso_date(day)
        cur = self.data["days"].get(iso, {})
        samples = cur.get("hrv_samples", [])
        samples.append(val)
        cur["hrv_samples"] = samples
        cur["hrv_sdnn_avg"] = sum(samples) / len(samples)
        cur["hrv_sdnn_min"] = min(samples)
        cur["hrv_sdnn_max"] = max(samples)
        self.data["days"][iso] = cur

    def _add_sleep(self, day: date, start: datetime, end: datetime, value: str):
        """value 形如 HKCategoryValueSleepAnalysisInBed / Asleep / Awake / AsleepDeep / AsleepREM / AsleepCore"""
        if not value:
            return
        # 睡眠段可能跨日（如 22:30 - 06:30），归属用"自然醒那天"——但用 start 日期方便聚合
        iso = to_iso_date(day)
        cur = self.data["days"].get(iso, {})
        segs = cur.setdefault("sleep_segments", [])
        segs.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "value": value,
            "duration_min": (end - start).total_seconds() / 60,
        })
        # 累计
        if value == "HKCategoryValueSleepAnalysisInBed":
            cur["sleep_in_bed_min"] = cur.get("sleep_in_bed_min", 0) + (end - start).total_seconds() / 60
        elif value == "HKCategoryValueSleepAnalysisAwake":
            cur["sleep_awake_min"] = cur.get("sleep_awake_min", 0) + (end - start).total_seconds() / 60
        elif "Asleep" in value:
            cur["sleep_asleep_min"] = cur.get("sleep_asleep_min", 0) + (end - start).total_seconds() / 60
            # 子分类
            stage_map = {
                "HKCategoryValueSleepAnalysisAsleepDeep": "deep",
                "HKCategoryValueSleepAnalysisAsleepREM": "rem",
                "HKCategoryValueSleepAnalysisAsleepCore": "core",
                "HKCategoryValueSleepAnalysisAsleepUnspecified": "unspecified",
                "HKCategoryValueSleepAnalysisAsleep": "unspecified",
            }
            stage = stage_map.get(value, "unspecified")
            cur.setdefault("sleep_stages", {})
            cur["sleep_stages"][stage] = cur["sleep_stages"].get(stage, 0) + (end - start).total_seconds() / 60
        self.data["days"][iso] = cur

    def _add_weight(self, day: date, val: float, source: str):
        iso = to_iso_date(day)
        cur = self.data["days"].get(iso, {})
        cur["weight_kg"] = val
        cur["weight_source"] = source
        self.data["days"][iso] = cur

    def _add_spo2(self, day: date, val: float):
        iso = to_iso_date(day)
        cur = self.data["days"].get(iso, {})
        samples = cur.get("spo2_samples", [])
        samples.append(val)
        cur["spo2_samples"] = samples
        cur["spo2_avg"] = sum(samples) / len(samples)
        cur["spo2_min"] = min(samples)
        self.data["days"][iso] = cur

    def _handle_workout(self, w: ET.Element):
        """处理 Workout 段（独立保存，不按日聚合到 days）。"""
        try:
            start = parse_dt(w.attrib.get("startDate", ""))
            end = parse_dt(w.attrib.get("endDate", ""))
        except Exception:
            return
        # 收集 WorkoutStatistics 子元素
        stats = {}
        for child in w:
            if child.tag == "WorkoutStatistics":
                stype = child.attrib.get("type", "")
                try:
                    sval = float(child.attrib.get("sum", "0") or "0")
                    sunit = child.attrib.get("unit", "")
                    stats[stype] = {"sum": sval, "unit": sunit}
                except ValueError:
                    pass
        self.workouts.append({
            "activity_type": w.attrib.get("workoutActivityType", ""),
            "duration_min": float(w.attrib.get("duration", "0") or "0"),
            "duration_unit": w.attrib.get("durationUnit", "min"),
            "total_distance": float(w.attrib.get("totalDistance", "0") or "0"),
            "total_distance_unit": w.attrib.get("totalDistanceUnit", ""),
            "total_energy_burned": float(w.attrib.get("totalEnergyBurned", "0") or "0"),
            "total_energy_unit": w.attrib.get("totalEnergyBurnedUnit", "kcal"),
            "source_name": w.attrib.get("sourceName", ""),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "date": to_iso_date(to_local_date(start)),
            "statistics": stats,
        })


# ---------- 后处理：填充睡眠效率、workout 注入 days ----------
def post_process(merged: dict):
    days = merged["days"]
    for iso, d in days.items():
        # 睡眠效率（clamp 到 [0, 1]）
        in_bed = d.get("sleep_in_bed_min", 0)
        asleep = d.get("sleep_asleep_min", 0)
        if in_bed > 0:
            eff = min(1.0, asleep / in_bed)
            d["sleep_efficiency"] = round(eff, 3)
        # 活跃站立小时（如果一天有 stand_hours_counted 字段，转成 stand_hours）
        if "stand_hours_counted" in d:
            d["stand_hours"] = d.pop("stand_hours_counted")
    # 注入 workout（按日）
    for w in merged.get("workouts", []):
        iso = w["date"]
        if iso in days:
            ws = days[iso].setdefault("workouts", [])
            ws.append({
                "activity_type": w["activity_type"],
                "duration_min": w["duration_min"],
                "total_distance": w["total_distance"],
                "total_distance_unit": w["total_distance_unit"],
                "total_energy_burned": w["total_energy_burned"],
                "start": w["start"],
                "end": w["end"],
            })


# ---------- 输出拆分 ----------
def split_outputs(merged: dict) -> dict:
    """按 Skill 拆分为 8 个 JSON。"""
    days = merged["days"]
    days_count = len(days)

    base = {
        "schema_version": merged["schema_version"],
        "export_source": "apple_health",
        "export_date": merged.get("stats", {}).get("export_date", ""),
        "days_count": days_count,
    }

    out = {}

    # rhr
    rhr = {**base, "days": {}}
    for iso, d in days.items():
        if "rhr" in d:
            rhr["days"][iso] = {
                "rhr": round(d["rhr"], 1),
                "rhr_samples_count": len(d.get("rhr_samples", [])),
            }
    out["rhr"] = rhr

    # hrv
    hrv = {**base, "days": {}}
    for iso, d in days.items():
        if "hrv_sdnn_avg" in d:
            hrv["days"][iso] = {
                "hrv_sdnn_avg": round(d["hrv_sdnn_avg"], 1),
                "hrv_sdnn_min": round(d.get("hrv_sdnn_min", 0), 1),
                "hrv_sdnn_max": round(d.get("hrv_sdnn_max", 0), 1),
                "hrv_samples_count": len(d.get("hrv_samples", [])),
            }
    out["hrv"] = hrv

    # sleep（保留段详情供 Skill 用）
    sleep = {**base, "days": {}}
    for iso, d in days.items():
        if "sleep_in_bed_min" in d or "sleep_asleep_min" in d:
            sleep["days"][iso] = {
                "in_bed_min": round(d.get("sleep_in_bed_min", 0), 1),
                "asleep_min": round(d.get("sleep_asleep_min", 0), 1),
                "awake_min": round(d.get("sleep_awake_min", 0), 1),
                "efficiency": d.get("sleep_efficiency"),
                "stages": d.get("sleep_stages", {}),
                "segments_count": len(d.get("sleep_segments", [])),
            }
    out["sleep"] = sleep

    # body_metrics（体重 + 来源）
    body = {**base, "days": {}}
    weights = []
    for iso, d in days.items():
        if "weight_kg" in d:
            body["days"][iso] = {
                "weight_kg": d["weight_kg"],
                "source": d.get("weight_source", ""),
            }
            weights.append((iso, d["weight_kg"]))
    if weights:
        weights.sort()
        # 去重：每个日期只保留最后一次记录
        seen_dates = {}
        for d, w in weights:
            seen_dates[d] = w  # 后者覆盖前者（同一天多次只留最后一次）
        unique_weights = sorted(seen_dates.items())
        body["first_weight_kg"] = unique_weights[0][1]
        body["first_weight_date"] = unique_weights[0][0]
        body["last_weight_kg"] = unique_weights[-1][1]
        body["last_weight_date"] = unique_weights[-1][0]
        body["weight_records_count"] = len(unique_weights)
        # 7 天均值（最近 7 个有效体重）
        recent = unique_weights[-7:]
        if recent:
            body["recent_7_avg_kg"] = round(sum(w for _, w in recent) / len(recent), 1)
    out["body_metrics"] = body

    # spo2
    spo2 = {**base, "days": {}}
    for iso, d in days.items():
        if "spo2_avg" in d:
            spo2["days"][iso] = {
                "spo2_avg": round(d["spo2_avg"], 1),
                "spo2_min": round(d.get("spo2_min", 0), 1),
                "spo2_samples_count": len(d.get("spo2_samples", [])),
            }
    out["spo2"] = spo2

    # wrist_temp（Apple Health 不直接导出）
    out["wrist_temp"] = {
        **base,
        "_note": "Apple Health 不直接导出独立的手腕温度字段。如果用户佩戴 Oura/Coro/Apple Watch Series 8+ 且授权，需用专用 API 获取。",
        "data": [],
    }

    # activity
    activity = {**base, "days": {}}
    # 先注入 workout 到 days（如果还没注入）
    for w in merged.get("workouts", []):
        iso = w["date"]
        if iso in days:
            ws = days[iso].setdefault("workouts", [])
            # 去重（同 iso + start + activity_type）
            key = (iso, w["start"], w["activity_type"])
            existing = {(ww.get("start", ""), ww.get("activity_type", "")) for ww in ws}
            if (w["start"], w["activity_type"]) not in existing:
                ws.append({
                    "activity_type": w["activity_type"],
                    "duration_min": w["duration_min"],
                    "total_distance": w["total_distance"],
                    "total_distance_unit": w["total_distance_unit"],
                    "total_energy_burned": w["total_energy_burned"],
                    "start": w["start"],
                    "end": w["end"],
                })
    for iso, d in days.items():
        if any(k in d for k in ["steps", "distance_km", "active_energy_kcal", "exercise_min", "stand_minutes", "flights_climbed", "time_in_daylight_min", "workouts"]):
            entry = {}
            if "steps" in d: entry["steps"] = int(d["steps"])
            if "distance_km" in d: entry["distance_km"] = round(d["distance_km"], 2)
            if "active_energy_kcal" in d: entry["active_energy_kcal"] = round(d["active_energy_kcal"], 1)
            if "basal_energy_kcal" in d: entry["basal_energy_kcal"] = round(d["basal_energy_kcal"], 1)
            if "exercise_min" in d: entry["exercise_min"] = round(d["exercise_min"], 1)
            if "stand_minutes" in d: entry["stand_minutes"] = round(d["stand_minutes"], 1)
            if "stand_hours" in d: entry["stand_hours"] = int(d["stand_hours"])
            if "flights_climbed" in d: entry["flights_climbed"] = int(d["flights_climbed"])
            if "time_in_daylight_min" in d: entry["time_in_daylight_min"] = round(d["time_in_daylight_min"], 1)
            if "respiratory_rate" in d: entry["respiratory_rate"] = d["respiratory_rate"]
            if "walking_steadiness" in d: entry["walking_steadiness"] = d["walking_steadiness"]
            if "workouts" in d: entry["workouts"] = d["workouts"]
            if entry:
                activity["days"][iso] = entry
    out["activity"] = activity

    # hydration
    hydration = {**base, "days": {}}
    for iso, d in days.items():
        if "water_ml" in d:
            hydration["days"][iso] = {
                "water_ml": round(d["water_ml"], 1),
            }
    out["hydration"] = hydration

    return out


# ---------- 主入口 ----------

def _sanitize_xml(xml_path: Path) -> Path:
    """预处理 XML：移除非法 XML 字符（保留到 /tmp/kaisei_sanitized_<hash>.xml）。

    Apple Health 导出的 device 字段里偶有 \x13 等非 XML 1.0 合法字符，
    lxml 会拒绝。预处理后写一个临时文件，原文件不动。
    """
    import hashlib
    h = hashlib.md5(str(xml_path).encode()).hexdigest()[:8]
    tmp_path = Path(f"/tmp/kaisei_sanitized_{h}.xml")
    if tmp_path.exists() and tmp_path.stat().st_mtime > xml_path.stat().st_mtime:
        return tmp_path  # 缓存命中

    def is_valid(c):
        code = ord(c)
        return code in (0x9, 0xA, 0xD) or (0x20 <= code <= 0xD7FF) or (0xE000 <= code <= 0xFFFD) or code >= 0x10000

    print(f"清理 XML 非法字符: {xml_path} ...")
    cleaned = 0
    with xml_path.open("rb") as fin, tmp_path.open("wb") as fout:
        while True:
            chunk = fin.read(1024 * 1024)
            if not chunk:
                break
            out = bytearray()
            i = 0
            while i < len(chunk):
                b = chunk[i]
                if b < 0x80:
                    if is_valid(chr(b)):
                        out.append(b)
                    else:
                        cleaned += 1
                    i += 1
                else:
                    if b & 0xE0 == 0xC0: end = i + 2
                    elif b & 0xF0 == 0xE0: end = i + 3
                    elif b & 0xF8 == 0xF0: end = i + 4
                    else: end = i + 1
                    try:
                        char = chunk[i:end].decode("utf-8")
                        if is_valid(char):
                            out.extend(chunk[i:end])
                        else:
                            cleaned += 1
                        i = end
                    except UnicodeDecodeError:
                        cleaned += 1
                        i += 1
            fout.write(out)
    print(f"  清理了 {cleaned} 个非法字符 → {tmp_path}")
    return tmp_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_dir", help="Apple Health 导出目录（含 导出.xml）")
    ap.add_argument("--data-root", default=str(Path.home() / "Documents" / "kaisei-data" / "private"),
                    help="输出目录（默认 ~/Documents/kaisei-data/private）")
    ap.add_argument("--xml-name", default="导出.xml", help="XML 文件名（默认 '导出.xml'）")
    args = ap.parse_args()

    src = Path(args.source_dir)
    if src.is_file():
        # 直接传了 XML 文件
        xml = src
    elif src.is_dir():
        xml = src / args.xml_name
        if not xml.exists():
            # 备选：找 *.xml
            cands = list(src.glob("*.xml"))
            if cands:
                xml = cands[0]
                print(f"⚠ 找不到 {args.xml_name}，用 {xml.name}")
            else:
                print(f"❌ 目录 {src} 中找不到 XML 文件")
                sys.exit(1)
    else:
        print(f"❌ 源路径不存在: {src}")
        sys.exit(1)

    out_dir = Path(args.data_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 检查并清理 XML（Apple Health 导出含非法 XML 字符）
    xml = _sanitize_xml(xml)

    parser = AppleHealthParser(xml)
    merged = parser.parse()
    post_process(merged)

    print("\n=== 按 Skill 拆分输出 ===")
    outputs = split_outputs(merged)

    for name, data in outputs.items():
        # 写文件
        path = out_dir / f"{name}.json"
        # dict 转字符串的 days 字段（保持 str keys）
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        days_count = data.get("days_count", 0)
        actual_days = len(data.get("days", {}))
        size = path.stat().st_size
        print(f"  ✓ {name:18s} {actual_days:4d} 天有数据  {size:>9,} bytes")

    print(f"\n所有文件已写入: {out_dir}")


if __name__ == "__main__":
    main()
