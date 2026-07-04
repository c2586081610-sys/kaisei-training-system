# 5 Agent 第一性原理扩展方案

> 基于第一性原理（First Principles Thinking）分析凯圣王专家团的扩展空间。
> 生成日期：2026-07-04
> 适用版本：当前 12-Skill / 5-Agent 体系

## 第一性原理

**健身的本质**：

```
身体变化 = 训练刺激(输入) - 疲劳累积(消耗) + 营养补充(原料) + 恢复质量(修复)
```

要让这个公式**对你有效**，决策需要 **5 类信息**：

| 类别 | 决定什么 |
|---|---|
| **1. 你是谁** | 个性化一切（目标/伤病/装备/历史） |
| **2. 你在做什么** | 训练/饮食/活动（输入） |
| **3. 你身体反应** | 生理/恢复（消耗与修复） |
| **4. 进展如何** | 时序趋势 |
| **5. 下一步该做什么** | 智能决策 |

按这 5 类信息去查缺补漏，比"按模块凑功能"更系统。

## 现状与缺口

| 类别 | 现有 | 缺什么 | 紧迫度 |
|---|---|---|:---:|
| **1. 你是谁** | 零 | 目标/伤病/装备/个人记录/年龄/性别 全部没建档 | 🔴 P0 |
| **2. 你在做什么** | 训记 + Apple Health | ✅ 基本完整 | — |
| **3. 你身体反应** | RHR/HRV/睡眠/SpO2/活动 | ✅ 基本完整 | — |
| **4. 进展如何** | 部分（Apple Health 趋势/体重） | 训练容量/渐进超负荷/异常检测 都没有 | 🟡 P0 |
| **5. 下一步** | 碳循环 + 动作推荐 | 排程/薄弱点/营养缺口/心率区间/异常预警 都没有 | 🟡 P0-P2 |

**最大缺口在「1 你是谁」和「4-5 进展与决策」**。

## 设计方案：1 个新 Agent + 9 个 Skill

### 新增 Agent：目标追踪师（goal-tracker-expert）

**为什么单独建 Agent**？

目标管理横跨训练/营养/恢复/防护 4 个维度，是**元层能力**——它不解决具体问题，而是**协调 4 个 Agent 围绕用户的目标**。这跟主理人"调度编排"是不同维度：

| | 主理人 | 目标追踪师 |
|---|---|---|
| 职责 | 一次任务的 SOP 调度 | 长期目标的拆解与追踪 |
| 时间维度 | 单次对话 | 跨周/跨月 |
| 颗粒度 | "今天练什么" | "8 周后要达成什么" |
| 输出形式 | 汇编 4 个 Agent 的产出 | 目标进度报告 + 调整建议 |

**配置**：

```yaml
name: goal-tracker-expert
displayName:
  en: "Goal Coach"
  zh: "目标追踪师"
profession: Goal Tracking Specialist
maxTurns: 50
skills: [user-profile, volume-analyzer, progression-tracker, anomaly-detector, achievement-tracker]
```

### 9 个 Skill（按"你是谁 / 进展 / 决策"3 类组织）

#### 类别 1：你是谁（地基）

**`user-profile` Skill**（挂给 5 个 Agent + 目标追踪师）

数据文件：`~/Documents/kaisei-data/profile/user_profile.json`

字段结构：
```json
{
  "schema_version": "kaisei_profile_v1",
  "basics": {
    "age": 32,
    "sex": "male",
    "height_cm": 178,
    "occupation": "office",
    "timezone": "Asia/Shanghai"
  },
  "goals": {
    "primary": "增肌",
    "targets": {
      "weight_kg": 78,
      "body_fat_pct": 15,
      "bench_1rm_kg": 100,
      "squat_1rm_kg": 140
    },
    "timeline_weeks": 8,
    "deadline": "2026-09-01"
  },
  "history": {
    "training_years": 3,
    "injuries": [
      {"area": "右肩", "type": "肩袖损伤", "year": 2024, "recovered": true}
    ],
    "chronic_conditions": [],
    "medications": []
  },
  "equipment": {
    "home": ["哑铃", "弹力带", "瑜伽垫"],
    "gym": ["杠铃", "哑铃", "绳索", "器械全套"]
  },
  "preferences": {
    "training_time": "morning",
    "available_days_per_week": 4,
    "session_duration_min": 60,
    "disliked_foods": ["苦瓜"]
  },
  "personal_records": {
    "bench_1rm_kg": 85,
    "squat_1rm_kg": 120,
    "deadlift_1rm_kg": 140,
    "ohp_1rm_kg": 55
  }
}
```

