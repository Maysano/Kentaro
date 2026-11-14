"""Deterministic acceptance checks for recorded Business Owner design journeys.

The evaluator does not simulate an LLM or confer approval.  An agent adapter records
the ordinary user turn, its response, next question, and the saved DesignPortfolio
after that turn.  Kentaro then validates those snapshots against a reusable case.
"""
from __future__ import annotations

from pathlib import Path

from .engagement import build_engagement_state
from .portfolio import validate_portfolio
from .reports import readiness
from .specifications import structural_completion


TRACE_MODEL = "KentaroBusinessDesignJourneyTrace"


def _finding(turn_id: str, code: str, message: str) -> dict:
    return {"turn_id": turn_id, "code": code, "message": message}


def validate_case(case: dict) -> dict:
    """Validate only the portable, non-agent-specific case contract."""
    findings = []
    if case.get("schema_version") != 1 or case.get("kind") != "KentaroBusinessDesignValidationCase":
        findings.append(_finding("case", "invalid_case", "Case must declare schema_version 1 and KentaroBusinessDesignValidationCase."))
    turns = case.get("turns")
    if not isinstance(turns, list) or not turns:
        findings.append(_finding("case", "missing_turns", "Case needs one or more ordered Business Owner turns."))
        turns = []
    seen = set()
    for turn in turns:
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id or turn_id in seen:
            findings.append(_finding(str(turn_id or "case"), "invalid_turn_id", "Each case turn needs a unique id."))
        seen.add(turn_id)
        if turn.get("actor") != "Business Owner" or not isinstance(turn.get("prompt"), str) or not turn["prompt"].strip():
            findings.append(_finding(str(turn_id or "case"), "invalid_business_owner_turn", "Each turn must contain an ordinary Business Owner prompt."))
        if not isinstance(turn.get("expected"), dict):
            findings.append(_finding(str(turn_id or "case"), "missing_expectations", "Each turn needs expected observable outcomes."))
    return {"valid": not findings, "findings": findings}


