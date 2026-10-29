"""Persistent engagement state derived from the authoritative DesignPortfolio.

The state file is an operational index, not a second design record.  It is
regenerated from the portfolio so a later agent never needs to infer progress
from a chat transcript or an old handover package.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .portfolio import content_hash, iter_claims, validate_portfolio
from .reports import analysis, readiness
from .specifications import structural_completion


STATE_FILENAME = "engagement-state.json"
SCHEMA_VERSION = 2


def state_path(portfolio_path: str | Path) -> Path:
    """Return the one local engagement-state file for a portfolio directory."""
    return Path(portfolio_path).expanduser().resolve().parent / STATE_FILENAME


def _claim_summary(portfolio: dict) -> dict:
    statuses = Counter()
    groups = Counter()
    sources = [portfolio["claims"]] + [item["claims"] for item in portfolio["objects"]]
    for claims in sources:
        for _, claim in iter_claims(claims):
            statuses[claim["status"]] += 1
            if claim["status"] in {"case_fact", "user_confirmed"}:
                groups["confirmed"] += 1
            elif claim["status"] in {"proposed", "assumed"}:
                groups["proposed"] += 1
            else:
                groups["unknown"] += 1
    return {
        "by_status": dict(sorted(statuses.items())),
        "confirmed": groups["confirmed"],
        "proposed": groups["proposed"],
        "unknown": groups["unknown"],
    }


def _required_deliverables(completion: dict, delivery: dict | None) -> dict:
    findings = completion.get("findings", [])
    codes = {item.get("code", "") for item in findings}
    def status_for(relevant_codes: set[str], *prefixes: str) -> str:
        missing = bool(codes & relevant_codes) or any(code.startswith(prefix) for code in codes for prefix in prefixes)
        return "missing_requirements" if missing else "complete"

    structurally_complete = bool(completion.get("structurally_complete"))
    final_state = "awaiting_explicit_review_and_confirmation" if structurally_complete else "blocked_by_missing_requirements"
    if delivery and delivery.get("source_hash") and delivery.get("source_hash") != completion.get("portfolio_hash"):
        final_state = "stale_after_portfolio_change"
    if delivery and delivery.get("source_hash") == completion.get("portfolio_hash"):
        final_state = delivery.get("status", final_state)
    specifications = "not_generated" if structurally_complete else "blocked_by_missing_requirements"
    if delivery and delivery.get("source_hash") == completion.get("portfolio_hash") and delivery.get("specifications_generated"):
        specifications = "generated_and_validated"
    return {
        "design_portfolio": {"status": "current"},
        "business_objectives": {"status": status_for({"missing_objective", "missing_objective_outcome"})},
        "business_kpis_and_targets": {"status": status_for({"missing_objective_kpi"})},
        "use_cases": {"status": status_for({"missing_use_case", "unlinked_use_case"}, "missing_use_case_")},
        "data_products": {"status": status_for({"missing_data_product", "unlinked_data_product"}, "missing_data_product_")},
        "product_kpis_and_targets": {"status": status_for({"missing_data_product_kpi"})},
        "odps_family_specifications": {"status": specifications},
        "odpg_relationship_graph": {"status": specifications},
        "final_handover_package": {"status": final_state},
    }


def _element_hashes(design: dict) -> dict:
    """Small fingerprints permit impact evaluation without duplicating the portfolio."""
    return {
        "portfolio": content_hash({"claims": design["claims"], "revision": design["revision"], "assessment_stage": design["assessment_stage"]}),
        "objects": {item["id"]: content_hash({"kind": item["kind"], "claims": item["claims"]}) for item in design["objects"]},
        "relationships": {item["id"]: content_hash(item) for item in design["relationships"]},
    }


def _changed_ids(current: dict, previous: dict | None, key: str) -> list[str]:
    if not previous:
        return sorted(current[key])
    old = previous.get(key, {})
    unchanged = {item for item in set(old) & set(current[key]) if old[item] == current[key][item]}
    return sorted((set(old) | set(current[key])) - unchanged)


def _topics(missing: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    names = {
        "missing_objective": "Business objectives",
        "missing_objective_outcome": "Business outcomes",
        "missing_objective_kpi": "Business KPI targets",
        "missing_use_case": "Use-case definition and links",
        "unlinked_use_case": "Use-case to objective links",
        "missing_data_product": "Data-product definition and links",
        "unlinked_data_product": "Use-case to data-product links",
        "missing_data_product_kpi": "Product KPI targets",
    }
    for finding in missing:
        code = finding.get("code", "")
        topic = names.get(code)
        if not topic:
            if code.startswith("missing_use_case_"):
                topic = "Use-case definition"
            elif code.startswith("missing_data_product_"):
                topic = "Data-product definition and service expectations"
            else:
                topic = "Portfolio validation"
        grouped.setdefault(topic, []).append(finding)
    return [{"topic": topic, "items": items} for topic, items in sorted(grouped.items())]


def _evaluation(design: dict, checked: dict, completion: dict, readiness_result: dict, previous: dict | None, delivery: dict | None) -> dict:
    current = _element_hashes(design)
    prior = previous.get("evaluation", {}).get("element_hashes") if previous else None
    changed_objects = _changed_ids(current, prior, "objects")
    changed_relationships = _changed_ids(current, prior, "relationships")
    impacted_relationships = [edge["id"] for edge in design["relationships"] if edge["id"] in changed_relationships or edge["from_id"] in changed_objects or edge["to_id"] in changed_objects]
    reconsideration = []
    if prior and current["portfolio"] != prior.get("portfolio"):
        reconsideration.append({"kind": "derived_outputs", "reason": "The authoritative portfolio changed; regenerate or re-check rendered reports and handover material."})
    if delivery and delivery.get("source_hash") and delivery["source_hash"] != checked["content_hash"]:
        reconsideration.append({"kind": "handover", "reason": "The recorded handover was generated from an older portfolio hash and is stale."})
    missing = completion.get("findings", [])
    decisions = [item for item in readiness_result["findings"] if item["category"] == "decision_dependency"]
    question = completion.get("discovery_questions", [None])[0] if completion.get("discovery_questions") else None
    highest_priority = (
        {"type": "missing_requirement", "finding": missing[0], "question": question}
        if missing else ({"type": "unresolved_decision", "finding": decisions[0]} if decisions else {"type": "review_confirmation", "question": "Ask for explicit human review and confirmation before final handover generation."})
    )
    return {
        "ran_for_current_interaction": True,
        "portfolio_validation": {"valid": checked["valid"], "finding_count": len(checked["findings"])},
        "design_skeleton": {"complete": completion.get("structurally_complete", False), "finding_count": len(missing)},
        "relationship_consistency": {"relationship_count": len(design["relationships"]), "analysis_valid": analysis(design)["valid"]},
        "affected_elements": {
            "portfolio_changed": not prior or current["portfolio"] != prior.get("portfolio"),
            "object_ids": changed_objects,
            "relationship_ids": changed_relationships,
            "impacted_relationship_ids": sorted(impacted_relationships),
        },
        "items_requiring_reconsideration": reconsideration,
        "highest_priority": highest_priority,
        "next_best_action": "Address the user's immediate request; then ask the highest-priority targeted discovery question if it remains unresolved.",
        "element_hashes": current,
    }


def build_engagement_state(portfolio: dict, *, portfolio_path: str | Path, delivery: dict | None = None, previous: dict | None = None) -> dict:
    """Build a transparent, persistent engagement index from one valid portfolio."""
    checked = validate_portfolio(portfolio)
    if not checked["valid"]:
        raise ValueError("Cannot create engagement state from an invalid DesignPortfolio")
    design = checked["portfolio"]
    completion = structural_completion(design)
    readiness_result = readiness(design)
    decision_dependencies = [item for item in readiness_result["findings"] if item["category"] == "decision_dependency"]
    missing = completion.get("findings", [])
    questions = completion.get("discovery_questions", [])
    next_requirement = questions[0] if questions else (
        "Ask the human reviewer to confirm the provisional design and acknowledge unresolved decisions before generating the final handover package."
        if completion.get("structurally_complete") else "Resolve the invalid portfolio before continuing."
    )
    source_path = Path(portfolio_path).expanduser().resolve()
    return {
        "schema_version": SCHEMA_VERSION,
        "model": "KentaroDesignEngagementState",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "authoritative_source": {
            "portfolio_path": str(source_path),
            "portfolio_id": design["portfolio_id"],
            "revision": design["revision"],
            "content_hash": checked["content_hash"],
        },
        "required_deliverables": _required_deliverables(completion, delivery),
        "claim_summary": _claim_summary(design),
        "missing_requirements": missing,
        "topics_to_resolve": _topics(missing),
        "unresolved_decisions": decision_dependencies,
        "next_unresolved_requirement": next_requirement,
        "structural_completion": {
            "complete": completion.get("structurally_complete", False),
            "limitations": completion.get("limitations", []),
        },
        "handover": delivery or {"status": "not_generated", "source_hash": checked["content_hash"]},
        "evaluation": _evaluation(design, checked, completion, readiness_result, previous, delivery),
    }


def update_engagement_state(
    portfolio: dict,
    portfolio_path: str | Path,
    *,
    delivery: dict | None = None,
) -> tuple[Path, dict]:
    """Refresh the local state from the portfolio and return its location and data."""
    destination = state_path(portfolio_path)
    preserved_delivery = delivery
    previous = None
    if destination.exists():
        try:
            existing = json.loads(destination.read_text(encoding="utf-8"))
            previous = existing if isinstance(existing, dict) else None
            existing_delivery = existing.get("handover")
            if preserved_delivery is None and isinstance(existing_delivery, dict):
                preserved_delivery = existing_delivery
        except (OSError, json.JSONDecodeError):
            # A malformed generated state must never override the authoritative portfolio.
            preserved_delivery = None
    state = build_engagement_state(portfolio, portfolio_path=portfolio_path, delivery=preserved_delivery, previous=previous)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination, state


def load_engagement_state(path: str | Path) -> dict:
    """Read an existing generated engagement state without treating it as authority."""
    try:
        state = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Engagement state must be a readable JSON file") from error
    if state.get("schema_version") not in {1, SCHEMA_VERSION} or state.get("model") != "KentaroDesignEngagementState":
        raise ValueError("Unsupported engagement state schema")
    return state
