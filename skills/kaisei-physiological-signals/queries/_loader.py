"""生理指标数据加载器（共享 base 路径）。"""
import json
import os
from functools import lru_cache
from pathlib import Path

_mem = {}


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
    if "_config" not in _mem:
        _mem["_config"] = json.loads(_find_config_path().read_text(encoding="utf-8"))
        # 路径安全校验：data_root 不能指向临时目录
        data_root = str(_mem["_config"].get("data_root", ""))
        for forbidden in ["/tmp", "/var/folders", "/private/tmp", "sandbox"]:
            if forbidden in data_root.lower():
                raise RuntimeError(
                    f"data.config.json 的 data_root 指向临时/沙箱目录：{data_root}\n"
                    f"必须改为 /Users/zzboy/Documents/kaisei-data 这种持久化目录。"
                )
        for allowed in ["/Users/zzboy/Documents/kaisei-data", "/Users/zzboy/Desktop/kaisei-data"]:
            if data_root.startswith(allowed):
                break
        else:
            raise RuntimeError(
                f"data.config.json 的 data_root 不在白名单：{data_root}\n"
                f"白名单：/Users/zzboy/Documents/kaisei-data 或 /Users/zzboy/Desktop/kaisei-data"
            )
    return _mem["_config"]


def _private_path(name: str) -> Path:
    cfg = _load_config()
    return Path(cfg["data_root"]) / cfg["private"][name]


@lru_cache(maxsize=1)
def _load(name: str) -> dict:
    p = _private_path(name)
    if not p.exists():
        return {"_note": f"private/{name}.json 不存在", "days": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def get(name: str) -> dict:
    """获取生理指标数据（带 cache）。name: 'rhr' / 'hrv' / 'spo2' / 'wrist_temp'。"""
    return _load(name)