def evaluate_journey(case: dict, trace: dict) -> dict:
    """Evaluate an agent-recorded journey against a reusable Business Owner case.

    Trace observations are evidence labels supplied by an adapter; material portfolio
    checks are independently derived from each embedded snapshot.
    """
    findings = list(validate_case(case)["findings"])
    turns = case.get("turns", [])
    events = trace.get("turns", []) if isinstance(trace, dict) else []
    if trace.get("schema_version") != 1 or trace.get("model") != TRACE_MODEL:
        findings.append(_finding("trace", "invalid_trace", f"Trace must declare schema_version 1 and {TRACE_MODEL}."))
    if trace.get("case_id") != case.get("id"):
        findings.append(_finding("trace", "case_mismatch", "Trace case_id does not match the supplied validation case."))
    if len(events) != len(turns):
        findings.append(_finding("trace", "turn_count_mismatch", "Trace must contain exactly one event for every case turn."))

    evaluated = []
    previous_decisions: list[dict] = []
    for index, expected_turn in enumerate(turns):
        turn_id = expected_turn.get("id", f"turn-{index + 1}")
        event = events[index] if index < len(events) and isinstance(events[index], dict) else {}
        expected = expected_turn.get("expected", {})
        if event.get("turn_id") != turn_id:
            findings.append(_finding(turn_id, "turn_order", "Trace turn ids must match the ordered case turns."))
        assistant = event.get("assistant", {})
        if not isinstance(assistant, dict) or not isinstance(assistant.get("response"), str) or not assistant["response"].strip():
            findings.append(_finding(turn_id, "missing_assistant_response", "Record the assistant response for every turn."))
        if expected.get("next_stage") and (not isinstance(assistant, dict) or not isinstance(assistant.get("next_question"), str) or not assistant["next_question"].strip()):
            findings.append(_finding(turn_id, "missing_next_question", "A turn that advances the journey needs a recorded next question."))
        portfolio = event.get("portfolio")
        checked = validate_portfolio(portfolio) if isinstance(portfolio, dict) else {"valid": False, "findings": [{"message": "Missing DesignPortfolio snapshot."}]}
        if not checked["valid"]:
            findings.append(_finding(turn_id, "invalid_portfolio", "Each trace event needs a valid DesignPortfolio snapshot."))
            evaluated.append({"turn_id": turn_id, "valid": False})
            continue
        design = checked["portfolio"]
        marker = design.get("claims", {}).get("company_graph_context", {}).get("value", {})
        completion = structural_completion(design)
        readiness_result = readiness(design)
        readiness_fields = {item.get("field") for item in readiness_result.get("findings", [])}
        observations = event.get("observations", {}) if isinstance(event.get("observations", {}), dict) else {}
        decisions = design.get("decisions", [])
        if expected.get("graph_context") and marker.get("verification_status") != expected["graph_context"]:
            findings.append(_finding(turn_id, "graph_context", "Portfolio graph verification status does not match the case expectation."))
        if expected.get("existing_kinds") and not set(expected["existing_kinds"]).issubset(set(marker.get("record_counts", {}))):
            findings.append(_finding(turn_id, "existing_context", "Portfolio graph provenance does not cover the expected existing record kinds."))
        if expected.get("draft_remains_editable") and not checked["valid"]:
            findings.append(_finding(turn_id, "draft_not_editable", "The incomplete design must remain a valid editable portfolio."))
        if expected.get("missing_information_visible") and not completion.get("findings"):
            findings.append(_finding(turn_id, "missing_information_hidden", "Incomplete information must remain visible as structural findings."))
        if expected.get("reuse_candidate_advisory") and "possible_data_product_reuse" not in readiness_fields:
            findings.append(_finding(turn_id, "reuse_not_visible", "Expected reuse candidate is not an advisory readiness finding."))
        if expected.get("unverified_dependencies_visible") and "unverified_dependency" not in readiness_fields:
            findings.append(_finding(turn_id, "dependencies_not_visible", "Expected unverified dependency is not visible in readiness."))
        if expected.get("minimum_alternatives") and len(design.get("design_alternatives", [])) < expected["minimum_alternatives"]:
            findings.append(_finding(turn_id, "alternatives_missing", "The portfolio does not contain the required alternatives."))
        if expected.get("human_decision_required") and decisions:
            findings.append(_finding(turn_id, "decision_premature", "A human decision was recorded before the case asks for one."))
        if expected.get("explicit_decision") and (len(decisions) <= len(previous_decisions) or decisions[-1].get("actor") != "Business Owner"):
            findings.append(_finding(turn_id, "decision_not_explicit", "Expected an appended Business Owner decision event."))
        if expected.get("decision_status") and (not decisions or decisions[-1].get("status") != expected["decision_status"]):
            findings.append(_finding(turn_id, "decision_status", "Decision status does not match the case expectation."))
        if expected.get("supersedes") and (not decisions or decisions[-1].get("supersedes") != expected["supersedes"]):
            findings.append(_finding(turn_id, "decision_not_superseded", "The changed direction must supersede the earlier decision."))
        if expected.get("history_preserved") and len({item.get("id") for item in decisions}) != len(decisions):
            findings.append(_finding(turn_id, "decision_history_overwritten", "Decision history must be append-only."))
        if expected.get("final_handover_blocked_until") and (completion.get("structurally_complete") or observations.get("handover") != "blocked"):
            findings.append(_finding(turn_id, "handover_not_gated", "The incomplete design must record a blocked handover attempt."))
        if expected.get("structured_specifications") and set(expected["structured_specifications"]) - set(observations.get("specification_kinds", [])):
            findings.append(_finding(turn_id, "specifications_missing", "The trace does not record all required validated specification kinds."))
        if expected.get("verification_status") and marker.get("verification_status") != expected["verification_status"]:
            findings.append(_finding(turn_id, "revalidation_status", "Graph revalidation status does not match the case expectation."))
        if expected.get("affected_elements_identified") and not marker.get("affected_object_ids"):
            findings.append(_finding(turn_id, "affected_elements_missing", "Changed graph evidence must identify affected design elements."))
        if expected.get("reconsideration_required") and not marker.get("requires_revalidation"):
            findings.append(_finding(turn_id, "reconsideration_not_required", "Changed graph evidence must require reconsideration."))
        if expected.get("explicit_confirmation") and not observations.get("confirmation"):
            findings.append(_finding(turn_id, "confirmation_missing", "Final handover needs an explicit local confirmation observation."))
        if expected.get("handover_status") and observations.get("handover_status") != expected["handover_status"]:
            findings.append(_finding(turn_id, "handover_status", "Recorded handover status does not match the case expectation."))
        build_engagement_state(design, portfolio_path=Path(f"/journey/{turn_id}.json"))
        previous_decisions = decisions
        evaluated.append({"turn_id": turn_id, "valid": True, "portfolio_hash": checked["content_hash"]})
    return {"valid": not findings, "case_id": case.get("id"), "turns_evaluated": evaluated, "findings": findings, "limitations": ["Transcript observations are adapter-supplied evidence. The evaluator independently validates every embedded DesignPortfolio snapshot; it does not authenticate actors, approve handover, or execute business work."]}
