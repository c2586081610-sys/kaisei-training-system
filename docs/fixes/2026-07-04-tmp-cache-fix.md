# 修复记录：缓存写到 /tmp 问题

**日期**：2026-07-04
**触发**：用户报告下载训记训练数据到 /tmp/kaisei-data 而非 ~/Documents/kaisei-data
**修复人**：统筹总教练

## 问题

5月5日、5月6日 的训记训练数据被下载到 `/tmp/kaisei-data/caches/trains/`，而非 `~/Documents/kaisei-data/caches/trains/`。

## 根因

Skill 内部路径解析按以下优先级：
1. 环境变量 `KAISEI_DATA_CONFIG`
2. `~/Documents/kaisei-data/data.config.json`
3. plugin 根目录 / 父目录的 data.config.json

**WorkBuddy 沙箱在跑 Agent 时，可能将 `Path.home()` 重定向到沙箱家目录**。沙箱里 `~/Documents/kaisei-data/` 不存在时，沙箱自身可能临时生成了一个 data.config.json，data_root 指向 `/tmp/kaisei-data/`。这次下载按这个错误配置跑，写到了 /tmp。

**Skill 代码本身没有"路径安全检查"**，无法阻止错误配置生效。

## 修复

### 1. 加路径白名单校验（4 个文件）

在 `_load_config()` 加载 data.config.json 后立即校验 `data_root`：

- **禁止**：包含 `/tmp` / `/var/folders` / `/private/tmp` / `sandbox`
- **强制白名单**：必须以 `/Users/zzboy/Documents/kaisei-data` 或 `/Users/zzboy/Desktop/kaisei-data` 开头

违反时直接 `RuntimeError` 报错，**不允许 Skill 启动**。

涉及文件：
- `skills/xunji-trains/queries/_client.py`
- `skills/xunji-food/queries/_client.py`
- `skills/kaisei-movement-library/queries/_loader.py`
- `skills/kaisei-physiological-signals/queries/_loader.py`（其他 4 个共享 Skill 通过此文件间接加载）

### 2. 修正 import 回归（3 个文件）

之前的排查记录把 `import _client` 改成 `from . import _client`（相对导入），但**直接执行** `python3 read_trains.py` 时会因缺少包上下文而失败。

**改为 try/except 双兼容**：
```python
try:
    from . import _client
except ImportError:
    import _client
```

这样包方式和直接执行方式都能工作。

### 3. 数据归位

将 `/tmp/kaisei-data/caches/trains/2026-05-{05,06}.json` 复制到 `~/Documents/kaisei-data/caches/trains/`，然后删除 `/tmp/kaisei-data/`。

## 验证

- ✅ 合法 data_root 正常加载
- ✅ /tmp data_root 被拦截（RuntimeError）
- ✅ sandbox 路径被拦截（RuntimeError）
- ✅ 5月5日、5月6日 数据归位后能正常读

## 教训

1. **任何"指向数据"的代码必须有路径安全检查**——不能假设调用方给的配置是对的
2. **环境隔离（沙箱/容器）下的 path.home() 行为不可信**——必须白名单
3. **相对导入 vs 绝对导入要兼容**——避免单一调用方式锁定
