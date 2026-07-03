---
name: kaisei-sleep-recovery
description: >
  凯圣王睡眠与恢复指标 Skill — 睡眠时长/效率/阶段（深睡/REM/core）。
  数据源：Apple Health 导出的 SleepAnalysis 段。
  挂载给：恢复睡眠教练、训练教练。
trigger:
  - "睡眠"
  - "睡眠质量"
  - "睡眠时长"
  - "深睡"
  - "REM"
  - "睡眠效率"
  - "昨晚睡得怎么样"
  - "我最近睡眠"
---

# kaisei-sleep-recovery — 凯圣王睡眠与恢复

## 数据源

`~/Documents/kaisei-data/private/sleep.json`

数据覆盖：567 天（约 1.5 年）

## 何时调用

- 用户问"昨晚睡得怎么样" → `get_sleep_latest()`
- 评估最近睡眠质量 → `get_sleep_summary(days=7)`
- 训练恢复评估 → `get_sleep(days=7)` + physiological-signals 联用

## 调用方法

```python
from queries import sleep

# 最近一晚
last = sleep.get_sleep_latest()
# → {date, in_bed_min, asleep_min, awake_min, efficiency, stages}

# 最近 7 天
recent = sleep.get_sleep(days=7)
# → [{date, in_bed_min, asleep_min, ...}, ...]

# 睡眠汇总（7 天均值）
summary = sleep.get_sleep_summary(days=7)
# → {days_count, avg_asleep_min, avg_efficiency, deep_total_min, rem_total_min, core_total_min}
```

## 状态

✅ Phase 4 完成：睡眠数据 567 天覆盖。
