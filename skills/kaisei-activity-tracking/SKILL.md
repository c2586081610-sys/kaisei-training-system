---
name: kaisei-activity-tracking
description: >
  凯圣王活动追踪 Skill — 步数/距离/活动能量/锻炼时长/站立/爬楼/锻炼记录（workout 详情）。
  数据源：Apple Health 导出的多种活动指标 + Workout 段。
  挂载给：恢复睡眠教练、训练教练。
trigger:
  - "今天走了多少步"
  - "活动量"
  - "站立时间"
  - "今天锻炼了吗"
  - "workout"
  - "我最近练了哪些"
  - "活动汇总"
---

# kaisei-activity-tracking — 凯圣王活动追踪

## 数据源

`~/Documents/kaisei-data/private/activity.json`

数据覆盖：1352 天（约 3.7 年，含 80 个 workout 聚合到 54 天）

## 何时调用

- 评估每日活动量 → `get_activity_latest()` / `get_activity(days=7)`
- 汇总 7 天活动 → `get_activity_summary(days=7)`
- 查最近 workout 记录 → `get_workouts(days=14)`

## 调用方法

```python
from queries import activity

# 今天活动
today = activity.get_activity_latest()
# → {date, steps, distance_km, active_energy_kcal, exercise_min, stand_minutes, stand_hours, flights_climbed, workouts}

# 最近 7 天
recent = activity.get_activity(days=7)

# 7 天汇总
summary = activity.get_activity_summary(days=7)
# → {days_count, avg_steps, total_steps, total_distance_km, total_active_energy_kcal, total_exercise_min, total_flights_climbed}

# 最近 workout
workouts = activity.get_workouts(days=14)
# → [{date, activity_type, duration_min, total_energy_burned, ...}, ...]
```

## 状态

✅ Phase 4 完成：活动数据 1352 天 + 80 个 workout 覆盖。
