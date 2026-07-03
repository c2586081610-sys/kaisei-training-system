---
name: kaisei-body-metrics
description: >
  凯圣王身体成分 Skill — 体重/BMI/趋势。
  数据源：Apple Health 导出的 BodyMass 记录（43 天有数据）。
  挂载给：训练教练、饮食营养碳循环教练。
trigger:
  - "体重"
  - "BMI"
  - "体脂"
  - "身体成分"
  - "我最近体重"
  - "体重趋势"
---

# kaisei-body-metrics — 凯圣王身体成分

## 数据源

`~/Documents/kaisei-data/private/body_metrics.json`

数据覆盖：43 天体重记录（来自"健康"App、"好轻"、"薄荷健康"等多来源）

## 何时调用

- 碳循环计算需要体重 → `get_weight_latest()`
- 体重趋势分析 → `get_weight_trend()` / `get_weight_history(days=90)`
- 评估减脂/增肌进展 → `get_weight_history(days=30)` 配合 xunji-food

## 调用方法

```python
from queries import body

# 最新体重
latest = body.get_weight_latest()
# → {date, weight_kg, source}

# 体重历史
hist = body.get_weight_history(days=90)

# 趋势总览
trend = body.get_weight_trend()
# → {first_weight_kg, last_weight_kg, recent_7_avg_kg, total_records}

# BMI 计算（需提供身高）
bmi = body.calc_bmi(weight_kg=75, height_m=1.78)
```

## 注意

- BMI/体脂 Apple Health 不直接导出，本 Skill 暂不覆盖
- 如需 BMI/体脂，需用户提供身高 + 手动测量数据

## 状态

✅ Phase 4 完成：体重数据 43 天覆盖。
