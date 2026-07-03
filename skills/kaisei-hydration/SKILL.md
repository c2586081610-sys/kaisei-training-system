---
name: kaisei-hydration
description: >
  凯圣王饮水量 Skill — Apple Health 导出的 DietaryWater 记录。
  数据源：Apple Health 导出的饮水记录（7 天有数据，较稀疏）。
  挂载给：饮食营养碳循环教练、恢复睡眠教练。
trigger:
  - "喝水"
  - "饮水量"
  - "今天喝了多少水"
  - "我最近喝水"
---

# kaisei-hydration — 凯圣王饮水量

## 数据源

`~/Documents/kaisei-data/private/hydration.json`

数据覆盖：7 天有数据（稀疏，需配合手动记录或第三方 App）

## 何时调用

- 评估今日饮水量 → `get_hydration_latest()`
- 7 天饮水汇总 → `get_hydration_summary(days=7)`

## 调用方法

```python
from queries import hydration

# 今天饮水
today = hydration.get_hydration_latest()
# → {date, water_ml}

# 7 天汇总
summary = hydration.get_hydration_summary(days=7)
# → {days_count, avg_ml, total_ml}
```

## 数据稀疏说明

Apple Health 自身不会自动记录饮水，需用户在 iPhone"健康"App 手动输入或第三方 App 写入。7 天覆盖表明用户偶尔记录。

如需更密集数据，建议：
- 用训记（xunji-food）记录饮食时同步记录饮水
- 或在 iPhone 上用 WaterMinder 等 App 自动写 HealthKit

## 状态

✅ Phase 4 完成：饮水数据接入。
