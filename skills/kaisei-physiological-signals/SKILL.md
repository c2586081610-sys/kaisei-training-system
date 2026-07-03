---
name: kaisei-physiological-signals
description: >
  凯圣王生理指标 Skill — 静息心率 (RHR) / 心率变异性 (HRV) / 血氧饱和度 (SpO2) / 手腕温度。
  数据源：Apple Health 导出（用 scripts/parse_apple_health.py 解析到 private/*.json）。
  挂载给：恢复睡眠教练、运动防护与康复教练、训练教练。
trigger:
  - "RHR"
  - "静息心率"
  - "HRV"
  - "心率变异性"
  - "血氧"
  - "SpO2"
  - "手腕温度"
  - "生理信号"
  - "恢复信号"
---

# kaisei-physiological-signals — 凯圣王生理指标

## 数据源

`~/Documents/kaisei-data/private/{rhr,hrv,spo2,wrist_temp}.json`

来源：Apple Health 导出 → `scripts/parse_apple_health.py` 解析。

数据覆盖（基于本次解析）：
- RHR：15 天有数据（Apple Watch 不会每天测 RHR）
- HRV SDNN：19 天
- SpO2：15 天
- 手腕温度：0 天（Apple Health 不直接导出独立字段）

## 何时调用

- 评估训练恢复状态 → `get_recovery_signals(days=7)`（聚合 RHR+HRV+SpO2）
- 监测 HRV 趋势 → `get_hrv(days=30)` / `get_hrv_latest()`
- 排查 SpO2 异常 → `get_spo2_latest()` / `get_spo2(days=7)`
- 评估训练负荷 → `get_rhr(days=7)`（晨脉监测）

## 调用方法

```python
from queries import signals

# 单指标
rhr = signals.get_rhr_latest()
hrv = signals.get_hrv_latest()
spo2 = signals.get_spo2_latest()

# 最近 N 天
rhr_7d = signals.get_rhr(days=7)
hrv_30d = signals.get_hrv(days=30)

# 聚合恢复信号
recovery = signals.get_recovery_signals(days=7)
# → {"rhr": [...], "hrv": [...], "spo2": [...]}

# 手腕温度（暂不可用）
temp = signals.get_wrist_temp(days=7)
# → {"available": False, "note": "..."}
```

## 数据依赖

- `~/Documents/kaisei-data/private/rhr.json`
- `~/Documents/kaisei-data/private/hrv.json`
- `~/Documents/kaisei-data/private/spo2.json`
- `~/Documents/kaisei-data/private/wrist_temp.json`

## 状态

✅ Phase 4 完成：4 类生理指标 Skill 实现，数据已填充。
