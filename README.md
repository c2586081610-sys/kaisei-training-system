# 凯圣王训练体系（Kaisei Training System）

基于凯圣王 B 站碳水循环体系，接入训记（Xunji）Open API 作为个性化数据源，融合 PeakWatch 动作库的 5 人 Team 型训练教练团。

## 团队（5 个 Agent）

| Agent ID | 中文名 | 职责 | 挂载 Skills |
|---|---|---|---|
| `kaisei-training-system-team-lead` | 统筹总教练 | 调度 + 汇编，不直连数据 | （空，铁律） |
| `training-expert` | 训练教练 | 训练方案编排、动作指导、碳日-训练匹配、读写训记训练 | xunji-trains, kaisei-movement-library |
| `nutrition-expert` | 饮食营养碳循环教练 | 碳循环计算、食物选择、动态调整、读写训记饮食 | kaisei-carb-cycling, xunji-food |
| `recovery-expert` | 恢复睡眠教练 | 睡眠优化、疲劳管理、主动恢复策略 | kaisei-movement-library, xunji-trains, kaisei-recovery-mobility |
| `injury-rehab-expert` | 运动防护与康复教练 | 损伤评估、康复方案、动作模式矫正 | kaisei-movement-library, xunji-trains, kaisei-rehab-protocols |

## 蒸馏协议

新增凯圣王体系内容时按 [`docs/distillation-protocol.md`](docs/distillation-protocol.md) 协议写到对应 Skill。

## 7 个 Skill

### 共享 Skill（多 Agent 共用）

| Skill | 数据源 | 能力 |
|---|---|---|
| `kaisei-movement-library` | 本地（PW 508 + Xunji 1092） | 按分类/肌群/器械/关键词筛选动作、取"注意"段、校验 Xunji 动作名 |
| `xunji-trains` | 远程（训记训练 API） | 读某日训练、写回训练（dry_run 必走）、列标准动作名 |
| `xunji-food` | 远程（训记饮食 API） | 查询饮食/搜索食物/写回饮食/自定义食物/模板套用 |

### 私有 Skill（单 Agent 专属）

| Skill | Agent | 状态 |
|---|---|---|
| `kaisei-carb-cycling` | 营养教练 | ✅ 100%（凯圣王碳水循环上下集蒸馏） |
| `kaisei-training-protocols` | 训练教练 | ⏳ 5%（碳日-训练匹配已蒸馏） |
| `kaisei-recovery-mobility` | 恢复教练 | ⏳ 0%（骨架已建，待蒸馏） |
| `kaisei-rehab-protocols` | 防护教练 | ⏳ 0%（骨架已建，待蒸馏） |
| `kaisei-physiological-signals` | 恢复+防护+训练 | ⏳ Phase 4（待 HealthKit 数据源） |
| `kaisei-sleep-recovery` | 恢复+训练 | ⏳ Phase 4 |
| `kaisei-body-metrics` | 训练+营养 | ⏳ Phase 4 |
| `kaisei-activity-tracking` | 恢复+训练 | ⏳ Phase 4 |
| `kaisei-hydration` | 营养+恢复 | ⏳ Phase 4 |

## 本地数据根目录

plugin 仓库**不存放任何个性化数据或 API Key**。所有用户私有数据放本地：

```
~/Documents/kaisei-data/        ← 数据根（默认路径，可改）
├── secrets.json                 ← API Key（chmod 600，git 排除）
├── data.config.json             ← 路径映射（plugin 通过这个找数据）
├── caches/trains/               ← 训记训练 API 响应缓存
├── caches/foods/                ← 训记饮食 API 响应缓存
├── static/                      ← 静态参考数据（PW 动作库、Xunji 名表）
├── private/                     ← 用户个人健康数据（HRV/RHR/睡眠/...）
└── audit/                       ← 写回操作审计日志
```

### 首次配置

