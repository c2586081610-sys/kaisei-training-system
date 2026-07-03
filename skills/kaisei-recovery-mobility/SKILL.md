---
name: kaisei-recovery-mobility
description: >
  凯圣王恢复与柔韧 Skill（蒸馏自凯圣王 B 站恢复/柔韧体系视频）— 主动恢复手段、拉伸方案、瑜伽流程、活动恢复、周期性减载。
  状态：⏳ 0%（骨架已建，待用户蒸馏）。
  挂载给：恢复教练（recovery-expert）。
trigger:
  - "主动恢复"
  - "拉伸"
  - "瑜伽"
  - "活动恢复"
  - "泡沫轴"
  - "周期性减载"
  - "deload"
  - "疲劳管理"
---

# kaisei-recovery-mobility — 凯圣王恢复与柔韧

## 蒸馏进度

| 子领域 | 进度 | 状态 |
|---|---|---|
| 主动恢复手段（拉伸/泡沫轴/冷热交替） | 0% | ⏳ 待蒸馏 |
| 拉伸方案（按肌群/训练日） | 0% | ⏳ 待蒸馏 |
| 瑜伽流程 | 0% | ⏳ 待蒸馏 |
| 周期性减载规划 | 0% | ⏳ 待蒸馏 |
| 训练疲劳累积管理 | 0% | ⏳ 待蒸馏 |
| 压力管理与恢复的关联 | 0% | ⏳ 待蒸馏 |
| 冷热交替/冷水浴/桑拿 | 0% | ⏳ 待蒸馏 |
| **总进度** | **0%** | ⏳ |

## 临时能力（来自共享 Skill，非凯圣王体系）

在没有凯圣王体系蒸馏内容之前，恢复教练可以借助共享 Skill：
- `kaisei-movement-library` → 查"主动恢复"类动作（拉伸/瑜伽在 PW 分类中以 `category` 区分）
- `xunji-trains` → 评估训练量/频率（疲劳累积）

这些能力**不属于本 Skill**，仅作过渡。

## 待蒸馏内容结构

```
queries/
├── active_recovery.py      # ⏳ 主动恢复手段
├── stretching.py           # ⏳ 拉伸方案
├── yoga_flows.py           # ⏳ 瑜伽流程
├── deload_planning.py      # ⏳ 周期性减载
├── fatigue_management.py   # ⏳ 疲劳累积管理
├── stress_recovery.py      # ⏳ 压力管理
├── temperature_therapy.py  # ⏳ 冷热交替
└── _loader.py
```

## 状态

⏳ Phase 5 骨架完成，0% 内容，等待蒸馏。
