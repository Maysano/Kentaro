"""Portable, deterministic DesignPortfolio model for local business design."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 2
MODEL_NAME = "DesignPortfolio"
CLAIM_STATUSES = {"case_fact", "user_confirmed", "proposed", "assumed", "unknown"}
ASSESSMENT_STAGES = {"discovery", "design", "implementation", "operation"}
KINDS = {"objective", "use_case", "ai_product", "data_product"}
RELATIONSHIPS = {
    "use-case-supports-objective": ("use_case", "objective"),
    "use-case-delivered-by-ai-product": ("use_case", "ai_product"),
    "use-case-requires-data-product": ("use_case", "data_product"),
    "ai-product-consumes-data-product": ("ai_product", "data_product"),
    "product-depends-on-product": (("ai_product", "data_product"), ("ai_product", "data_product")),
    "data-product-reused-by-use-case": ("data_product", "use_case"),
}
REQUIRED_OBJECT_CLAIMS = ("name", "purpose", "owner", "lifecycle_status")
CLAIM_FIELDS = {"value", "status", "source_id", "source_revision", "asserted_at", "derivation_input_hash"}


def content_hash(value: object) -> str:
    """Return a stable digest of the complete structured design input."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_claim(
    value: object,
    status: str,
    source_id: str,
    source_revision: str,
    derivation_input_hash: str,
    *,
    asserted_at: str | None = None,
) -> dict:
    return {
        "value": value,
        "status": status,
        "source_id": source_id,
        "source_revision": source_revision,
        "asserted_at": asserted_at or datetime.now(timezone.utc).isoformat(),
        "derivation_input_hash": derivation_input_hash,
    }


def _finding(code: str, message: str, object_id: str | None = None, severity: str = "blocker") -> dict:
    finding = {"code": code, "message": message, "severity": severity}
    if object_id:
        finding["object_id"] = object_id
    return finding


def is_claim(value: object) -> bool:
    return (
        isinstance(value, dict)
        and CLAIM_FIELDS <= set(value)
        and value["status"] in CLAIM_STATUSES
        and all(isinstance(value[field], str) and value[field] for field in CLAIM_FIELDS - {"value", "status"})
    )


def iter_claims(values: object, prefix: str = ""):
    """Yield canonical claims, including claims nested in business-information groups."""
    if is_claim(values):
        yield prefix, values
    elif isinstance(values, dict):
        for key, value in values.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            yield from iter_claims(value, label)


def _claims_are_canonical(values: object) -> bool:
    if is_claim(values):
        return True
    return isinstance(values, dict) and bool(values) and all(_claims_are_canonical(value) for value in values.values())


def migrate_portfolio(portfolio: object) -> dict:
    """Upgrade the v0.2 LearningPortfolio shape without losing its claims or links."""
    if not isinstance(portfolio, dict):
        raise ValueError("DesignPortfolio must be a JSON object")
    migrated = deepcopy(portfolio)
    if migrated.get("schema_version") == 1 and "model" not in migrated:
        migrated["schema_version"] = SCHEMA_VERSION
        migrated["model"] = MODEL_NAME
        if "case_id" in migrated:
            migrated["scenario_id"] = migrated.pop("case_id")
    # New local designs start in discovery. Older v0.2 files predate lifecycle-aware
    # reporting, so retain their facts while giving reports an explicit safe default.
    migrated.setdefault("assessment_stage", "discovery")
    migrated.setdefault("design_alternatives", [])
    return migrated


def create_design_portfolio(title: str, portfolio_id: str, *, revision: str = "draft-v1") -> dict:
    if not title.strip() or not portfolio_id.strip():
        raise ValueError("DesignPortfolio title and portfolio_id are required")
    return {
        "schema_version": SCHEMA_VERSION,
        "model": MODEL_NAME,
        "portfolio_id": portfolio_id,
        "title": title,
        "revision": revision,
        "assessment_stage": "discovery",
        "design_alternatives": [],
        "claims": {},
        "objects": [],
        "relationships": [],
    }