1. **创建数据根目录**（如不存在）：

   ```bash
   mkdir -p ~/Documents/kaisei-data/{caches/{trains,foods,movements},static,private,audit}
   ```

2. **复制配置模板**：

   ```bash
   cp <plugin>/data.config.example.json ~/Documents/kaisei-data/data.config.json
   ```

3. **创建 secrets.json**（从训记 App 获取 3 个 Key 后填入）：

   ```json
   {
     "XUNJI_TRAINS_KEY": "<填入你的训记训练 API Key>",
     "XUNJI_FOOD_KEY": "<填入你的训记饮食 API Key>",
     "XUNJI_FOOD_SEARCH_KEY": "<填入你的训记食物搜索 Key>"
   }
   ```

   ```bash
   chmod 600 ~/Documents/kaisei-data/secrets.json
   ```

4. **复制静态数据**（从 PeakWatch 反编译数据 / GitHub 同步）：

   见 `docs/data-prep.md`（如有）

### 自定义数据根目录

如果不想用默认路径，有 3 种方式（按优先级）：

```bash
# 方式 1：环境变量（推荐）
export KAISEI_DATA_CONFIG=/path/to/data.config.json

# 方式 2：放在 plugin 根的 data.config.json（gitignore 已排除）
# 方式 3：默认 ~/Documents/kaisei-data/data.config.json
```

## 写回操作安全规则

**所有写回训记 API 的操作必须遵守"三步流程"**：

1. **dry_run=True**（默认）— 调 Skill 拿到变更摘要
2. **展示摘要给用户** — 列出日期、餐次、食物名、数量、单位、key
3. **用户明确确认后** — 重调 Skill 传 dry_run=False 才真写

任何时候用户没确认就"被"写回了，**视为事故**，需立即从 audit 日志定位 + 回滚。

### 限频

| 接口 | 限频 |
|---|---|
| 训记训练读 | 15s/次（轻量）/ 30s/次（含 full data） |
| 训记训练写 | 45s/次 |
| 训记饮食/搜索/模板 | 15s/次 |

Skill 内部已实现 sleep 等待，Agent 不用手动处理。

## 团队协作铁律

1. **主理人只调度不持有数据** — `skills: []` 永远空
2. **专项 Agent 持有数据 + 调 API** — 主理人通过 SendMessage 收汇总
3. **写回必须由专项 Agent 发起** — 主理人不直连训记 API
4. **dry_run 必须先走** — 见上节三步流程
5. **成员不能互相直连** — 所有跨成员通信经主理人中转

## 知识可靠性规则（90/10 规则）

1. **90% 忠于凯圣王体系** — 回答以 Skill 公式/数据表/方法论为基础
2. **10% 检索对立观点** — 每个回答附带一次网络搜索
3. **标注引用** — 资料结论标"凯圣王体系"，网络观点标出处
4. **无资料 = 不调用** — 不编造内容

## 开发约定

### 新增 Skill

```
skills/<skill-name>/
├── SKILL.md              # Skill 描述、接口、调用方法
└── queries/              # Python 查询脚本
    ├── __init__.py
    ├── _client.py        # 共享 HTTP 客户端、限频、缓存
    └── <operation>.py    # 各操作（read/upsert/...）
```

挂载到 Agent：
- 在 Agent MD 顶部 `skills: [skill-name]` 加一项
- 在 `plugin.json` 的 `skills` 数组加 `'./skills/skill-name'`

### 修改触发自动提交

按 team-lead.md 规则，以下变更触发 `git add -A && git commit -m "[auto] ..." && git push`：

- 体系规则变更（90/10、SOP）
- 成员能力清单增删
- Skill 内容更新
- 专家 MD 核心能力/工作流程变更
- plugin.json 团队结构变更

不触发：纯格式修正、头像替换、临时调试。

## 仓库

- **本地**：`~/.workbuddy/plugins/marketplaces/my-experts/plugins/kaisei-training-system/`
- **远程**：https://github.com/c2586081610-sys/kaisei-training-system
