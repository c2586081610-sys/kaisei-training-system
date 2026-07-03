---
name: kaisei-movement-library
description: >
  凯圣王动作库 — 融合 PeakWatch 508 个动作（含详细描述+动画+408 条注意）和 Xunji 1092 个标准动作名。
  用于"选动作+教学"（PW）和"写回训练时按名匹配"（Xunji）。
  数据源：本地静态 JSON（peakwatch_movements_slim.json + xunji_movements_full.json）。
trigger:
  - "有什么练胸的动作"
  - "练背的动作"
  - "找一个练腿的动作"
  - "卧推有哪些变式"
  - "Xunji 标准动作名"
  - "这个动作的注意事项"
  - "动作的注意点"
  - "动作细节"
  - "中文动作名"
---

# kaisei-movement-library — 凯圣王动作库

## 两个数据源

| 数据源 | 条数 | 用途 | 字段特点 |
|---|---|---|---|
| PeakWatch 精简版 | 508 | 选动作+教学+防护 | id/code/中文名/分类/主肌群/辅肌群/器械/408 条注意/动作细节/动画 URL |
| Xunji 标准动作名 | 1092 | 写回训练时按名匹配 | seq/中文名/分类（力量/有氧/拉伸） |

## 数据流

```
用户问"有什么练胸的动作"
   ↓
search.search_movements(category='胸' or '4001')
   ↓
返回前 N 条 [{id, code, name, main_muscles, ...}, ...]
   ↓
用户选"杠铃卧推" (id=1)
   ↓
get_details.get_cautions(1) → 返回 ["身体稳定性尤为重要...", "推起至最高点时..."]
   ↓
防护教练/训练教练使用这些注意段
```

## 何时调用

- 用户问"有什么练 X 的动作" → `search_movements(category=...)`
- 用户要"找一个练 X 肌群 + 哑铃的动作" → `search_movements(main_muscle=..., equipment=...)`
- 用户问"这个动作要注意什么" → `get_cautions(id)`
- 用户要"卧推的动作细节" → `get_details(id)`
- 写回训练前不确定动作名 → `xunji_movements.is_valid_xunji_name(name)` 校验

## 调用方法

### 搜索动作

```python
from queries import search

# 按分类（中文名或 ID 都行）
chest = search.search_movements(category="胸", limit=20)  # 或 category="4001"
# → 79 条胸部动作

# 按肌群 + 器械
back_dumbbell = search.search_movements(main_muscle="背", equipment="哑铃", limit=10)
# → 背 + 哑铃的动作

# 按关键词
bench = search.search_movements(keyword="卧推", limit=20)

# 力量动作（排除有氧/康复）
strength = search.search_movements(movement_type=1, limit=50)
# 有氧/康复
cardio = search.search_movements(movement_type=3, limit=30)

# 看分类/肌群/器械字典
print(search.list_categories())  # {'4001': '胸', '4002': '背', ...}
print(search.list_muscles())     # 主肌群
print(search.list_equipments())  # 器械
```

### 取动作详情

```python
from queries import get_details

# 按 ID
m = get_details.get_movement(1)  # 杠铃卧推完整字段
# → {id, code, name, category, main_muscles, secondary_muscles,
#    equipments, targets, type, is_free, image_3d, image_thumb,
#    cautions: [...], details: [...]}

# 取注意段（防护要点）
cautions = get_details.get_cautions(1)
# → ["- 身体稳定性尤为重要...\n- 推起至最高点时..."]

# 取动作细节
details = get_details.get_details(1)
# → ["- 双脚踩实地面..."]
```

### Xunji 标准动作名（写回用）

```python
from queries import xunji_movements

# 列出所有含"卧推"的标准名
bench_names = xunji_movements.list_xunji_movements(keyword="卧推", limit=20)
# → [{"seq": 123, "name": "杠铃卧推"}, ...]

# 列出有氧类
cardio_names = xunji_movements.list_xunji_movements(category="cardio", limit=20)

# 校验某个动作名是否在 Xunji 表里
is_valid = xunji_movements.is_valid_xunji_name("杠铃卧推")
# → True

# 取写回特殊规则（休息日/有氧）
rules = xunji_movements.get_xunji_rules()
# → {"rest_day": "...", "cardio": "...", "writeback": "..."}
```

## 数据依赖

- `~/Documents/kaisei-data/static/peakwatch_movements_slim.json` — PW 精简版（508 条）
- `~/Documents/kaisei-data/static/peakwatch_config.json` — 字典
- `~/Documents/kaisei-data/static/xunji_movements_full.json` — Xunji 动作名表（1092 条）

## 状态

✅ Phase 3 完成：搜索/详情/Xunji 名表 3 大类查询实现。
