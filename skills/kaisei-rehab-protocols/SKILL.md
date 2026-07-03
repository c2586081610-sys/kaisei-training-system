---
name: kaisei-rehab-protocols
description: >
  凯圣王运动防护与康复 Skill（蒸馏自凯圣王 B 站防护/康复体系视频）— 伤痛评估、康复方案、动作模式矫正、关节活动度训练、重返训练评估。
  状态：⏳ 0%（骨架已建，待用户蒸馏）。
  挂载给：运动防护与康复教练（injury-rehab-expert）。
trigger:
  - "伤痛评估"
  - "康复方案"
  - "动作模式"
  - "关节活动度"
  - "重返训练"
  - "热身激活动作"
  - "肩弹响"
  - "膝盖疼"
---

# kaisei-rehab-protocols — 凯圣王运动防护与康复

## 蒸馏进度

| 子领域 | 进度 | 状态 |
|---|---|---|
| 训练伤痛评估（肩/腰/膝等） | 0% | ⏳ 待蒸馏 |
| 动作模式筛查与矫正 | 0% | ⏳ 待蒸馏 |
| 急慢性损伤康复方案 | 0% | ⏳ 待蒸馏 |
| 关节活动度与稳定性训练 | 0% | ⏳ 待蒸馏 |
| 训练前热身/激活动作设计 | 0% | ⏳ 待蒸馏 |
| 重返训练的评估标准 | 0% | ⏳ 待蒸馏 |
| **总进度** | **0%** | ⏳ |

## 临时能力（来自共享 Skill，非凯圣王体系）

在没有凯圣王体系蒸馏内容之前，防护教练可以借助：
- `kaisei-movement-library.get_details.get_cautions(id)` → 取动作的"注意"段（PW 408 条防护要点）
- `xunji-trains.read_trains(datestr, include_full_data=True)` → 评估训练频率+组次风险
- `kaisei-movement-library.search` → 筛选"高注意"动作（cautions 数量多 = 风险高）

这些能力**不属于本 Skill**，仅作过渡。严重症状仍建议就医。

## 待蒸馏内容结构

```
queries/
├── injury_assessment.py       # ⏳ 伤痛评估
├── movement_screening.py      # ⏳ 动作模式筛查
├── rehab_protocols.py         # ⏳ 急慢性损伤康复
├── joint_mobility.py          # ⏳ 关节活动度
├── warmup_activation.py       # ⏳ 热身激活动作
├── return_to_training.py      # ⏳ 重返训练评估
└── _loader.py
```

## 状态

⏳ Phase 5 骨架完成，0% 内容，等待蒸馏。
