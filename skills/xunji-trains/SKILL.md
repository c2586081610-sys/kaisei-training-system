---
name: xunji-trains
description: >
  训记（Xunji）训练数据 Open API 封装。读取/写回用户在训记 App 中记录的训练历史。
  数据源：远程 API（Bearer Token 鉴权）+ 本地缓存（按 datestr）+ 审计日志。
  限频：读 15s/次、含 full 30s/次、写 45s/次。
  安全：写回前 dry_run 默认 True，必须显式确认才真写。
trigger:
  - "我今天练了什么"
  - "我昨天练了什么"
  - "我上周的胸部训练"
  - "Xunji 训练历史"
  - "训记训练"
  - "记录训练"
  - "加一个训练"
  - "查训练记录"
---

# xunji-trains — 训记训练数据 API 封装

## 数据流

```
Agent → read_trains(datestr) → 缓存？→ Xunji API → 缓存 + 返回
Agent → upsert_train(trains, dry_run=True) → 摘要 → 等待用户确认
用户确认 → upsert_train(trains, dry_run=False) → Xunji API → 覆盖缓存 + 审计
```

## 何时调用

- 用户问"我 X 月 X 日练了什么"、"我最近一周的训练"、"Xunji 训练历史" → 读
- 用户要"加一个训练"、"记录今天胸部训练"、"修改昨天的训练" → 写

## 调用方法

### 兼容性说明

queries/ 下的文件用 try/except 双兼容导入（包内相对导入 + 兜底绝对导入），所以：
- ✅ 包方式：`from queries import read_trains`（推荐，Agent 内调用）
- ✅ 直接执行：`cd queries && python3 -c "import read_trains; ..."`（脚本调试）
- ⚠️ 注意：直接 `python3 read_trains.py` 会触发 RuntimeWarning，但功能正常

### 读训练

```python
from queries import read_trains

# 当天轻量
res = read_trains.read_trains("2026-07-03", include_full_data=False)
# 当天完整（含 RPE/左右侧/秒数/休息）
res = read_trains.read_trains("2026-07-03", include_full_data=True)
# 强制不走缓存
res = read_trains.read_trains("2026-07-03", force_refresh=True)
```

返回结构：
```json
{
  "success": true,
  "res": {"trains": [...]},
  "from_cache": false,
  "ts": "2026-07-03T23:35:12"
}
```

`res.trains[]` 中每条训练含 `localid`, `title`, `start`, `end`, `movements[]`。

### 写训练（必须先 dry_run）

```python
from queries import upsert_train

trains = [{
    "datestr": "2026-07-03",
    "title": "胸部训练",
    "start": 1744010000000,
    "end": 1744013600000,
    "movements": [
        {"name": "杠铃卧推", "sets": [
            {"done": True, "weight": "60", "unit": "kg", "reps": "10"}
        ]}
    ]
}]

# Step 1: dry_run 预览
preview = upsert_train.upsert_train(trains, dry_run=True)
# → {"dry_run": true, "summary": "  1. [新建] 2026-07-03 胸部训练 (1 动作: 杠铃卧推)", ...}

# Step 2: 展示给用户，等用户确认

# Step 3: 用户确认后真写
result = upsert_train.upsert_train(trains, dry_run=False)
# → {"success": true, "res": {...}, "dry_run": false}
```

### 查 Xunji 标准动作名

```python
from queries import list_standard_movements

# 全部
all_movements = list_standard_movements.list_standard_movements()
# 按关键词
bench = list_standard_movements.list_standard_movements(keyword="卧推")
# 按大类
cardio = list_standard_movements.list_standard_movements(category="cardio")
# 写回特殊规则
rules = list_standard_movements.get_rules()
```

## 写回规则（强制）

1. **dry_run 默认 True** — 必须先预览
2. **摘要必须展示** — 给用户看变更内容
3. **用户明确确认后才能真写** — 听用户的"确认"字样
4. **只传中文 name** — 不要传内部 key
5. **不确定动作名时先 list_standard_movements** — 不要凭印象写
6. **有 localid = 更新，没有 = 新建** — 不要因为缓存里没看到就删
7. **单次 ≤4 条训练、同日、每条 ≤15 动作、每动作 ≤20 组** — 超出会被服务端拒
8. **更新旧训练保留 localid/start/end** — 除非用户明确要改时间
9. **未完成组用 done:false** — 不要把 dry_run 读到的未完成组擅自删

## 限频与错误处理

- 同一接口 15-45 秒限频，Skill 内部 sleep 等待
- 错误码 `too frequent` → 等待提示的 retry 时间
- `apikey missing` / `apikey invalid` → 提示用户回 App 复制新 Key
- `仅VIP可用` → 当前账号需会员权限

## 数据依赖

- `~/Documents/kaisei-data/data.config.json` — 数据根配置
- `~/Documents/kaisei-data/secrets.json` — XUNJI_TRAINS_KEY（chmod 600）
- `~/Documents/kaisei-data/caches/trains/{datestr}.json` — 读缓存
- `~/Documents/kaisei-data/caches/trains/{datestr}_full.json` — full 读缓存
- `~/Documents/kaisei-data/static/xunji_movements_full.json` — 动作名表
- `~/Documents/kaisei-data/audit/writeback_YYYY-MM-DD.log` — 写回审计

## 状态

✅ Phase 1 完成：读、缓存、dry_run 写、真写、动作名查询全部实现。
