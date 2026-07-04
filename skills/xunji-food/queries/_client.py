"""训记 Xunji 饮食 API 共享客户端。

复用 xunji-trains 的 _client 思路，但饮食端点不同，且：
- 查询/写回/自定义/模板 走 https://eatings.xunjiapp.cn
- 食物搜索走 https://api.xunjiapp.cn（鉴权用 XUNJI_FOOD_SEARCH_KEY，不是 XUNJI_FOOD_KEY）
- 所有接口 15s 限频
"""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
import gzip
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

_state = {"config": None, "secrets": None, "last_call_at": {}}


def _find_config_path() -> Path:
    import os
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
    if _state["config"] is None:
        _state["config"] = json.loads(_find_config_path().read_text(encoding="utf-8"))
        # 路径安全校验：data_root 不能指向临时目录
        data_root = str(_state["config"].get("data_root", ""))
        for forbidden in ["/tmp", "/var/folders", "/private/tmp", "sandbox"]:
            if forbidden in data_root.lower():
                raise RuntimeError(
                    f"data.config.json 的 data_root 指向临时/沙箱目录：{data_root}\n"
                    f"必须改为 /Users/zzboy/Documents/kaisei-data 这种持久化目录。\n"
                    f"请检查 ~/Documents/kaisei-data/data.config.json 是否存在且正确。"
                )
        for allowed in ["/Users/zzboy/Documents/kaisei-data", "/Users/zzboy/Desktop/kaisei-data"]:
            if data_root.startswith(allowed):
                break
        else:
            raise RuntimeError(
                f"data.config.json 的 data_root 不在白名单：{data_root}\n"
                f"白名单：/Users/zzboy/Documents/kaisei-data 或 /Users/zzboy/Desktop/kaisei-data"
            )
    return _state["config"]


def _load_secrets() -> dict:
    if _state["secrets"] is None:
        cfg = _load_config()
        secrets_path = Path(cfg["data_root"]) / cfg.get("secrets_file", "secrets.json")
        _state["secrets"] = json.loads(secrets_path.read_text(encoding="utf-8"))
    return _state["secrets"]


def _get_key(env_name: str) -> str:
    s = _load_secrets()
    if env_name not in s:
        raise KeyError(f"secrets.json 缺少 key: {env_name}")
    return s[env_name]


def _throttle(bucket: str, cooldown: float) -> None:
    now = time.time()
    last = _state["last_call_at"].get(bucket, 0)
    wait = cooldown - (now - last)
    if wait > 0:
        time.sleep(wait)
    _state["last_call_at"][bucket] = time.time()


def _post_json(url: str, headers: dict, body: dict, timeout: int = 30) -> Any:
    data = json.dumps(body).encode("utf-8")
    h = dict(headers)
    h.setdefault("Accept-Encoding", "gzip")
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if raw[:2] == b"\x1f\x8b":
                try: raw = gzip.decompress(raw)
                except: pass
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


def _auth_food_headers() -> dict:
    key = _get_key("XUNJI_FOOD_KEY")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "x-api-key": key}


def _auth_search_headers() -> dict:
    key = _get_key("XUNJI_FOOD_SEARCH_KEY")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "x-api-key": key, "x-agent-key": key}


def _cache_path(name: str) -> Path:
    cfg = _load_config()
    return Path(cfg["data_root"]) / cfg["caches"]["foods_dir"] / name


def _read_cache(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try: return json.loads(path.read_text(encoding="utf-8"))
    except: return None


def _write_cache(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _audit_log(action: str, payload: dict) -> None:
    cfg = _load_config()
    audit_dir = Path(cfg["data_root"]) / cfg.get("audit_dir", "audit")
    audit_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = audit_dir / f"writeback_{today}.log"
    line = json.dumps({"ts": datetime.now().isoformat(), "action": action, "payload": payload}, ensure_ascii=False)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------- 公开调用入口 ----------
def call_food(endpoint: str, body: dict, cooldown: float, bucket: str, use_search_key: bool = False) -> dict:
    cfg = _load_config()
    url = cfg["endpoints"]["food_base"] + endpoint
    if use_search_key:
        url = cfg["endpoints"]["food_search_base"] + endpoint
    _throttle(bucket, cooldown)
    headers = _auth_search_headers() if use_search_key else _auth_food_headers()
    return _post_json(url, headers, body)


def validate_date_range(start_date: str, end_date: str) -> Optional[str]:
    """训记饮食 API 限制：过去 1 年 ~ 未来 3 个月。"""
    try:
        s = date.fromisoformat(start_date)
        e = date.fromisoformat(end_date)
    except Exception as ex:
        return f"日期格式错误：{ex}"
    today = date.today()
    earliest = date(today.year - 1, today.month, today.day)
    latest = date(today.year, today.month + 3, 1) if today.month <= 9 else date(today.year + 1, today.month - 9, 1)
    if s < earliest:
        return f"开始日期 {start_date} 早于 1 年前 ({earliest})，请拆分到允许范围"
    if e > latest:
        return f"结束日期 {end_date} 晚于 3 个月后 ({latest})，请拆分到允许范围"
    if s > e:
        return f"开始日期 {start_date} 晚于结束日期 {end_date}"
    return None
