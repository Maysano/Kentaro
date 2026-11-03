"""Ephemeral company-graph context for connected business design.

The Maysano pilot API specifies ``Cache-Control: no-store``.  This module
therefore keeps source records only in memory for the active design operation.
It can persist a small provenance-only marker in a DesignPortfolio, but never a
copy of the company graph.
"""
from __future__ import annotations

from collections import Counter
import re

from .portfolio import make_claim


_STOP_WORDS = frozenset({
    "a", "an", "and", "assessment", "business", "case", "data", "for", "from",
    "improve", "in", "of", "or", "our", "process", "product", "service", "the",
    "to", "use", "we", "with",
})


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]{3,}", value.lower()) if term not in _STOP_WORDS}


def unavailable_context(reason: str = "No configured Maysano connection was available.") -> dict:
    """Return an explicit local-only context; this is not a failed graph read."""
    return {
        "mode": "local_unverified",
        "available": False,
        "reason": reason,
        "records": [],
        "relationships": [],
        "limitations": [
            "No authoritative company-graph context was retrieved.",
            "Reuse, duplication, and dependency findings are not verified against Maysano.",
        ],
    }


def initialize_company_context(snapshot: dict, *, source_kind: str) -> dict:
    """Validate and hold one existing reader snapshot for the active operation."""
    records = snapshot.get("records")
    relationships = snapshot.get("relationships")
    if not isinstance(records, list) or not isinstance(relationships, list):
        raise ValueError("Company graph reader returned an invalid context")
    counts = Counter(record.get("kind") for record in records)
    return {
        "mode": "connected",
        "available": True,
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
            "availability": "unavailable",
            "reason": context["reason"],
            "reuse_status": "not_verified",
        }
    return {
        "mode": "connected",
        "availability": "available",
        "source_kind": context["source_kind"],
        "source_label": context["source_label"],
        "scope": context["scope"],
        "retrieved_at": context["retrieved_at"],
        "record_counts": context["record_counts"],
        "relationship_count": context["relationship_count"],
        "match_count": len(findings["matches"]),
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
