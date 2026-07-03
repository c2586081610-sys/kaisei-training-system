"""训记 Xunji 训练 API 共享客户端。

职责：
1. 加载 data.config.json（定位用户数据根目录 + 端点 + 限频）
2. 加载 secrets.json（读取鉴权 Key，绝不打印/写日志）
3. HTTP POST 调用，限频控制（读 15s / 含 full 30s / 写 45s）
4. 缓存（trains 按 datestr 缓存；写回成功后覆盖缓存）
5. 审计日志（写回前记 audit log）
"""

from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

# ---------- 单例状态 ----------
_state: dict = {
    "config": None,
    "secrets": None,
    "last_call_at": {},  # 接口名 → 上次调用 epoch
}


def _find_config_path() -> Path:
    """按优先级找 data.config.json。"""
    env = os.environ.get("KAISEI_DATA_CONFIG")
    if env and Path(env).exists():
        return Path(env)
    # 用户默认数据根
    default = Path.home() / "Documents" / "kaisei-data" / "data.config.json"
    if default.exists():
        return default
    # plugin 根目录
    here = Path(__file__).resolve()
    for p in [here.parent, here.parent.parent, here.parent.parent.parent, here.parent.parent.parent.parent]:
        candidate = p / "data.config.json"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "data.config.json 找不到。请在 ~/Documents/kaisei-data/ 下创建，"
        "或参考 plugin/data.config.example.json。"
    )


def _load_config() -> dict:
    if _state["config"] is None:
        p = _find_config_path()
        _state["config"] = json.loads(p.read_text(encoding="utf-8"))
    return _state["config"]


def _load_secrets() -> dict:
    if _state["secrets"] is None:
        cfg = _load_config()
        data_root = Path(cfg["data_root"])
        secrets_file = data_root / cfg.get("secrets_file", "secrets.json")
        if not secrets_file.exists():
            raise FileNotFoundError(f"secrets.json 找不到：{secrets_file}")
        _state["secrets"] = json.loads(secrets_file.read_text(encoding="utf-8"))
    return _state["secrets"]


def _get_key(env_name: str) -> str:
    """根据 env-name 拿 Key。"""
    secrets = _load_secrets()
    if env_name not in secrets:
        raise KeyError(f"secrets.json 缺少 key: {env_name}")
    return secrets[env_name]


# ---------- 限频 ----------
def _throttle(bucket: str, cooldown: float) -> None:
    """同一接口 cooldown 秒内不能重复调用。不足则 sleep。"""
    now = time.time()
    last = _state["last_call_at"].get(bucket, 0)
    wait = cooldown - (now - last)
    if wait > 0:
        time.sleep(wait)
    _state["last_call_at"][bucket] = time.time()


# ---------- HTTP ----------
def _post_json(url: str, headers: dict, body: dict, timeout: int = 30) -> dict:
    import gzip
    data = json.dumps(body).encode("utf-8")
    # 请求时也声明接受 gzip
    h = dict(headers)
    h.setdefault("Accept-Encoding", "gzip")
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # 如果服务端返回了 gzip 压缩，解压
            if raw[:2] == b"\x1f\x8b":
                try:
                    raw = gzip.decompress(raw)
                except Exception:
                    pass
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read()
            if err_body[:2] == b"\x1f\x8b":
                err_body = gzip.decompress(err_body)
            err_body = err_body.decode("utf-8")
        except Exception:
            err_body = str(e)
        return {"success": False, "error": f"HTTP {e.code}", "detail": err_body}
    except urllib.error.URLError as e:
        return {"success": False, "error": "URLError", "detail": str(e.reason)}
    except Exception as e:
        return {"success": False, "error": type(e).__name__, "detail": str(e)}


def _auth_headers(env_name: str) -> dict:
    key = _get_key(env_name)
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "x-api-key": key,  # 兼容 header
    }


# ---------- 缓存 ----------
def _cache_path(kind: str, name: str) -> Path:
    """返回缓存文件路径。kind: 'trains' / 'foods' / 'movements'。"""
    cfg = _load_config()
    return Path(cfg["data_root"]) / cfg["caches"][f"{kind}_dir"] / name


def _read_cache(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 审计 ----------
def _audit_log(action: str, payload: dict) -> None:
    cfg = _load_config()
    audit_dir = Path(cfg["data_root"]) / cfg.get("audit_dir", "audit")
    audit_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = audit_dir / f"writeback_{today}.log"
    line = json.dumps(
        {"ts": datetime.now().isoformat(), "action": action, "payload": payload},
        ensure_ascii=False,
    )
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------- 公开调用入口 ----------
def call_trains(endpoint: str, body: dict, cooldown: float, bucket: str) -> dict:
    """调训记训练 API（含限频）。"""
    cfg = _load_config()
    url = cfg["endpoints"]["trains_base"] + endpoint
    _throttle(bucket, cooldown)
    return _post_json(url, _auth_headers("XUNJI_TRAINS_KEY"), body)
