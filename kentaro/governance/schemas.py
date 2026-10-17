"""Versioned local-object validation with no external I/O except explicit JSON reads."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


SCHEMA_VERSION = 1
OBJECT_TYPES = {
    "context_package",
    "mandate",
    "work_envelope",
    "execution_package",
    "execution_request",
    "revocation_policy",
    "evidence_event",
    "correction",
}
REVOCATION_SCOPES = {"agent", "capability", "connector", "workspace", "mandate"}
REVOCATION_SEVERITIES = {"low", "medium", "high", "critical"}
REVOCATION_ACTIONS = {"disable_execution", "disable_connector", "require_human_review", "restrict_scope"}
MAYSANO_ROLES = {"Service Owner", "Policy Owner", "Connector Owner", "Security Officer", "Platform Administrator"}
MINIMUM_SUSPENSION_TRIGGERS = {
    "outside_work_envelope_or_mandate",
    "payload_scope_or_target_differs_from_approved_digest",
    "source_evidence_missing_stale_or_contradictory",
    "unapproved_confidential_personal_or_credential_derived_data",
    "deterministic_validation_or_policy_control_failed",
    "repeated_correction_rejection_or_safety_failure_threshold",
    "identity_connector_or_credential_integrity_unverified",
    "emergency_suspension_by_accountable_authority",
}
LOCAL_REVOCATION_STATUSES = {"declared_active", "simulated_suspended"}
COMMON_FIELDS = {
    "id",
    "object_type",
    "schema_version",
    "version",
    "created_at",
    "actor",
    "source_references",
    "relationship_references",
}


def load_bundle(path: str | Path) -> dict:
    """Load a local JSON object bundle without interpreting any content as code."""
    try:
        with Path(path).open(encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Unable to read a valid local governance JSON bundle") from error
    if not isinstance(payload, dict):
        raise ValueError("Governance bundle must be a JSON object")
    return payload


def _is_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _finding(code: str, message: str, *, object_id: str | None = None, severity: str = "error") -> dict:
    finding = {"code": code, "message": message, "severity": severity}
    if object_id is not None:
        finding["object_id"] = object_id
    return finding


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _is_role_list(value: object) -> bool:
    return _is_string_list(value) and bool(value) and set(value).issubset(MAYSANO_ROLES)


def _validate_reference(value: object, field: str, object_id: str, findings: list[dict]) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not value["id"] or type(value.get("version")) is not int or value["version"] < 1:
        findings.append(_finding("invalid_reference", f"{field} must contain a nonempty id and positive integer version", object_id=object_id))


def _validate_common(item: object, findings: list[dict]) -> str | None:
    if not isinstance(item, dict):
        findings.append(_finding("invalid_object", "Each object must be a JSON object"))
        return None
    object_id = item.get("id") if isinstance(item.get("id"), str) else None
    if not object_id:
        findings.append(_finding("missing_id", "Object requires a nonempty id"))
        return None
    if item.get("object_type") not in OBJECT_TYPES:
        findings.append(_finding("invalid_object_type", "Object type is unsupported", object_id=object_id))
    if item.get("schema_version") != SCHEMA_VERSION:
        findings.append(_finding("unsupported_schema_version", "Object schema_version must be 1", object_id=object_id))
    if type(item.get("version")) is not int or item["version"] < 1:
        findings.append(_finding("invalid_version", "Object version must be a positive integer", object_id=object_id))
    if not _is_timestamp(item.get("created_at")):
        findings.append(_finding("invalid_created_at", "created_at must be an ISO 8601 timestamp", object_id=object_id))
    if not isinstance(item.get("actor"), str) or not item["actor"]:
        findings.append(_finding("invalid_actor", "actor must be a nonempty string", object_id=object_id))
    for field in ("source_references", "relationship_references"):
        references = item.get(field)
        if not isinstance(references, list):
            findings.append(_finding("invalid_references", f"{field} must be a list", object_id=object_id))
            continue
        for reference in references:
            _validate_reference(reference, field, object_id, findings)
            if field == "source_references" and (not isinstance(reference, dict) or not _is_timestamp(reference.get("retrieved_at"))):
                findings.append(_finding("invalid_source_timestamp", "source_references require retrieved_at as an ISO 8601 timestamp", object_id=object_id))
    return object_id


def _validate_object(item: object, findings: list[dict]) -> None:
    object_id = _validate_common(item, findings)
    if object_id is None or not isinstance(item, dict):
        return
    kind = item.get("object_type")
    if kind == "context_package":
        if not item["source_references"]:
            findings.append(_finding("missing_context_sources", "ContextPackage requires at least one source reference", object_id=object_id))
        if not isinstance(item.get("retrieval_scope"), dict):
            findings.append(_finding("invalid_context_scope", "ContextPackage requires retrieval_scope", object_id=object_id))
        if item.get("freshness") not in {"fresh", "stale", "unknown"}:
            findings.append(_finding("invalid_freshness", "ContextPackage freshness must be fresh, stale, or unknown", object_id=object_id))
        if not isinstance(item.get("conflicts"), list):
            findings.append(_finding("invalid_conflicts", "ContextPackage conflicts must be a list", object_id=object_id))
    elif kind == "mandate":
        _validate_boundary(item, object_id, findings, "Mandate")
        if not isinstance(item.get("business_area"), str) or not item["business_area"]:
            findings.append(_finding("invalid_business_area", "Mandate requires business_area", object_id=object_id))
        if not _is_timestamp(item.get("expires_at")):
            findings.append(_finding("invalid_expiry", "Mandate requires expires_at", object_id=object_id))
    elif kind == "work_envelope":
        _validate_boundary(item, object_id, findings, "WorkEnvelope")
        _validate_reference(item.get("mandate_reference"), "mandate_reference", object_id, findings)
        if not isinstance(item.get("requested_result"), str) or not item["requested_result"]:
            findings.append(_finding("invalid_requested_result", "WorkEnvelope requires requested_result", object_id=object_id))
        if not _is_timestamp(item.get("expires_at")):
            findings.append(_finding("invalid_expiry", "WorkEnvelope requires expires_at", object_id=object_id))
    elif kind == "execution_package":
        _validate_boundary(item, object_id, findings, "ExecutionPackage")
        _validate_reference(item.get("work_envelope_reference"), "work_envelope_reference", object_id, findings)
        for field in ("planned_steps", "expected_outputs", "dependencies", "acceptance_criteria"):
            if not _is_string_list(item.get(field)):
                findings.append(_finding("invalid_delivery_plan", f"ExecutionPackage {field} must be a list of nonempty strings", object_id=object_id))
        if not isinstance(item.get("timing"), str) or not item["timing"]:
            findings.append(_finding("invalid_timing", "ExecutionPackage requires timing", object_id=object_id))
    elif kind == "revocation_policy":
        if not isinstance(item.get("policyId"), str) or item.get("policyId") != object_id:
            findings.append(_finding("invalid_policy_id", "RevocationPolicy policyId must equal its stable id", object_id=object_id))
        if item.get("scope") not in REVOCATION_SCOPES:
            findings.append(_finding("invalid_revocation_scope", "RevocationPolicy scope is unsupported", object_id=object_id))
        chain = item.get("authorityChain")
        if not isinstance(chain, dict):
            findings.append(_finding("invalid_authority_chain", "RevocationPolicy requires an authorityChain object", object_id=object_id))
        else:
            _validate_reference(chain.get("mandate_reference"), "authorityChain.mandate_reference", object_id, findings)
            _validate_reference(chain.get("work_envelope_reference"), "authorityChain.work_envelope_reference", object_id, findings)
            for field in ("suspendAuthorities", "restoreAuthorities", "narrowAuthorities", "emergencySuspendAuthorities"):
                if not _is_role_list(chain.get(field)):
                    findings.append(_finding("invalid_revocation_authority", f"authorityChain {field} must name one or more Maysano roles", object_id=object_id))
            if "Security Officer" not in chain.get("emergencySuspendAuthorities", []):
                findings.append(_finding("missing_emergency_authority", "RevocationPolicy emergencySuspendAuthorities must include Security Officer", object_id=object_id))
        if item.get("accountableOwnerRole") not in MAYSANO_ROLES:
            findings.append(_finding("invalid_accountable_owner", "RevocationPolicy requires a named Maysano accountableOwnerRole", object_id=object_id))
        triggers = item.get("suspensionTriggers")
        if not _is_string_list(triggers) or not MINIMUM_SUSPENSION_TRIGGERS.issubset(set(triggers)):
            findings.append(_finding("missing_suspension_triggers", "RevocationPolicy must include every minimum suspension trigger", object_id=object_id))
        thresholds = item.get("triggerThresholds")
        repeated_failure_threshold = thresholds.get("repeated_correction_rejection_or_safety_failure_threshold") if isinstance(thresholds, dict) else None
        if type(repeated_failure_threshold) is not int or repeated_failure_threshold < 1:
            findings.append(_finding("invalid_trigger_threshold", "RevocationPolicy must define a positive repeated correction, rejection, or safety-failure threshold", object_id=object_id))
        if item.get("severity") not in REVOCATION_SEVERITIES:
            findings.append(_finding("invalid_revocation_severity", "RevocationPolicy severity is unsupported", object_id=object_id))
        if item.get("immediateAction") not in REVOCATION_ACTIONS:
            findings.append(_finding("invalid_immediate_action", "RevocationPolicy immediateAction is unsupported", object_id=object_id))
        for field in ("evidenceRequirements", "restorationRequirements"):
            if not _is_string_list(item.get(field)) or not item[field]:
                findings.append(_finding("invalid_revocation_requirements", f"RevocationPolicy {field} must be a nonempty list of strings", object_id=object_id))
        if not _is_role_list(item.get("notificationTargets")):
            findings.append(_finding("invalid_notification_targets", "RevocationPolicy notificationTargets must name one or more Maysano roles", object_id=object_id))
        if not _is_timestamp(item.get("expiryOrReviewDate")):
            findings.append(_finding("invalid_revocation_review_date", "RevocationPolicy expiryOrReviewDate must be an ISO 8601 timestamp", object_id=object_id))
        if item.get("localStatus") not in LOCAL_REVOCATION_STATUSES:
            findings.append(_finding("invalid_local_revocation_status", "RevocationPolicy localStatus must be declared_active or simulated_suspended", object_id=object_id))
    elif kind == "execution_request":
        _validate_reference(item.get("execution_package_reference"), "execution_package_reference", object_id, findings)
        _validate_reference(item.get("revocation_policy_reference"), "revocation_policy_reference", object_id, findings)
        for field in ("action", "tool", "target"):
            if not isinstance(item.get(field), str) or not item[field]:
                findings.append(_finding("invalid_request", f"ExecutionRequest requires {field}", object_id=object_id))
        if type(item.get("requested_authority")) is not int or item["requested_authority"] not in {0, 1, 2, 3}:
            findings.append(_finding("invalid_authority", "requested_authority must be an integer from 0 to 3", object_id=object_id))
        if type(item.get("approval_required")) is not bool:
            findings.append(_finding("invalid_approval_flag", "approval_required must be true or false", object_id=object_id))
        if item.get("approval_expires_at") is not None and not _is_timestamp(item.get("approval_expires_at")):
            findings.append(_finding("invalid_approval_expiry", "approval_expires_at must be an ISO 8601 timestamp or null", object_id=object_id))
    elif kind == "evidence_event":
        _validate_reference(item.get("work_envelope_reference"), "work_envelope_reference", object_id, findings)
        if not item["source_references"]:
            findings.append(_finding("missing_evidence_sources", "EvidenceEvent requires at least one source reference", object_id=object_id))
        if not isinstance(item.get("event_type"), str) or not item["event_type"]:
            findings.append(_finding("invalid_event_type", "EvidenceEvent requires event_type", object_id=object_id))
        if not _is_timestamp(item.get("occurred_at")):
            findings.append(_finding("invalid_occurred_at", "EvidenceEvent requires occurred_at", object_id=object_id))
        if not isinstance(item.get("payload"), dict):
            findings.append(_finding("invalid_evidence_payload", "EvidenceEvent requires a JSON object payload", object_id=object_id))
    elif kind == "correction":
        _validate_reference(item.get("target_reference"), "target_reference", object_id, findings)
        if item.get("kind") not in {"output", "context", "mandate", "policy", "tool"}:
            findings.append(_finding("invalid_correction_kind", "Correction kind is unsupported", object_id=object_id))
        for field in ("destination", "summary"):
            if not isinstance(item.get(field), str) or not item[field]:
                findings.append(_finding("invalid_correction", f"Correction requires {field}", object_id=object_id))


def _validate_boundary(item: dict, object_id: str, findings: list[dict], label: str) -> None:
    for field in ("scope", "tools", "data_access", "approval_rights"):
        if not _is_string_list(item.get(field)):
            findings.append(_finding("invalid_boundary", f"{label} {field} must be a list of nonempty strings", object_id=object_id))
    if item.get("owner") is not None and (not isinstance(item.get("owner"), str) or not item["owner"]):
        findings.append(_finding("invalid_owner", f"{label} owner must be a nonempty string or null", object_id=object_id))
    if type(item.get("authority_level")) is not int or item["authority_level"] not in {0, 1, 2, 3}:
        findings.append(_finding("invalid_authority", f"{label} authority_level must be an integer from 0 to 3", object_id=object_id))


def index_objects(bundle: dict) -> dict[tuple[str, int], dict]:
    """Index local instances by stable ID and version after successful schema validation."""
    return {(item["id"], item["version"]): item for item in bundle["objects"]}


def _referenced(index: dict, reference: object) -> dict | None:
    if not isinstance(reference, dict):
        return None
    return index.get((reference.get("id"), reference.get("version")))


def _is_subset(child: object, parent: object) -> bool:
    return isinstance(child, list) and isinstance(parent, list) and set(child).issubset(parent)


def validate_bundle(bundle: dict) -> dict:
    """Validate schemas plus local relationships; this function has no side effects."""
    findings: list[dict] = []
    if bundle.get("schema_version") != SCHEMA_VERSION:
        findings.append(_finding("unsupported_bundle_schema", "Bundle schema_version must be 1"))
    objects = bundle.get("objects")
    if not isinstance(objects, list) or not objects:
        findings.append(_finding("invalid_bundle_objects", "Bundle objects must be a nonempty list"))
        return {"valid": False, "findings": findings}
    seen: set[tuple[str, int]] = set()
    for item in objects:
        _validate_object(item, findings)
        if isinstance(item, dict) and isinstance(item.get("id"), str) and type(item.get("version")) is int:
            key = (item["id"], item["version"])
            if key in seen:
                findings.append(_finding("duplicate_object_version", "Object id and version must be unique", object_id=item["id"]))
            seen.add(key)
    if findings:
        return {"valid": False, "findings": findings}
    index = index_objects(bundle)
    for item in objects:
        object_id = item["id"]
        if item["object_type"] == "work_envelope":
            mandate = _referenced(index, item["mandate_reference"])
            if not mandate or mandate.get("object_type") != "mandate":
                findings.append(_finding("missing_mandate", "WorkEnvelope must reference an existing Mandate version", object_id=object_id))
            else:
                for field in ("scope", "tools", "data_access", "approval_rights"):
                    if not _is_subset(item[field], mandate[field]):
                        findings.append(_finding("envelope_expands_mandate", f"WorkEnvelope {field} exceeds its Mandate", object_id=object_id))
                if item["authority_level"] > mandate["authority_level"]:
                    findings.append(_finding("envelope_expands_mandate", "WorkEnvelope authority_level exceeds its Mandate", object_id=object_id))
        elif item["object_type"] == "execution_package":
            envelope = _referenced(index, item["work_envelope_reference"])
            if not envelope or envelope.get("object_type") != "work_envelope":
                findings.append(_finding("missing_work_envelope", "ExecutionPackage must reference an existing WorkEnvelope version", object_id=object_id))
            else:
                for field in ("scope", "tools", "data_access", "approval_rights"):
                    if not _is_subset(item[field], envelope[field]):
                        findings.append(_finding("package_expands_envelope", f"ExecutionPackage {field} exceeds its WorkEnvelope", object_id=object_id))
                if item["authority_level"] > envelope["authority_level"]:
                    findings.append(_finding("package_expands_envelope", "ExecutionPackage authority_level exceeds its WorkEnvelope", object_id=object_id))
        elif item["object_type"] == "revocation_policy":
            chain = item["authorityChain"]
            mandate = _referenced(index, chain["mandate_reference"])
            envelope = _referenced(index, chain["work_envelope_reference"])
            if not mandate or mandate.get("object_type") != "mandate":
                findings.append(_finding("missing_revocation_mandate", "RevocationPolicy must reference an existing Mandate version", object_id=object_id))
            if not envelope or envelope.get("object_type") != "work_envelope":
                findings.append(_finding("missing_revocation_work_envelope", "RevocationPolicy must reference an existing WorkEnvelope version", object_id=object_id))
            elif mandate and envelope.get("mandate_reference") != chain["mandate_reference"]:
                findings.append(_finding("revocation_authority_chain_mismatch", "RevocationPolicy WorkEnvelope must belong to its referenced Mandate", object_id=object_id))
        elif item["object_type"] == "execution_request":
            package = _referenced(index, item["execution_package_reference"])
            if not package or package.get("object_type") != "execution_package":
                findings.append(_finding("missing_execution_package", "ExecutionRequest must reference an existing ExecutionPackage version", object_id=object_id))
                continue
            policy = _referenced(index, item["revocation_policy_reference"])
            if not policy or policy.get("object_type") != "revocation_policy":
                findings.append(_finding("missing_revocation_policy", "ExecutionRequest must reference an existing RevocationPolicy version", object_id=object_id))
                continue
            envelope = _referenced(index, package.get("work_envelope_reference"))
            mandate = _referenced(index, envelope.get("mandate_reference")) if envelope else None
            chain = policy["authorityChain"]
            if not envelope or not mandate or chain["work_envelope_reference"] != package["work_envelope_reference"] or chain["mandate_reference"] != envelope["mandate_reference"]:
                findings.append(_finding("revocation_policy_chain_mismatch", "ExecutionRequest RevocationPolicy must match its WorkEnvelope and Mandate chain", object_id=object_id))
    return {"valid": not findings, "findings": findings}