def validate_portfolio(portfolio: object) -> dict:
    try:
        design = migrate_portfolio(portfolio)
    except ValueError as error:
        return {"valid": False, "findings": [_finding("invalid_portfolio", str(error))]}
    findings: list[dict] = []
    for field in ("schema_version", "model", "portfolio_id", "title", "revision", "assessment_stage", "design_alternatives", "claims", "objects", "relationships"):
        if field not in design:
            findings.append(_finding("missing_field", f"DesignPortfolio requires {field}"))
    if design.get("schema_version") != SCHEMA_VERSION or design.get("model") != MODEL_NAME:
        findings.append(_finding("unsupported_schema", "DesignPortfolio schema_version must be 2"))
    if not all(isinstance(design.get(field), str) and design[field] for field in ("portfolio_id", "title", "revision")):
        findings.append(_finding("invalid_identity", "portfolio_id, title, and revision must be nonempty strings"))
    if design.get("assessment_stage") not in ASSESSMENT_STAGES:
        findings.append(_finding("invalid_assessment_stage", "assessment_stage must be discovery, design, implementation, or operation"))
    if not isinstance(design.get("design_alternatives"), list):
        findings.append(_finding("invalid_design_alternatives", "design_alternatives must be a list"))
    if not isinstance(design.get("claims"), dict) or (design["claims"] and not _claims_are_canonical(design["claims"])):
        findings.append(_finding("invalid_claims", "Portfolio claims must contain only canonical Claim values"))
    by_id: dict[str, str] = {}
    objects = design.get("objects")
    if not isinstance(objects, list):
        findings.append(_finding("invalid_objects", "objects must be a list"))
    else:
        for item in objects:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                findings.append(_finding("invalid_object", "Every object needs a nonempty id"))
                continue
            if item["id"] in by_id:
                findings.append(_finding("duplicate_object", "Object IDs must be unique", item["id"]))
            kind = item.get("kind")
            if kind not in KINDS:
                findings.append(_finding("invalid_kind", "Object kind is unsupported", item["id"]))
            else:
                by_id[item["id"]] = kind
            claims = item.get("claims")
            if not isinstance(claims, dict) or not _claims_are_canonical(claims):
                findings.append(_finding("invalid_claims", "Object claims must contain only canonical Claim values", item["id"]))
                continue
            for name in REQUIRED_OBJECT_CLAIMS:
                if not is_claim(claims.get(name)):
                    findings.append(_finding("invalid_claim", f"{name} must use the canonical Claim schema", item["id"]))
            if kind == "use_case" and "ai_involvement" in claims and not is_claim(claims["ai_involvement"]):
                findings.append(_finding("invalid_claim", "ai_involvement must use the canonical Claim schema", item["id"]))
    relationships = design.get("relationships")
    if not isinstance(relationships, list):
        findings.append(_finding("invalid_relationships", "relationships must be a list"))
    else:
        ids = set()
        for edge in relationships:
            if not isinstance(edge, dict) or not all(isinstance(edge.get(field), str) and edge[field] for field in ("id", "from_id", "to_id", "kind")):
                findings.append(_finding("invalid_relationship", "Relationship needs id, from_id, to_id, and kind"))
                continue
            if edge["id"] in ids:
                findings.append(_finding("duplicate_relationship", "Relationship IDs must be unique", edge["id"]))
            ids.add(edge["id"])
            if "provenance" in edge and not is_claim(edge["provenance"]):
                findings.append(_finding("invalid_relationship_provenance", "Relationship provenance must use the canonical Claim schema", edge["id"]))
            expected = RELATIONSHIPS.get(edge["kind"])
            if expected is None:
                findings.append(_finding("invalid_relationship_kind", "Relationship kind is unsupported", edge["id"]))
                continue
            source, target = by_id.get(edge["from_id"]), by_id.get(edge["to_id"])
            source_allowed = expected[0] if isinstance(expected[0], tuple) else (expected[0],)
            target_allowed = expected[1] if isinstance(expected[1], tuple) else (expected[1],)
            if source not in source_allowed or target not in target_allowed:
                findings.append(_finding("invalid_relationship_endpoints", "Relationship endpoints do not match its semantic predicate", edge["id"]))
    if isinstance(design.get("design_alternatives"), list):
        alternative_ids = set()
        for alternative in design["design_alternatives"]:
            if not isinstance(alternative, dict) or not all(isinstance(alternative.get(field), str) and alternative[field] for field in ("id", "name")):
                findings.append(_finding("invalid_design_alternative", "Every design alternative needs a nonempty id and name"))
                continue
            if alternative["id"] in alternative_ids:
                findings.append(_finding("duplicate_design_alternative", "Design alternative IDs must be unique", alternative["id"]))
            alternative_ids.add(alternative["id"])
            for field in ("object_ids", "shared_object_ids"):
                values = alternative.get(field, [])
                if not isinstance(values, list) or not all(isinstance(value, str) and value in by_id for value in values):
                    findings.append(_finding("invalid_design_alternative_members", f"{field} must contain known design object IDs", alternative["id"]))
    return {"valid": not findings, "findings": findings, "content_hash": content_hash(design), "portfolio": design}


def load_portfolio(path: str | Path) -> dict:
    try:
        return migrate_portfolio(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("DesignPortfolio must be a readable JSON file") from error


def save_portfolio(portfolio: dict, path: str | Path) -> Path:
    result = validate_portfolio(portfolio)
    if not result["valid"]:
        raise ValueError("DesignPortfolio is invalid")
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result["portfolio"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def add_object(portfolio: dict, object_id: str, kind: str, claims: dict) -> dict:
    updated = migrate_portfolio(portfolio)
    updated["objects"].append({"id": object_id, "kind": kind, "claims": deepcopy(claims)})
    return updated


def add_relationship(portfolio: dict, relationship_id: str, from_id: str, to_id: str, kind: str, *, provenance: dict | None = None) -> dict:
    updated = migrate_portfolio(portfolio)
    relationship = {"id": relationship_id, "from_id": from_id, "to_id": to_id, "kind": kind}
    if provenance is not None:
        relationship["provenance"] = deepcopy(provenance)
    updated["relationships"].append(relationship)
    return updated


def set_claim(portfolio: dict, field: str, claim: dict, *, object_id: str | None = None) -> dict:
    updated = migrate_portfolio(portfolio)
    if object_id is None:
        updated["claims"][field] = deepcopy(claim)
        return updated
    for item in updated["objects"]:
        if item["id"] == object_id:
            item["claims"][field] = deepcopy(claim)
            return updated
    raise ValueError(f"Unknown design object: {object_id}")
