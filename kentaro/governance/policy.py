"""Pure deterministic evaluation of proposed actions; it never invokes a tool."""
from __future__ import annotations

from datetime import datetime, timezone

from .schemas import index_objects, validate_bundle


def _now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _expired(value: str, now: datetime) -> bool:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) <= now


def _result(outcome: str, request: dict, chain: dict, rules: list[dict], evaluated_at: datetime) -> dict:
    return {
        "outcome": outcome,
        "execution_request": {"id": request["id"], "version": request["version"]},
        "evaluated_objects": [
            {"id": chain[name]["id"], "version": chain[name]["version"], "object_type": chain[name]["object_type"]}
            for name in ("execution_package", "work_envelope", "mandate")
        ],
        "rules": rules,
        "evaluated_at": evaluated_at.isoformat(),
        "execution_permitted": False,
    }


def _resolve(index: dict, item: dict, field: str) -> dict | None:
    reference = item.get(field)
    if not isinstance(reference, dict):
        return None
    return index.get((reference.get("id"), reference.get("version")))


def evaluate_execution_request(bundle: dict, request_id: str, *, request_version: int | None = None, evaluated_at: str | None = None) -> dict:
    """Return a reproducible structural result without external reads or side effects."""
    validation = validate_bundle(bundle)
    index = index_objects(bundle) if isinstance(bundle.get("objects"), list) else {}
    matches = [item for item in index.values() if item.get("object_type") == "execution_request" and item.get("id") == request_id]
    if request_version is not None:
        matches = [item for item in matches if item.get("version") == request_version]
    if len(matches) != 1:
        raise ValueError("Select exactly one valid ExecutionRequest by id and optional version")
    request = matches[0]
    now = _now(evaluated_at)
    if not validation["valid"]:
        raise ValueError("ExecutionRequest evaluation requires a valid local governance bundle")
    package = _resolve(index, request, "execution_package_reference")
    envelope = _resolve(index, package or {}, "work_envelope_reference")
    mandate = _resolve(index, envelope or {}, "mandate_reference")
    if not package or not envelope or not mandate:
        raise ValueError("ExecutionRequest requires a complete ExecutionPackage, WorkEnvelope, and Mandate chain")
    chain = {"execution_package": package, "work_envelope": envelope, "mandate": mandate}
    rules: list[dict] = []

    if not mandate.get("owner") or not envelope.get("owner"):
        rules.append({"id": "missing_owner", "result": "escalated", "reason": "Mandate and WorkEnvelope require named owners for evaluation."})
        return _result("escalated", request, chain, rules, now)
    if _expired(mandate["expires_at"], now) or _expired(envelope["expires_at"], now):
        rules.append({"id": "expired_boundary", "result": "escalated", "reason": "Mandate or WorkEnvelope has expired."})
        return _result("escalated", request, chain, rules, now)

    contexts = [item for item in index.values() if item.get("object_type") == "context_package"]
    if not contexts or any(context["freshness"] != "fresh" or context["conflicts"] for context in contexts):
        rules.append({"id": "context_uncertain", "result": "escalated", "reason": "Context is missing, stale, unknown, or conflicting."})
        return _result("escalated", request, chain, rules, now)
    if request["tool"] not in envelope["tools"]:
        rules.append({"id": "tool_outside_envelope", "result": "denied", "reason": "Requested tool is outside the WorkEnvelope."})
        return _result("denied", request, chain, rules, now)
    if request["requested_authority"] > envelope["authority_level"]:
        rules.append({"id": "authority_escalation", "result": "denied", "reason": "Requested authority exceeds the WorkEnvelope."})
        return _result("denied", request, chain, rules, now)
    if request["approval_expires_at"] and _expired(request["approval_expires_at"], now):
        rules.append({"id": "expired_approval", "result": "escalated", "reason": "Approval data has expired; v0.1 does not request or process approvals."})
        return _result("escalated", request, chain, rules, now)
    if request["approval_required"]:
        rules.append({"id": "approval_required", "result": "approval_required", "reason": "A future approval boundary applies; v0.1 records no real approval."})
        return _result("approval_required", request, chain, rules, now)
    rules.append({"id": "structurally_in_scope", "result": "allowed", "reason": "The proposed request is structurally within the local boundary; execution remains disabled."})
    return _result("allowed", request, chain, rules, now)
