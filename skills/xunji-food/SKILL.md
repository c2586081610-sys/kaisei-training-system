---
name: xunji-food
description: >
  训记（Xunji）饮食数据 Open API 封装。读取/搜索/写回用户在训记 App 中记录的饮食。
  数据源：远程 API（Bearer Token 鉴权）+ 本地缓存（按查询条件 hash）+ 审计日志。
  鉴权：查询/写回用 XUNJI_FOOD_KEY；搜索用 XUNJI_FOOD_SEARCH_KEY。
  限频：所有接口 15s/次。
  安全：写回前 dry_run 默认 True，必须显式确认才真写。
  范围：过去 1 年 ~ 未来 3 个月。
trigger:
  - "我今天吃了什么"
  - "我昨天吃了什么"
  - "Xunji 饮食历史"
  - "训记饮食"
  - "查饮食记录"
  - "搜食物"
  - "记录饮食"
  - "加一个食物"
  - "套用饮食模板"
---

# xunji-food — 训记饮食数据 API 封装

## 6 个接口

| 接口 | 用途 | 鉴权 Key |
|---|---|---|
| `query_food` | 查询某日期范围饮食 | XUNJI_FOOD_KEY |
| `search_food` | 搜索官方食物库 | XUNJI_FOOD_SEARCH_KEY |
| `upsert_food` | 写回饮食记录 | XUNJI_FOOD_KEY |
| `upsert_custom_food` | 新增/更新自定义食物 | XUNJI_FOOD_KEY |
| `list_templates` | 查询饮食模板 | XUNJI_FOOD_KEY |
| `apply_template` | 套用饮食模板 | XUNJI_FOOD_KEY |

## 数据流

```
Agent → search_food("鸡蛋") → Xunji 食物库 → 返回 uniquekey + ntr
Agent → upsert_food(..., dry_run=True) → 摘要 → 等待用户确认
用户确认 → upsert_food(..., dry_run=False) → Xunji 写回 + 覆盖缓存 + 审计
```

## 何时调用

- 用户问"我 X 月 X 日吃了什么" → `query_food`
- 用户要"加一个鸡蛋"、"记录午餐" → 先 `search_food` 拿 uniquekey，再 `upsert_food`
- 用户要"创建自定义食物" → `upsert_custom_food`
- 用户要"套用我的高碳日模板" → 先 `list_templates` 找 ID，再 `apply_template`

## 调用方法

### 搜索食物

```python
from queries import search_food
res = search_food.search_food("鸡蛋", limit=8)
# res.foods[] 每项含 name, uniquekey, ntr{cal, protein, fat, carb}, units
```

### 查询饮食

```python
from queries import query_food
res = query_food.query_food("2026-07-01", "2026-07-03", include_detail=True)
```

### 写饮食（必须先 dry_run）

```python
from queries import search_food, upsert_food

# Step 1: 搜食物拿 uniquekey
search = search_food.search_food("鸡蛋")
egg = search["res"]["foods"][0]  # 取第一条
uniquekey = egg["uniquekey"]
ntr = egg["ntr"]

# Step 2: 构造写入参数
foods = [{
    "date": "2026-07-03",
    "meal_type": "lunch",
    "name": egg["name"],
    "amount": 100,
    "unit": "g",
    "uniquekey": uniquekey,
    "ntr": ntr,
}]

# Step 3: dry_run 预览
preview = upsert_food.upsert_food(foods, dry_run=True)
# → {"dry_run": true, "summary": "  1. [2026-07-03 lunch] 鸡蛋 100g (key=xxx)", ...}

# Step 4: 用户确认后真写
result = upsert_food.upsert_food(foods, dry_run=False)
```

### 创建自定义食物

```python
from queries import upsert_custom_food
food = {
    "name": "用户确认的食物名",
    "ntr": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0, "foodpic": ""},
    "units": [{"unit": "份", "count": "1", "gram": 100}],
}
preview = upsert_custom_food.upsert_custom_food(food, dry_run=True)
# → 等用户确认
result = upsert_custom_food.upsert_custom_food(food, dry_run=False)
```

### 套用模板

```python
from queries import templates

# 列出模板
ts = templates.list_templates()
# ts.res.templates[]

# 套用
preview = templates.apply_template("template_id_123", "2026-07-03", "lunch", dry_run=True)
result = templates.apply_template("template_id_123", "2026-07-03", "lunch", dry_run=False)
```

## 写回规则（强制）

1. **dry_run 默认 True** — 必须先预览
2. **摘要必须展示** — 给用户看变更内容
3. **用户明确确认后才能真写** — 听用户的"确认"字样
4. **官方食物必须先 search 拿 uniquekey** — 不要凭印象写
5. **ntr 必须是用户确认的** — 写回接口不会替你猜营养
6. **不要因为查询结果里缺少旧记录就删除旧记录** — 除非用户明确要求

## 限频与错误处理

- 所有接口 15s 限频
- 错误码 `too frequent` → 等待提示的 retry 时间
- `apikey missing` / `apikey invalid` → 提示用户回 App 复制新 Key
- `仅VIP可用` → 当前账号需会员权限
- 日期范围错误 → 拆分到允许范围（过去 1 年 ~ 未来 3 个月）

## 数据依赖

- `~/Documents/kaisei-data/data.config.json` — 数据根配置
- `~/Documents/kaisei-data/secrets.json` — XUNJI_FOOD_KEY + XUNJI_FOOD_SEARCH_KEY
- `~/Documents/kaisei-data/caches/foods/{start}_to_{end}_{hash}.json` — 查询缓存
- `~/Documents/kaisei-data/audit/writeback_YYYY-MM-DD.log` — 写回审计

## 状态

✅ Phase 2 完成：6 个接口全部实现，含限频、缓存、dry_run。
