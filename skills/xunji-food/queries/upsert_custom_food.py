"""新增或更新自定义食物。

接口：POST /open/food/custom/upsert_gzip
参数：food 含 name, ntr (cal/protein/fat/carb, 每 100g), units
安全规则：
1. dry_run 默认 True
2. 只有搜索不到合适官方食物，或用户明确要创建私有食物时，才创建
3. ntr 必须有用户确认的营养来源；不确定时追问
4. units 和 ntr.foodUnit 必须一致
"""

from __future__ import annotations
import uuid
from typing import Optional
import _client


def _validate(food: dict) -> Optional[str]:
    if not food.get("name"):
        return "food.name 必填"
    ntr = food.get("ntr", {})
    required = ["cal", "protein", "fat", "carb"]
    for k in required:
        if k not in ntr:
            return f"ntr.{k} 必填（每 100g 数值）"
    units = food.get("units", [])
    food_units = ntr.get("foodUnit", [])
    if units and food_units:
        # 检查一致（简单按 set 比较）
        u1 = {(x.get("unit"), x.get("count"), x.get("gram")) for x in units}
        u2 = {(x.get("unit"), x.get("count"), x.get("gram")) for x in food_units}
        if u1 != u2:
            return "units 和 ntr.foodUnit 不一致"
    return None


def upsert_custom_food(food: dict, dry_run: bool = True, client_request_id: Optional[str] = None) -> dict:
    """参数: food 形如 {name, ntr: {cal, protein, fat, carb, foodUnit}, units: [...]}"""
    err = _validate(food)
    if err:
        return {"success": False, "error": "validation", "detail": err}

    summary = _summarize(food)
    if dry_run:
        return {
            "dry_run": True,
            "summary": summary,
            "action_required": "用户确认营养来源后再次调用，dry_run=False 才会真写",
        }

    body = {
        "client_request_id": client_request_id or str(uuid.uuid4()),
        "dry_run": False,
        "food": food,
    }
    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["food_all"]
    resp = _client.call_food("/open/food/custom/upsert_gzip", body, cooldown=cooldown, bucket="food_custom")

    _client._audit_log("upsert_custom_food", {
        "client_request_id": body["client_request_id"],
        "summary": summary,
        "response_success": resp.get("success"),
    })

    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        return {"success": True, "res": resp["res"], "dry_run": False}
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp


def _summarize(food: dict) -> str:
    ntr = food.get("ntr", {})
    return (
        f"  食物名: {food.get('name')}\n"
        f"  每 100g 营养: cal={ntr.get('cal')} protein={ntr.get('protein')}g "
        f"fat={ntr.get('fat')}g carb={ntr.get('carb')}g\n"
        f"  单位: {food.get('units', [])}"
    )