**采集方式**：
- 首次使用由主理人通过对话分 2-3 轮收集
- 或者用户直接给我一份（更快）
- 后续可修改

**所有其他 Skill 都依赖 user-profile**——没有它，"个性化"无从谈起。

---

#### 类别 2：进展分析（progress layer）

**`volume-analyzer` Skill**（挂给训练 + 目标追踪师）

基于 xunji-trains 拉数据，按肌群/动作/周聚合训练容量：

```python
def get_weekly_volume_per_muscle(weeks=8) -> dict:
    """返回 {week: {muscle: total_sets}}"""
    # 推荐基准（增肌）: 10-20 组/肌群/周（Mike Israetel）
    # 减脂维持: 6-8 组/肌群/周
    # 输出: 红黄绿（低于/达标/过度）

def get_weekly_volume_per_action(weeks=8) -> dict:
    """动作级容量（用于判断过度专项化）"""
```

**`progression-tracker` Skill**（挂给训练 + 目标追踪师）

```python
def get_action_progression(action_name, weeks=12) -> list:
    """返回动作的力量进展（top set 重量/次数/估算 1RM）"""
    # 1RM 估算: weight * (1 + reps/30)  # Epley 公式

def detect_plateau(action_name, weeks=4) -> bool:
    """4 周内 1RM 进展 < 2.5% → 平台期"""

def get_pr_history() -> list:
    """所有动作的 1RM 历史 PR"""
```

**`anomaly-detector` Skill**（挂给恢复 + 防护 + 目标追踪师）

多信号融合检测：

```python
def check_training_overload(lookback_days=14) -> dict:
    """训练过度检测：
    - 训练容量周环比 +20%+
    - RHR 7 天均值 +5 bpm
    - HRV 7 天均值 -10%
    - 睡眠效率 < 85% 持续 3 天
    触发: 4 项中 3 项异常 → 红色警告"""

def check_injury_risk() -> dict:
    """伤痛风险：
    - 同一肌群训练频率 > 5 次/周
    - 主观 RPE 持续 > 9
    - 训练容量突增
    - HRV 突然下降"""
```

**`achievement-tracker` Skill**（挂给目标追踪师）

```python
def check_milestones() -> list:
    """检测里程碑：
    - 1RM 突破整数（100/120/140kg）
    - 训练连续天数（30/60/100/365）
    - 体重/体脂达到目标值
    - 完成首次双倍体重深蹲等"""
```

---

#### 类别 3：决策智能（decision layer）

**`nutrition-gap` Skill**（挂给营养教练）

```python
def get_nutrition_gap(date: str) -> dict:
    """对比目标 vs 实际：
    - 蛋白质缺口（实际 g - 目标 g/kg 体重）
    - 碳水缺口（按碳日类型）
    - 脂肪缺口
    - 热量缺口
    - 连续 3 天 < 目标 80% 警告"""

def get_weekly_macro_summary() -> dict:
    """本周宏量营养素平均 vs 目标"""
```

**`heart-rate-zones` Skill**（挂给训练 + 防护）

```python
def calculate_zones(age, rhr=60) -> dict:
    """Karvonen 公式：HRR = max_hr - rhr
    Zone 1-5 = (HRR × % + rhr)"""

def analyze_workout_hr_zones(workout_data) -> dict:
    """分析 workout 中心率在各区间的时长占比"""

def get_weekly_zone_distribution(weeks=4) -> dict:
    """周度心率区间分布（判断是否过度有氧/无氧）"""
```

**`weakness-analyzer` Skill**（挂给训练 + 防护）

