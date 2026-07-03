---
name: kaisei-training-protocols
description: >
  凯圣王训练协议 Skill（蒸馏自凯圣王 B 站训练体系视频）— 周期化编排、分化方案、变量调控、动作选择与进退阶。
  状态：⏳ 5%（仅含碳日-训练匹配规则）。其余 95% 待用户继续蒸馏。
  挂载给：训练教练（training-expert）。
trigger:
  - "训练周期"
  - "分化方案"
  - "PPL"
  - "上下肢分化"
  - "五分化"
  - "训练变量"
  - "组次次数"
  - "动作选择"
  - "卧推怎么突破"
  - "平台期"
---

# kaisei-training-protocols — 凯圣王训练协议

## 蒸馏进度

| 子领域 | 进度 | 状态 |
|---|---|---|
| 碳日-训练匹配 | 5% | ✅ 已有（见下） |
| 训练周期化编排（增肌/减脂/力量周期） | 0% | ⏳ 待蒸馏 |
| 分化训练方案（PPL/上下肢/五分化） | 0% | ⏳ 待蒸馏 |
| 动作选择与进退阶策略 | 0% | ⏳ 待蒸馏 |
| 训练变量调控（容量/强度/频率/间歇） | 0% | ⏳ 待蒸馏 |
| 增肌训练的具体组次负荷方案 | 0% | ⏳ 待蒸馏 |
| 减脂训练的有氧安排和强度策略 | 0% | ⏳ 待蒸馏 |
| **总进度** | **约 5%** | ⏳ |

## 已有内容：碳日-训练匹配规则

来源：凯圣王 B 站视频（蒸馏自 kaisei-carb-cycling Skill 关联内容）

| 碳日 | 碳水摄入参考 | 训练强度 | 训练类型 | 时长建议 |
|------|------------|---------|---------|---------|
| 高碳日 | 3-5g/kg | 高 | 大重量复合训练、腿部日、容量日 | 60-90min |
| 中碳日 | 2-3g/kg | 中 | 上肢推拉、中等容量训练 | 45-60min |
| 低碳日 | 0.5-1.5g/kg | 低 | 有氧、核心训练、活动恢复 | 30-45min |

> 增肌人群：可结合腰围和体重，以每公斤体重 1g 碳水向上递增。
> 减脂人群：晨脉向上波动 8-12 次、精神状态欠佳，可在高碳日内增加适当碳水。

## 待蒸馏内容结构

新增蒸馏内容时按以下子领域分文件存放：

```
queries/
├── carb_day_matching.py        # ✅ 碳日-训练匹配（已有）
├── periodization.py            # ⏳ 周期化编排
├── splits.py                   # ⏳ 分化方案
├── exercise_selection.py       # ⏳ 动作选择与进退阶
├── variables.py                # ⏳ 训练变量调控
├── hypertrophy_sets.py         # ⏳ 增肌组次负荷
├── cardio_strategy.py          # ⏳ 减脂有氧策略
└── _loader.py                  # 共享内容加载器
```

每个文件一个核心函数，签名示例：

```python
# queries/periodization.py
def get_periodization(goal: str, experience: str, weeks: int) -> dict:
    """返回周期化方案（按目标和周数）。"""
    # 待蒸馏内容
    pass
```

具体协议见 `docs/distillation-protocol.md`。

## 调用方法

```python
from queries import carb_day_matching

# 碳日-训练匹配（当前唯一可用）
match = carb_day_matching.match_training_to_carb_day("高", user_weight_kg=75)
# → {"carb_intake": "3-5g/kg", "intensity": "高", "type": "大重量复合", "duration": "60-90min"}
```

## 知识来源

- 凯圣王 B 站训练体系视频（蒸馏中，进度 5%）
- 间接引用：`kaisei-carb-cycling` Skill 中的碳日-训练匹配段

## 数据依赖

无需外部数据源。蒸馏内容以代码/常量形式内嵌于 `queries/*.py`。

## 状态

⏳ Phase 5 骨架完成，5% 归位，等待继续蒸馏。
