# 凯圣王体系蒸馏协议

本协议说明：当你从凯圣王 B 站视频蒸馏出新方法论时，**写到哪个 Skill 的哪个文件、用什么结构**。

## 适用对象

凯圣王训练/恢复/防护 3 块的体系内容（训练周期化、分化方案、康复方案等）。

营养师（`kaisei-carb-cycling`）和 Xunji/动作库类 Skill 不适用本协议——它们的数据源已经稳定。

## 蒸馏工作流

### Step 1: 确定蒸馏内容属于哪个 Skill

| 内容类型 | 目标 Skill | 目标 Agent |
|---|---|---|
| 训练周期化/分化/变量/动作选择/组次负荷 | `kaisei-training-protocols` | 训练教练 |
| 主动恢复/拉伸/瑜伽/减载/疲劳管理 | `kaisei-recovery-mobility` | 恢复教练 |
| 伤痛评估/康复/动作模式/热身/重返训练 | `kaisei-rehab-protocols` | 防护教练 |

### Step 2: 确定目标文件

每个 Skill 的 `queries/` 下有按子领域拆分的待建文件（详见各 Skill 的 SKILL.md）。新蒸馏内容写到对应文件。

### Step 3: 按规范写代码

每个文件一个核心函数，命名约定：

```python
# queries/periodization.py
def get_periodization(goal: str, experience: str, weeks: int) -> dict:
    """根据目标/经验/周数返回周期化方案。

    参数:
        goal: "增肌" / "减脂" / "力量" / "塑形"
        experience: "新手" / "进阶" / "高级"
        weeks: 周期长度（周）
    返回:
        {"phase_1": {...}, "phase_2": {...}, ...}
    """
    # 凯圣王蒸馏内容
    pass
```

### Step 4: 更新 SKILL.md

每加一个新函数，更新对应 Skill 的 `SKILL.md`：
- 在"蒸馏进度"表格里把对应子领域从 0% 改成实际进度
- 加 trigger 关键词
- 加调用方法示例

### Step 5: 更新 Agent MD

在对应 Agent MD 的"已有资料"或新加段里引用蒸馏内容。Agent MD 不再直接放蒸馏内容（避免和 Skill 重复），改为"挂载 Skill X"。

### Step 6: 触发自动提交

按 team-lead.md 的 GitHub 规则，Skill 内容更新触发自动 commit + push。

## 蒸馏内容的 4 条铁律

1. **忠于原文** — 90/10 规则，蒸馏内容必须基于凯圣王视频原话，不要混入其他体系（如 NSCA、ACSM）
2. **标注来源** — 在函数 docstring 或 SKILL.md 注明"来源：凯圣王 B 站《XXX》视频，发布时间 YYYY-MM"
3. **不确定就标"待确认"** — 视频里没讲清楚的，标 `[待确认]` 而不是猜测
4. **不编动作名/重量** — 如果视频给具体数字（如"3-4 组，每组 8-12 次"），照写；没给就标"凯圣王未指定，建议 X-Y"

## 文件结构示例

完整蒸馏后的 `kaisei-training-protocols` 应该是：

```
skills/kaisei-training-protocols/
├── SKILL.md                              # 描述、进度、调用方法
└── queries/
    ├── __init__.py
    ├── _loader.py                        # 共享内容加载（如果需要）
    ├── carb_day_matching.py              # ✅ 5%（已有）
    ├── periodization.py                  # ⏳ 蒸馏中
    ├── splits.py                         # ⏳ 蒸馏中
    ├── exercise_selection.py             # ⏳ 蒸馏中
    ├── variables.py                      # ⏳ 蒸馏中
    ├── hypertrophy_sets.py               # ⏳ 蒸馏中
    └── cardio_strategy.py                # ⏳ 蒸馏中
```

## 进度更新模板

每次蒸馏新内容时，更新 `SKILL.md` 顶部"蒸馏进度"表：

```markdown
| 子领域 | 进度 | 状态 |
|---|---|---|
| 碳日-训练匹配 | 100% | ✅ |
| 训练周期化编排 | 60% | 🟡 蒸馏中 |
| 分化方案 | 0% | ⏳ 待蒸馏 |
| ... | | |
| **总进度** | **30%** | 🟡 |
```

进度符号：
- `0%` ⏳ 待蒸馏
- `1-99%` 🟡 蒸馏中
- `100%` ✅ 完成

## 蒸馏完成后

当某个 Skill 达到 100%：
1. 移除 Agent MD 里"无资料区域"中对应条目
2. 把 Agent MD 的"可答问法"扩展
3. 更新主理人 MD 的"知识体系扩展指南"和"当前发展阶段标记"
4. 触发自动 commit + push
