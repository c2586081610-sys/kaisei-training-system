"""饮食模板：查询/套用。

接口：
- 查询模板：POST /open/food/templates/list_gzip
- 套用模板：POST /open/food/templates/apply_gzip
套用模板也属于写回操作，必须先给用户看摘要并等待确认。
"""

from __future__ import annotations
import uuid
from typing import Optional
import _client


def list_templates() -> dict:
    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["food_all"]
    body = {}
    resp = _client.call_food("/open/food/templates/list_gzip", body, cooldown=cooldown, bucket="food_templates_list")

    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        return {"success": True, "res": resp["res"]}
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp


def apply_template(
    template_id: str,
    target_date: str,
    meal_type: str,
    dry_run: bool = True,
    client_request_id: Optional[str] = None,
) -> dict:
    """参数: template_id (从 list_templates 获取), target_date YYYY-MM-DD, meal_type 如 'lunch'"""
    if not template_id or not target_date or not meal_type:
        return {"success": False, "error": "validation", "detail": "template_id, target_date, meal_type 必填"}

    summary = f"  套用模板 {template_id} 到 {target_date} {meal_type}"

    if dry_run:
        return {
            "dry_run": True,
            "summary": summary,
            "action_required": "用户确认后再次调用，dry_run=False 才会真写",
        }

    body = {
        "client_request_id": client_request_id or str(uuid.uuid4()),
        "dry_run": False,
        "template_id": template_id,
        "date": target_date,
        "meal_type": meal_type,
    }
    cfg = _client._load_config()
    cooldown = cfg["rate_limits"]["food_all"]
    resp = _client.call_food("/open/food/templates/apply_gzip", body, cooldown=cooldown, bucket="food_templates_apply")

    _client._audit_log("apply_template", {
        "client_request_id": body["client_request_id"],
        "summary": summary,
        "response_success": resp.get("success"),
    })

    if isinstance(resp, dict) and "res" in resp and "error" not in resp:
        return {"success": True, "res": resp["res"], "dry_run": False}
    if "success" not in resp:
        resp = {"success": False, "error": "unexpected_response", "detail": str(resp)[:500]}
    return resp
