"""Ephemeral company-graph context for connected business design.

The Maysano pilot API specifies ``Cache-Control: no-store``.  This module
therefore keeps source records only in memory for the active design operation.
It can persist a small provenance-only marker in a DesignPortfolio, but never a
copy of the company graph.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import re

from .portfolio import make_claim


_STOP_WORDS = frozenset({
    "a", "an", "and", "assessment", "business", "case", "data", "for", "from",
    "improve", "in", "of", "or", "our", "process", "product", "service", "the",
    "to", "use", "we", "with",
})


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]{3,}", value.lower()) if term not in _STOP_WORDS}


VERIFICATION_STATES = frozenset({"verified", "stale", "unverified", "source_unavailable"})


def unavailable_context(reason: str = "No configured Maysano connection was available.", *, session_mode: str = "auto") -> dict:
    """Return an explicit local-only context; this is not a failed graph read."""
    return {
        "mode": "local_unverified",
        "session_mode": session_mode,
        "available": False,
        "verification_status": "source_unavailable" if session_mode == "graph_connected" else "unverified",
        "requires_revalidation": session_mode == "graph_connected",
        "next_action": "Retry retrieval, configure the Maysano connection, or explicitly switch to local design." if session_mode == "graph_connected" else "Continue as local design or configure Maysano before asking for graph verification.",
        "reason": reason,
        "records": [],
        "relationships": [],
        "limitations": [
            "No authoritative company-graph context was retrieved.",
            "Reuse, duplication, and dependency findings are not verified against Maysano.",
        ],
    }


def initialize_company_context(snapshot: dict, *, source_kind: str, session_mode: str = "auto") -> dict:
    """Validate and hold one existing reader snapshot for the active operation."""
    records = snapshot.get("records")
    relationships = snapshot.get("relationships")
    if not isinstance(records, list) or not isinstance(relationships, list):
        raise ValueError("Company graph reader returned an invalid context")
    counts = Counter(record.get("kind") for record in records)
    return {
        "mode": "connected",
        "session_mode": session_mode,
        "available": True,
        "verification_status": "verified" if source_kind == "maysano" else "unverified",
        "requires_revalidation": source_kind == "maysano",
        "next_action": "Use the Maysano source before treating graph conclusions as verified." if source_kind != "maysano" else "Review any reuse candidates before proposing a new capability.",
        "source_kind": source_kind,
        "source_label": snapshot.get("source_label", "Synthetic Maysano demo" if source_kind == "demo" else "Maysano source"),
        "scope": snapshot.get("scope", "not supplied"),
        "retrieved_at": snapshot.get("retrieved_at", "not supplied"),
        "record_counts": dict(sorted((str(kind), count) for kind, count in counts.items())),
        "relationship_count": len(relationships),
        "limitations": list(snapshot.get("limitations", [])),
        # Deliberately ephemeral: callers use these during this operation only.
        "records": records,
        "relationships": relationships,
    }


def match_business_intent(context: dict, business_input: str) -> dict:
    """Find transparent, lexical candidates without asserting semantic equivalence."""
    if not context.get("available"):
        return {
            "status": "unverified",
            "reason": context["reason"],
            "matches": [],
            "recommendation": "Continue as a local proposal; do not claim graph-verified reuse, duplication, or dependencies.",
        }
    intent = _terms(business_input)
    matches = []
    for record in context["records"]:
        title = record.get("title")
        if not isinstance(title, str):
            continue
        overlap = sorted(intent & _terms(title))
        if overlap:
            matches.append({
                "id": record.get("id"), "kind": record.get("kind"), "title": title,
                "source_ref": record.get("source_ref"), "matching_terms": overlap,
                "source_revision": record.get("version", "not supplied"),
            })
    matches.sort(key=lambda item: (-len(item["matching_terms"]), str(item["kind"]), str(item["id"])))
    products = [item for item in matches if item["kind"] == "data_product"]
    if products:
        recommendation = "Evaluate the matched existing data product(s) for reuse before proposing another product; suitability remains to be confirmed."
    elif matches:
        recommendation = "Review the matched existing objective or use case before treating this as a new capability; lexical similarity alone is not duplication evidence."
    else:
        recommendation = "No lexical match was found in the retrieved scope; this does not prove that no reusable capability exists."
    return {"status": "available", "matches": matches, "recommendation": recommendation}


def provenance_marker(context: dict, findings: dict) -> dict:
    """Return only durable provenance and result labels, never graph records or titles."""
    if not context.get("available"):
        return {
            "mode": "local_unverified",
            "session_mode": context.get("session_mode", "auto"),
            "availability": "unavailable",
            "verification_status": context.get("verification_status", "unverified"),
            "requires_revalidation": bool(context.get("requires_revalidation")),
            "next_action": context.get("next_action"),
            "reason": context["reason"],
            "reuse_status": "not_verified",
        }
    source_references = [
        {"source_ref": item["source_ref"], "source_revision": str(item.get("source_revision", "not supplied")), "verified_at": context["retrieved_at"]}
        for item in findings["matches"] if isinstance(item.get("source_ref"), str) and item["source_ref"]
    ]
    return {
        "mode": "connected",
        "session_mode": context.get("session_mode", "auto"),
        "availability": "available",
        "verification_status": context.get("verification_status", "unverified"),
        "requires_revalidation": bool(context.get("requires_revalidation")),
        "next_action": context.get("next_action"),
        "source_kind": context["source_kind"],
        "source_label": context["source_label"],
        "scope": context["scope"],
        "retrieved_at": context["retrieved_at"],
        "record_counts": context["record_counts"],
        "relationship_count": context["relationship_count"],
        "match_count": len(findings["matches"]),
        "source_references": source_references,
        "reuse_status": "candidates_require_evaluation" if findings["matches"] else "no_lexical_match_in_retrieved_scope",
        "limitations": context["limitations"],
    }


def attach_context_marker(portfolio: dict, context: dict, findings: dict) -> dict:
    """Attach source metadata to the local proposal without embedding company content."""
    marker = provenance_marker(context, findings)
    status = "case_fact" if context.get("available") else "unknown"
    source_id = "maysano:company-graph" if context.get("available") else "kentaro:local-design"
    revision = str(marker.get("retrieved_at", "not-retrieved"))
    portfolio["claims"]["company_graph_context"] = make_claim(
        marker, status, source_id, revision, "company-graph-context-v1"
    )
    return portfolio


def revalidate_company_context(portfolio: dict, context: dict) -> tuple[dict, dict]:
    """Refresh source-safe graph provenance and flag only affected local conclusions.

    The graph payload never leaves the active operation.  Persisted comparison
    data contains only source references, versions, timestamps, and local IDs.
    """
    prior_claim = portfolio.get("claims", {}).get("company_graph_context", {})
    prior = prior_claim.get("value", {}) if isinstance(prior_claim, dict) else {}
    updated = deepcopy(portfolio)
    if not context.get("available"):
        if context.get("session_mode") == "local":
            marker = provenance_marker(context, {"matches": []})
            updated["claims"]["company_graph_context"] = make_claim(marker, "unknown", "kentaro:local-design", "not-retrieved", "company-graph-context-v1")
            return updated, {
                "verification_status": "unverified", "changed": False,
                "affected_claims": [], "affected_object_ids": [], "affected_relationship_ids": [],
                "next_action": marker.get("next_action"),
            }
        marker = deepcopy(prior) if isinstance(prior, dict) else {}
        marker.update({
            "mode": marker.get("mode", "local_unverified"),
            "availability": "unavailable",
            "verification_status": "source_unavailable",
            "requires_revalidation": True,
            "last_revalidation_at": None,
            "reason": context.get("reason", "Company graph context is unavailable."),
            "next_action": context.get("next_action", "Retry retrieval or explicitly switch to local design."),
        })
        updated["claims"]["company_graph_context"] = make_claim(marker, "unknown", "maysano:company-graph", "unavailable", "company-graph-revalidation-v1")
        return updated, {
            "verification_status": "source_unavailable", "changed": False,
            "affected_claims": ["company_graph_context"], "affected_object_ids": [], "affected_relationship_ids": [],
            "next_action": marker["next_action"],
        }
    business_input = updated.get("claims", {}).get("initial_business_input", {}).get("value", "")
    findings = match_business_intent(context, business_input if isinstance(business_input, str) else "")
    marker = provenance_marker(context, findings)
    before = {(item.get("source_ref"), item.get("source_revision")) for item in prior.get("source_references", []) if isinstance(item, dict)}
    after = {(item.get("source_ref"), item.get("source_revision")) for item in marker.get("source_references", [])}
    changed_references = sorted(
        {reference for reference, _ in before ^ after if isinstance(reference, str)}
    )
    affected_object_ids = [item["id"] for item in updated.get("objects", []) if item.get("kind") == "data_product"]
    affected_relationship_ids = [
        edge["id"] for edge in updated.get("relationships", [])
        if edge.get("from_id") in affected_object_ids or edge.get("to_id") in affected_object_ids
    ]
    # A later read with the same source revision does not erase a material
    # reconsideration obligation.  Only an explicit linked human decision can.
    changed = bool(changed_references) or (
        prior.get("verification_status") == "stale" and bool(prior.get("requires_revalidation"))
    )
    marker.update({
        "last_revalidation_at": context.get("retrieved_at"),
        "verification_status": "stale" if changed else "verified",
        "requires_revalidation": changed,
        "changed_source_references": changed_references,
        "affected_object_ids": affected_object_ids if changed else [],
        "affected_relationship_ids": affected_relationship_ids if changed else [],
        "next_action": "Review the affected local design conclusions before final handover." if changed else "Graph-derived context was revalidated for the current scope.",
    })
    updated["claims"]["company_graph_context"] = make_claim(marker, "case_fact", "maysano:company-graph", str(context.get("retrieved_at", "not supplied")), "company-graph-revalidation-v1")
    return updated, {
        "verification_status": marker["verification_status"], "changed": changed,
        "changed_source_references": changed_references,
        "affected_claims": ["company_graph_context"] if changed else [],
        "affected_object_ids": marker["affected_object_ids"], "affected_relationship_ids": marker["affected_relationship_ids"],
        "next_action": marker["next_action"],
    }


def acknowledge_graph_reconsideration(portfolio: dict, decision: dict) -> bool:
    """Clear a stale graph-review gate only through an explicit linked decision."""
    claim = portfolio.get("claims", {}).get("company_graph_context", {})
    marker = claim.get("value", {}) if isinstance(claim, dict) else {}
    if marker.get("verification_status") != "stale":
        return False
    affected_ids = set(marker.get("affected_object_ids", []))
    changed_refs = set(marker.get("changed_source_references", []))
    related_ids = set(decision.get("related_object_ids", []))
    evidence_refs = set(decision.get("evidence_references", []))
    if not (affected_ids & related_ids or changed_refs & evidence_refs):
        return False
    marker["verification_status"] = "verified"
    marker["requires_revalidation"] = False
    marker["reconsidered_by_decision"] = decision["id"]
    marker["next_action"] = "Graph evidence was reconsidered through the recorded human decision."
    return True
