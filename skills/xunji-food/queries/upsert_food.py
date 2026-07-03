"""写回饮食记录。

接口：POST /open/food/upsert_gzip
参数：foods[] 含 date/meal_type/name/amount/unit/uniquekey/ntr
安全规则：
1. dry_run 默认 True
2. 必须已有用户确认的 ntr（写回接口不会搜食物也不会替你猜营养）
3. 有服务端记录 id 时更新原记录；没有 id 时新建
4. 不要因为查询结果里缺少旧记录就删除旧记录，除非用户明确要求
5. 写回前必须展示摘要 + 等用户确认
"""

from __future__ import annotations
import uuid
from typing import Optional
import _client


def _validate(foods: list) -> Optional[str]:
    if not isinstance(foods, list) or not foods:
        return "foods 必须是 list 且非空"
    for i, f in enumerate(foods):
        if not f.get("name"):
            return f"第 {i+1} 条食物缺少 name"
        if not f.get("date"):
            return f"第 {i+1} 条食物缺少 date"
        if f.get("amount") is None:
            return f"第 {i+1} 条食物缺少 amount"
        # uniquekey 和 ntr 至少要有一个（如果是官方食物，应带 uniquekey）
        if not f.get("uniquekey") and not f.get("ntr"):
            return f"第 {i+1} 条食物缺少 uniquekey 或 ntr"
    return None


def upsert_food(
    foods: list,
    dry_run: bool = True,
    client_request_id: Optional[str] = None,
) -> dict:
    """参数: foods 形如 [{date, meal_type, name, amount, unit, uniquekey, ntr}, ...]"""
    err = _validate(foods)
    if err:
        return {"success": False, "error": "validation", "detail": err}

    summary = _summarize(foods)
    if dry_run:
        return {
            "dry_run": True,
            "summary": summary,
            "foods_count": len(foods),
            "action_required": "用户确认后再次调用，dry_run=False 才会真写",
        }

    body = {
        "client_request_id": client_request_id or str(uuid.uuid4()),
        "dry_run": False,
        "foods": foods,
    }
    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["food_all"]
    resp = _client.call_food("/open/food/upsert_gzip", body, cooldown=cooldown, bucket="food_write")

    _client._audit_log("upsert_food", {
        "client_request_id": body["client_request_id"],
        "summary": summary,
        "response_success": resp.get("success"),
    })

    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        return {"success": True, "res": resp["res"], "dry_run": False}
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp


def _summarize(foods: list) -> str:
    parts = []
    for i, f in enumerate(foods, 1):
        date = f.get("date", "?")
        meal = f.get("meal_type", "?")
        name = f.get("name", "?")
        amount = f.get("amount", "?")
        unit = f.get("unit", "g")
        uniquekey = f.get("uniquekey", "(无，新自定义?)")
        parts.append(f"  {i}. [{date} {meal}] {name} {amount}{unit} (key={uniquekey})")
    return "\n".join(parts)
