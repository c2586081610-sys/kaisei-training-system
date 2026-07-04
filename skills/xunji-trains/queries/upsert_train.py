"""写回训练记录（增/改）。

接口：POST /api_upsert_trains_for_llm_v2
安全规则（按训记 API 文档）：
1. dry_run 默认 True，必须显式 False 才真写
2. 单次最多 4 条训练，必须同日
3. 每条训练最多 15 个动作，每个动作最多 20 组
4. 写回动作只传中文 name，不要传 key
5. 不确定中文名时先 list_standard_movements
6. 有 localid = 更新原训练，没有 = 新建
7. 更新旧训练保留 localid/start/end，除非用户明确要改时间
8. 未完成组用 done:false
9. 写回前 dry_run 展示摘要 + 等用户确认
10. 写回成功后用服务端标准化 res 覆盖缓存
"""

from __future__ import annotations
from typing import Optional
try:
    from . import _client
except ImportError:
    # 直接执行时（不在包内），回退到绝对导入
    import _client


def _validate(trains: list) -> Optional[str]:
    if not isinstance(trains, list):
        return "trains 必须是 list"
    if len(trains) == 0:
        return "trains 不能为空"
    if len(trains) > 4:
        return f"单次最多 4 条训练，当前 {len(trains)}"
    # 同日校验
    dates = {t.get("datestr", "") for t in trains}
    if len(dates) > 1:
        return f"单次写回必须同日，当前日期：{dates}"
    for i, t in enumerate(trains):
        mvs = t.get("movements", [])
        if len(mvs) > 15:
            return f"第 {i+1} 条训练动作数 {len(mvs)} 超过 15 上限"
        for j, m in enumerate(mvs):
            if not m.get("name"):
                return f"第 {i+1} 条训练第 {j+1} 个动作缺少中文 name"
            sets = m.get("sets", [])
            if len(sets) > 20:
                return f"第 {i+1} 条训练第 {j+1} 个动作组数 {len(sets)} 超过 20 上限"
    return None


def upsert_train(
    trains: list,
    dry_run: bool = True,
    client_request_id: Optional[str] = None,
) -> dict:
    """
    参数:
        trains: 训练列表，每条形如 {datestr, localid?, title, start, end, movements: [{name, sets: [...]}]}
        dry_run: True = 仅预览不真写（默认），False = 真写
        client_request_id: 唯一请求 ID（防止重复提交）
    返回:
        dry_run 模式：{"dry_run": True, "summary": "变更摘要", "trains_count": N, "movements_count": M}
        真写模式：{"success": bool, "res": {...}, "from_cache": False, "dry_run": False}
    """
    # 校验
    err = _validate(trains)
    if err:
        return {"success": False, "error": "validation", "detail": err}

    # 摘要
    summary = _summarize(trains)

    if dry_run:
        return {
            "dry_run": True,
            "summary": summary,
            "trains_count": len(trains),
            "action_required": "用户确认后再次调用，dry_run=False 才会真写",
        }

    # 真写
    import uuid
    body = {
        "schema_version": "train_open_api_v2",
        "client_request_id": client_request_id or str(uuid.uuid4()),
        "dry_run": False,
        "include_full_data": False,
        "res": trains,
    }

    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["trains_write"]
    resp = _client.call_trains("/api_upsert_trains_for_llm_v2", body, cooldown=cooldown, bucket="trains_write")

    # 审计
    _client._audit_log("upsert_train", {
        "client_request_id": body["client_request_id"],
        "summary": summary,
        "response_success": resp.get("success"),
    })

    if resp.get("success") is True:
        # 用服务端标准化数据覆盖当日缓存
        server_res = resp.get("res", {})
        datestr = trains[0].get("datestr")
        if datestr:
            cache_path = _client._cache_path("trains", f"{datestr}.json")
            payload = {
                "success": True,
                "res": server_res,
                "from_cache": False,
                "ts": _client.datetime.now().isoformat(),
            }
            _client._write_cache(cache_path, payload)
        return payload
    return resp


def _summarize(trains: list) -> str:
    """生成变更摘要（供 dry_run 展示 + 用户确认）。"""
    parts = []
    for i, t in enumerate(trains, 1):
        localid = t.get("localid")
        title = t.get("title", "(未命名)")
        datestr = t.get("datestr", "?")
        mvs = t.get("movements", [])
        mv_summary = ", ".join(m.get("name", "?") for m in mvs[:5])
        if len(mvs) > 5:
            mv_summary += f" 等 {len(mvs)} 个动作"
        action = "更新" if localid else "新建"
        parts.append(f"  {i}. [{action}] {datestr} {title} ({len(mvs)} 动作: {mv_summary})")
    return "\n".join(parts)
