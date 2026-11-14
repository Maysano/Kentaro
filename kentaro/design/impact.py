"""Deterministic, local impact assessment for changed business assumptions.

The service deliberately reports review work; it never alters a decision,
approves a redesign, or treats a relationship with proposed provenance as a
confirmed dependency.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from .portfolio import is_claim, validate_portfolio


MATERIAL_CHANGE_STATES = {"challenged", "revised", "unsupported", "contradicted", "verification_unavailable"}
CONFIRMED_STATUSES = {"case_fact", "user_confirmed"}


def _event(design: dict, assessment_id: str | None) -> tuple[dict, dict] | None:
    events = [(assumption, event) for assumption in design["assumptions"] for event in assumption["assessments"]]
    if assessment_id is None:
        material = [(assumption, event) for assumption, event in events if event["state"] in MATERIAL_CHANGE_STATES]
        return material[-1] if material else None
    return next(((assumption, event) for assumption, event in events if event["id"] == assessment_id), None)


def _confirmed_edge(edge: dict) -> bool:
    provenance = edge.get("provenance")
    return is_claim(provenance) and provenance["status"] in CONFIRMED_STATUSES


def _resolved_by(design: dict, event_id: str, decision_id: str) -> str | None:
    for decision in design["decisions"]:
        if decision.get("supersedes") == decision_id and event_id in decision.get("resolves_assessment_ids", []):
            return decision["id"]
    return None


def assess_impact(portfolio: dict, assessment_id: str | None = None) -> dict:
    """Assess one recorded assumption event through explicit local references.

    Read-only calls are stable: the service creates neither events nor findings
    in the DesignPortfolio.  Direct assumption links are confirmed links;
    relationships with non-confirmed provenance become potential review
    candidates and are not traversed further.
    """
    check = validate_portfolio(portfolio)
    if not check["valid"]:
        return {"valid": False, "findings": check["findings"]}
    design = check["portfolio"]
    selected = _event(design, assessment_id)
    if selected is None:
        return {"valid": True, "portfolio_hash": check["content_hash"], "assessment": None, "elements": [], "decisions": [], "summary": {"confirmed_impacts": 0, "potential_impacts": 0, "unaffected": len(design["objects"]), "unknown": 0}, "limitations": ["No material recorded assumption change was selected."]}
    assumption, event = selected
    objects = {item["id"]: item for item in design["objects"]}
    direct = set(assumption["related_object_ids"])
    linked_decisions = {item["id"]: item for item in design["decisions"] if assumption["id"] in item.get("assumption_ids", []) or item["id"] in assumption["related_decision_ids"]}
    for decision in linked_decisions.values():
        direct.update(decision.get("related_object_ids", []))

    confirmed, potential = set(direct), set()
    reasons = {item: [f"Explicit assumption reference: {assumption['id']}."] for item in direct}
    queue = deque(sorted(direct))
    adjacency: dict[str, list[dict]] = {item: [] for item in objects}
    for edge in design["relationships"]:
        adjacency.setdefault(edge["from_id"], []).append(edge)
        adjacency.setdefault(edge["to_id"], []).append(edge)
    while queue:
        source = queue.popleft()
        for edge in adjacency.get(source, []):
            target = edge["to_id"] if edge["from_id"] == source else edge["from_id"]
            reason = f"{source} is connected through {edge['id']} ({edge['kind']})."
            if _confirmed_edge(edge):
                if target not in confirmed:
                    confirmed.add(target)
                    reasons.setdefault(target, []).append(reason)
                    queue.append(target)
            elif target not in confirmed:
                potential.add(target)
                reasons.setdefault(target, []).append(reason + " Relationship provenance is not confirmed.")

    elements = []
    for object_id in sorted(objects):
        if object_id in confirmed:
            classification, certainty = "review_required", "confirmed"
        elif object_id in potential:
            classification, certainty = "review_required", "potential"
        else:
            classification, certainty = "unaffected", "no_known_dependency"
        elements.append({"object_id": object_id, "kind": objects[object_id]["kind"], "name": objects[object_id]["claims"]["name"]["value"], "classification": classification, "certainty": certainty, "reasons": reasons.get(object_id, ["No explicit assumption or evaluated relationship dependency was identified for this change."])})
    decisions = []
    for decision_id, decision in sorted(linked_decisions.items()):
        resolved_by = _resolved_by(design, event["id"], decision_id)
        decisions.append({"decision_id": decision_id, "subject": decision["subject"], "owner": decision["actor"], "related_object_ids": list(decision.get("related_object_ids", [])), "classification": "unaffected" if resolved_by else "review_required", "requires_reassessment": not bool(resolved_by), "resolved_by": resolved_by, "reason": "The decision recorded this assumption and its then-current assessment; its historical resolution remains unchanged.", "recommended_action": "Record a subsequent human decision with the changed evidence if the commitment changes." if not resolved_by else "A subsequent local human decision records resolution of this reassessment requirement."})
    unknown = event["state"] == "verification_unavailable"
    return {
        "valid": True,
        "portfolio_hash": check["content_hash"],
        "assessment": {"assumption_id": assumption["id"], "assessment_id": event["id"], "state": event["state"], "previous_assessment": deepcopy(assumption["assessments"][-2]) if len(assumption["assessments"]) > 1 and event is assumption["assessments"][-1] else None, "current": deepcopy(event), "evidence_references": list(event.get("evidence_references") or assumption["evidence_references"]), "assessed_at": event["assessed_at"]},
        "elements": elements,
        "decisions": decisions,
        "summary": {"confirmed_impacts": sum(item["certainty"] == "confirmed" for item in elements), "potential_impacts": sum(item["certainty"] == "potential" for item in elements), "unaffected": sum(item["classification"] == "unaffected" for item in elements), "unknown": int(unknown)},
        "limitations": ["Unchanged technical specifications are not invalidated by this advisory business-impact assessment.", "Unaffected means no dependency was identified from this specific change; it is not authorization to proceed.", "Actor labels are locally supplied and are not authenticated approvals."],
    }


def impact_report(portfolio: dict, assessment_id: str | None = None) -> dict:
    """Return structured assessment plus a concise decision-owner Markdown view."""
    result = assess_impact(portfolio, assessment_id)
    if not result["valid"] or result["assessment"] is None:
        return {**result, "markdown": "# Decision impact assessment\n\nNo material recorded assumption change was selected.\n"}
    change = result["assessment"]
    impacted = [item for item in result["elements"] if item["classification"] != "unaffected"]
    unaffected = [item for item in result["elements"] if item["classification"] == "unaffected"]
    decisions = [item for item in result["decisions"] if item["requires_reassessment"]]
    lines = ["# Decision impact assessment", "", "This is local advisory review material. It does not alter a decision, approve work, or mutate Maysano.", "", "## What changed", "", f"Assumption `{change['assumption_id']}` is **{change['state']}** as of {change['assessed_at']}. Evidence: {', '.join(change['evidence_references']) or 'not recorded'}.", "", "## Why it matters", "", "The affected decisions captured this assumption's prior assessment. Technical structural validity is assessed separately; business justification may need reassessment.", "", "## Which commitments are affected", ""]
    lines += [f"- {item['subject']} — owner: {item['owner'] or 'unknown'}; reassessment required." for item in decisions] or ["- No recorded decision explicitly references this assumption."]
    lines += ["", "## Confirmed and potential impacts", ""]
    lines += [f"- {item['name']} ({item['kind']}): {item['certainty']} — {' '.join(item['reasons'])}" for item in impacted] or ["- No impacted design object was identified."]
    lines += ["", "## What remains unaffected", ""]
    lines += [f"- {item['name']} ({item['kind']})" for item in unaffected] or ["- None identified."]
    lines += ["", "## What needs to happen next", "", "- The recorded decision owner should review the changed evidence and record a subsequent local decision if the commitment changes.", "- Keep technical validation separate; no specification is automatically invalidated.", "- Missing or unavailable evidence remains a review requirement, not confirmation of safety.", ""]
    return {**result, "markdown": "\n".join(lines)}
