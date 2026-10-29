"""Deterministic analysis, reports, manifests, and ODPS validation for DesignPortfolio."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from .portfolio import ASSESSMENT_STAGES, content_hash, is_claim, iter_claims, validate_portfolio


CONFIRMED_CLAIM_STATUSES = {"case_fact", "user_confirmed"}
FINDING_CATEGORY_ORDER = {"implementation_blocker": 0, "decision_dependency": 1, "design_gap": 2}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _display(value: object) -> str:
    return json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)


def _claim_status(claim: dict | None) -> str:
    if not claim:
        return "unknown"
    if claim["status"] in CONFIRMED_CLAIM_STATUSES:
        return "established"
    if claim["status"] in {"proposed", "assumed"}:
        return "proposed"
    return "unknown"


def _first_claim(claims: dict, *fields: str) -> tuple[str | None, dict | None]:
    for field in fields:
        value = claims.get(field)
        if is_claim(value):
            return field, value
    return None, None


def _claim_id(object_id: str, field: str) -> str:
    return f"claim:{object_id}:{field}"


def _finding_category(field: str, item_kind: str | None, stage: str) -> tuple[str, str, str]:
    label = field.lower().replace("-", "_")
    if any(token in label for token in ("owner", "authority", "boundary", "policy", "decision")):
        return "decision_dependency", "high", "An accountable business, product, or governance decision is required."
    implementation_sensitive = any(token in label for token in ("eligibility", "rule", "authorization", "access", "contract", "interface", "human_oversight", "security", "freshness", "quality"))
    if item_kind == "ai_product" and label in {"human_oversight", "oversight"}:
        implementation_sensitive = True
    if implementation_sensitive and stage in {"implementation", "operation"}:
        return "implementation_blocker", "critical", "This must be resolved before the requested implementation or operation can proceed safely."
    if implementation_sensitive:
        return "design_gap", "high", "Investigate and make the required design decision before implementation."
    return "design_gap", "medium", "Investigate or explicitly retain this information gap during design."


def _readiness_finding(
    *, object_id: str, item_kind: str | None, field: str, claim: dict, stage: str
) -> dict:
    category, severity, required_resolution = _finding_category(field, item_kind, stage)
    state = claim["status"].replace("_", " ")
    source_claim_id = _claim_id(object_id, field)
    key = f"{object_id}|{field}|{category}|{stage}"
    return {
        "finding_id": f"finding:{sha256(key.encode('utf-8')).hexdigest()[:16]}",
        "affected_object_id": object_id,
        "category": category,
        "severity": severity,
        "assessment_stage": stage,
        "field": field,
        "explanation": f"{field.replace('_', ' ')} is {state}; it is not established evidence.",
        "required_resolution": required_resolution,
        "source_claim_ids": [source_claim_id],
        "dependency_references": [f"{claim['source_id']}@{claim['source_revision']}"],
    }


def readiness(portfolio: dict, *, assessment_stage: str | None = None) -> dict:
    check = validate_portfolio(portfolio)
    if not check["valid"]:
        return {"valid": False, "findings": check["findings"], "portfolio_hash": check.get("content_hash")}
    stage = assessment_stage or check["portfolio"]["assessment_stage"]
    if stage not in ASSESSMENT_STAGES:
        raise ValueError("assessment_stage must be discovery, design, implementation, or operation")
    findings = []
    sources = [("portfolio", None, check["portfolio"]["claims"])] + [(item["id"], item["kind"], item["claims"]) for item in check["portfolio"]["objects"]]
    for object_id, item_kind, claims in sources:
        for field, claim in iter_claims(claims):
            if claim["status"] not in CONFIRMED_CLAIM_STATUSES:
                findings.append(_readiness_finding(object_id=object_id, item_kind=item_kind, field=field, claim=claim, stage=stage))
    findings.sort(key=lambda item: (FINDING_CATEGORY_ORDER[item["category"]], SEVERITY_ORDER[item["severity"]], item["affected_object_id"], item["field"]))
    category_counts = dict(Counter(item["category"] for item in findings))
    severity_counts = dict(Counter(item["severity"] for item in findings))
    return {
        "valid": True,
        "portfolio_hash": check["content_hash"],
        "assessment_stage": stage,
        "findings": findings,
        "summary": {
            "by_category": {category: category_counts.get(category, 0) for category in FINDING_CATEGORY_ORDER},
            "by_severity": {severity: severity_counts.get(severity, 0) for severity in SEVERITY_ORDER},
            # Retained only for callers of the previous compact shape. A blocker is now
            # specifically an implementation blocker, never every unknown discovery claim.
            "blockers": category_counts.get("implementation_blocker", 0),
            "warnings": len(findings) - category_counts.get("implementation_blocker", 0),
        },
    }


def _data_product_qualification(design: dict, item: dict) -> dict:
    object_id = item["id"]
    claims = item["claims"]
    consumers = []
    for edge in design["relationships"]:
        if edge["to_id"] != object_id or edge["kind"] not in {"use-case-requires-data-product", "ai-product-consumes-data-product"}:
            continue
        source = next(candidate for candidate in design["objects"] if candidate["id"] == edge["from_id"])
        name = source["claims"]["name"]
        consumers.append({"object_id": source["id"], "name": name["value"], "status": _claim_status(name), "relationship_id": edge["id"]})
    _, boundary = _first_claim(claims, "product_boundary", "consumer_boundary")
    _, capability = _first_claim(claims, "consumption_capability", "data_capability", "service_capability")
    _, interface = _first_claim(claims, "interface", "service_model", "access_interface")
    _, ownership = _first_claim(claims, "owner", "product_owner")
    _, lifecycle = _first_claim(claims, "lifecycle_status", "lifecycle")
    purpose_status = _claim_status(claims.get("purpose"))
    # A named relationship supplies consumer demand. Its status is only established
    # when the linked consumer's identity is established; relationships are otherwise proposed.
    consumer_status = "established" if any(value["status"] == "established" for value in consumers) else ("proposed" if consumers else "unknown")
    criteria = {
        "business_purpose_and_value": purpose_status,
        "identified_consumer_demand": consumer_status,
        "consumer_oriented_product_boundary": _claim_status(boundary),
        "recognizable_consumption_capability": _claim_status(capability),
        "intended_interface_and_service_model": _claim_status(interface),
        "ownership_and_lifecycle_responsibility": "unknown" if "unknown" in {_claim_status(ownership), _claim_status(lifecycle)} else ("proposed" if "proposed" in {_claim_status(ownership), _claim_status(lifecycle)} else "established"),
    }
    core = tuple(criteria[key] for key in ("business_purpose_and_value", "identified_consumer_demand", "consumer_oriented_product_boundary", "recognizable_consumption_capability", "intended_interface_and_service_model"))
    candidate = all(status in {"established", "proposed"} for status in core)
    qualified = candidate and all(status == "established" for status in core)
    return {
        "object_id": object_id,
        "criteria": criteria,
        "classification": "qualified_design_concept" if qualified else ("candidate_data_product" if candidate else "information_requirement"),
        "candidate_data_product": candidate,
        "qualified_design_concept": qualified,
        "implementation_ready": False,
        "operational_data_product": False,
        "consumer_count": len(consumers),
    }


def _reuse_assessment(design: dict, item: dict) -> dict:
    object_id = item["id"]
    consumers = []
    for edge in design["relationships"]:
        if edge["to_id"] == object_id and edge["kind"] in {"use-case-requires-data-product", "ai-product-consumes-data-product"}:
            source = next(candidate for candidate in design["objects"] if candidate["id"] == edge["from_id"])
            consumer = {"object_id": source["id"], "relationship_id": edge["id"], "name": source["claims"]["name"]["value"], "status": _claim_status(source["claims"]["name"])}
            consumers.append(consumer)
    return {
        "object_id": object_id,
        "existing_confirmed_consumers": [item for item in consumers if item["status"] == "established"],
        "additional_proposed_consumers": [item for item in consumers if item["status"] != "established"],
        "potential_reuse_across_objectives_or_use_cases": len(consumers) > 1,
        "shared_semantic_and_data_capabilities": _claim_status(_first_claim(item["claims"], "shared_semantics", "data_capability", "consumption_capability")[1]),
        "constraints_limiting_reuse": _claim_status(_first_claim(item["claims"], "reuse_constraints", "access_constraints")[1]),
    }


def analysis(portfolio: dict, *, assessment_stage: str | None = None) -> dict:
    check = validate_portfolio(portfolio)
    if not check["valid"]:
        return {"valid": False, "findings": check["findings"]}
    design = check["portfolio"]
    objects = {item["id"]: item for item in design["objects"]}
    usage = Counter(edge["to_id"] for edge in design["relationships"] if edge["kind"] in {"ai-product-consumes-data-product", "use-case-requires-data-product", "use-case-delivered-by-ai-product"})
    reusable = [{"object_id": object_id, "name": objects[object_id]["claims"]["name"]["value"], "used_by": count} for object_id, count in sorted(usage.items()) if count > 1]
    readiness_result = readiness(design, assessment_stage=assessment_stage)
    data_products = [item for item in design["objects"] if item["kind"] == "data_product"]
    return {"valid": True, "portfolio_hash": check["content_hash"], "assessment_stage": readiness_result["assessment_stage"], "object_counts": dict(Counter(item["kind"] for item in design["objects"])), "relationship_count": len(design["relationships"]), "reuse_opportunities": reusable, "data_product_qualification": [_data_product_qualification(design, item) for item in data_products], "reuse_assessment": [_reuse_assessment(design, item) for item in data_products], "readiness": readiness_result["summary"]}


def executive_summary(portfolio: dict, assessment: dict) -> str:
    check = validate_portfolio(portfolio)
    design = check["portfolio"]
    names = {kind: [str(item["claims"]["name"]["value"]) for item in design["objects"] if item["kind"] == kind] for kind in ("objective", "use_case", "ai_product", "data_product")}
    list_or_none = lambda values: ", ".join(values) if values else "None yet"
    return "\n".join((
        f"# {design['title']} — Executive Summary", "",
        "**Status:** local design artefact. It is not a business approval, system of record, or production-readiness assessment.", "",
        f"## Objectives\n\n{list_or_none(names['objective'])}", "",
        f"## Use cases\n\n{list_or_none(names['use_case'])}", "",
        f"## AI products\n\n{list_or_none(names['ai_product'])}", "",
        f"## Data products\n\n{list_or_none(names['data_product'])}", "",
        f"## Readiness\n\nAssessment stage: {assessment['assessment_stage']}. {assessment['summary']['by_category']['implementation_blocker']} implementation blocker(s), {assessment['summary']['by_category']['decision_dependency']} decision dependency/dependencies, and {assessment['summary']['by_category']['design_gap']} design gap(s). Validation and this report do not establish production readiness.", "",
        "## Next actions\n\n1. Confirm accountable owners, measurable outcomes, and supporting evidence.\n2. Review dependencies, access needs, and delivery constraints.\n3. Resolve or explicitly retain open decisions, then regenerate local outputs.", "",
        f"Input hash: `{assessment['portfolio_hash']}`.", "",
    ))


def unresolved_decisions(portfolio: dict, assessment: dict) -> str:
    design = validate_portfolio(portfolio)["portfolio"]
    counts = assessment["summary"]["by_category"]
    lines = [f"# {design['title']} — Unresolved Decisions", "", "This is a local design review, not a Maysano decision record or approval request.", "", f"Assessment stage: {assessment['assessment_stage']}. {counts['implementation_blocker']} implementation blocker(s), {counts['decision_dependency']} decision dependency/dependencies, and {counts['design_gap']} design gap(s).", ""]
    for finding in assessment["findings"]:
        if finding["category"] != "decision_dependency":
            continue
        lines.extend((f"## {finding['affected_object_id']} · {finding['field'].replace('_', ' ')}", "", f"- Severity: `{finding['severity']}`", f"- Explanation: {finding['explanation']}", f"- Required human action: {finding['required_resolution']}", f"- Source reference: `{', '.join(finding['dependency_references'])}`", ""))
    return "\n".join(lines)


def manifest(portfolio: dict, outputs: dict[str, Path]) -> dict:
    design = validate_portfolio(portfolio)["portfolio"]
    digest = content_hash(design)
    return {"schema_version": 1, "portfolio_model": "DesignPortfolio", "portfolio_hash": digest, "source_revision": design["revision"], "generated_at": datetime.now(timezone.utc).isoformat(), "dependency_manifest": [{"kind": "design_portfolio", "content_hash": digest, "source_revision": design["revision"]}], "artifacts": [{"name": name, "path": str(path), "input_hash": digest, "source_revision": design["revision"], "stale": False} for name, path in outputs.items()]}


def stale_outputs(portfolio: dict, manifest_data: dict) -> list[dict]:
    design = validate_portfolio(portfolio)["portfolio"]
    digest = content_hash(design)
    return [{**artifact, "stale": artifact.get("input_hash") != digest or artifact.get("source_revision") != design["revision"]} for artifact in manifest_data.get("artifacts", [])]


def validate_odps(path: str | Path) -> dict:
    """Use the pinned SDK CLI as the only ODPS structural validator."""
    try:
        import open_data_products
    except ImportError as error:
        raise ValueError('ODPS validation requires `pip install "kentaro[odps]"`.') from error
    if getattr(open_data_products, "__version__", None) != "0.4.0":
        raise ValueError("Design validation requires open-data-products 0.4.0")
    completed = subprocess.run([sys.executable, "-m", "open_data_products.cli", "validate", str(Path(path).resolve()), "--json"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {"valid": False, "errors": [completed.stderr or "SDK did not return JSON"]}
    result["sdk_version"] = "0.4.0"
    return result