```python
def detect_strength_imbalance() -> dict:
    """左右肌力不平衡：推类（卧推+OHP+推举）vs 拉类（划船+引体+下拉）推荐 1:1"""

def detect_volume_imbalance() -> dict:
    """训练容量不平衡：上肢 vs 下肢"""

def detect_neglected_muscles(days=30) -> list:
    """30 天内训练量 < 5 组的肌群"""

def detect_mobility_gaps() -> list:
    """柔韧性薄弱点（基于柔韧性测试数据，如有）"""
```

**`schedule-builder` Skill**（挂给目标追踪师 + 主理人）

```python
def build_weekly_schedule(goal, available_days, equipment, recovery_state) -> dict:
    """基于用户档案 + 恢复状态生成周训练日历：
    - 周一：高碳日 + 推 + 60min
    - 周二：低碳日 + 活动恢复
    - 周三：中碳日 + 拉 + 60min
    - 周四：休息
    - 周五：高碳日 + 腿 + 75min
    - 周六：低碳日 + 瑜伽/拉伸
    - 周日：休息
    """
```

---

## 实施优先级

按"价值/复杂度"排序：

| 优先级 | Skill / Agent | 价值 | 复杂度 | 估时 | 依赖 |
|:---:|---|:---:|:---:|:---:|---|
| **P0** | `user-profile` | ★★★★★ | 中（需设计采集） | 1-2 天 | — |
| **P0** | `volume-analyzer` | ★★★★★ | 低 | 0.5 天 | user-profile |
| **P0** | `progression-tracker` | ★★★★★ | 中（需 1RM 估算） | 1 天 | user-profile |
| **P0** | `anomaly-detector` | ★★★★ | 中（多信号融合） | 1 天 | user-profile + xunji-trains + apple health |
| **P1** | `goal-tracker-expert` Agent | ★★★★ | 中（设计 SOP） | 1 天 | 4 个 P0 Skill |
| **P1** | `heart-rate-zones` | ★★★ | 低 | 0.5 天 | user-profile |
| **P1** | `weakness-analyzer` | ★★★ | 中 | 1 天 | volume-analyzer + progression-tracker |
| **P2** | `nutrition-gap` | ★★★ | 低 | 0.5 天 | xunji-food + user-profile |
| **P2** | `schedule-builder` | ★★★ | 高（约束求解） | 2-3 天 | 所有上面 + user-profile |
| **P3** | `achievement-tracker` | ★★ | 低 | 0.5 天 | progression-tracker |

## 落地路径

### Phase 6：地基（1-2 周）

**目标**：4 个 P0 Skill 全部就位

1. **`user-profile`**（1-2 天）
   - 设计 JSON schema
   - 写 Skill
   - 采集用户数据
2. **`volume-analyzer`**（0.5 天）
   - 聚合 xunji-trains 数据按肌群/动作/周
   - 红黄绿阈值
3. **`progression-tracker`**（1 天）
   - 1RM 估算公式
   - 平台期检测逻辑
4. **`anomaly-detector`**（1 天）
   - 多信号融合规则
   - 警告分级

### Phase 7：目标追踪师（1 周）

- 新建 `goal-tracker-expert` Agent
- 挂载 4 个 P0 Skill
- 设计 SOP：设目标 → 拆解 → 追踪 → 调整

### Phase 8：决策增强（1-2 周）

- 3 个 P1 Skill（heart-rate-zones / weakness-analyzer / nutrition-gap）
- 每个独立、互不依赖

### Phase 9：体验优化（按需）

- schedule-builder
- achievement-tracker

## 为什么按这个顺序

**P0 这 4 个 Skill 是"复利价值"最大的**：

- `user-profile` 让**所有现有 Agent** 立刻个性化（一次投入，所有 Agent 受益）
- `volume-analyzer` + `progression-tracker` 让训练教练从"能查动作"升级到"能看趋势"
- `anomaly-detector` 让恢复/防护从"被动响应"升级到"主动预警"

完成后整个专家团从「**记录和查询**」升级到「**诊断和建议**」，是质变。

P1-P3 则是"功能扩展"，锦上添花。

## 下一步

1. **采集 user-profile 数据**：需要用户填写（见采集问卷）
2. **写 user-profile Skill**（1-2 天）
3. **并行开发其他 3 个 P0 Skill**（基于 user-profile）

---

## 附录：数据采集问卷

详见 `docs/user-profile-questionnaire.md`（待生成）
