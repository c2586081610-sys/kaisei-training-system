"""kaisei-movement-library 数据加载器。

数据源：
- PW 精简版：~/Documents/kaisei-data/static/peakwatch_movements_slim.json（508 条，含注意段）
- PW 字典：~/Documents/kaisei-data/static/peakwatch_config.json（肌群/部位/器械）
- Xunji 动作名表：~/Documents/kaisei-data/static/xunji_movements_full.json（1092 个）
- Xunji 动作目录：训记 API 提供（缓存于本地时合并 PW 完整版使用）
"""

from __future__ import annotations
import json
import os
from functools import lru_cache
from pathlib import Path

_mem_cache: dict = {}


def _find_config_path() -> Path:
    env = os.environ.get("KAISEI_DATA_CONFIG")
    if env and Path(env).exists():
        return Path(env)
    default = Path.home() / "Documents" / "kaisei-data" / "data.config.json"
    if default.exists():
        return default
    here = Path(__file__).resolve()
    for p in [here.parent, here.parent.parent, here.parent.parent.parent, here.parent.parent.parent.parent]:
        candidate = p / "data.config.json"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("data.config.json 找不到")


def _load_config() -> dict:
    if "_config" not in _mem_cache:
        _mem_cache["_config"] = json.loads(_find_config_path().read_text(encoding="utf-8"))
    return _mem_cache["_config"]


@lru_cache(maxsize=1)
def load_pw_slim() -> list:
    cfg = _load_config()
    p = Path(cfg["data_root"]) / cfg["static"]["pw_movements_slim"]
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_pw_config() -> dict:
    cfg = _load_config()
    p = Path(cfg["data_root"]) / cfg["static"]["pw_config"]
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_xunji_movements() -> dict:
    cfg = _load_config()
    p = Path(cfg["data_root"]) / cfg["static"]["xunji_movements"]
    return json.loads(p.read_text(encoding="utf-8"))
