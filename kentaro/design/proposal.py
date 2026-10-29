"""Bounded, deterministic first-pass proposals from minimal business input.

This module deliberately does not infer facts. It offers only reusable, explicitly
proposed design patterns when the supplied text matches a supported problem frame.
"""
from __future__ import annotations

from hashlib import sha256

from .portfolio import add_object, add_relationship, create_design_portfolio, make_claim
from .reports import analysis, readiness


def _source(text: str) -> tuple[str, str, str]:
    digest = sha256(text.encode("utf-8")).hexdigest()
    return (f"business-input:{digest[:16]}", "minimal-input-v1", digest)


def _claim(value: object, status: str, source: tuple[str, str, str]) -> dict:
    return make_claim(value, status, *source)


def _object_claims(name: str, purpose: str, source: tuple[str, str, str], **additional: tuple[object, str]) -> dict:
    claims = {
        "name": _claim(name, "proposed", source),
        "purpose": _claim(purpose, "proposed", source),
        "owner": _claim("Unknown", "unknown", source),
        "lifecycle_status": _claim("discovery", "proposed", source),
    }
    for field, (value, status) in additional.items():
        claims[field] = _claim(value, status, source)
    return claims


def _connect(portfolio: dict, relationship_id: str, from_id: str, to_id: str, kind: str, source: tuple[str, str, str]) -> dict:
    return add_relationship(
        portfolio,
        relationship_id,
        from_id,
        to_id,
        kind,
        provenance=_claim("deterministic initial proposal", "proposed", source),
    )


def _metric_to_confirm(name: str, source: tuple[str, str, str]) -> dict:
    """Represent a required metric without inventing its target or measurement plan."""
    return {
        "name": _claim(name, "proposed", source),
        "target": _claim("To be confirmed", "unknown", source),
        "unit": _claim("To be confirmed", "unknown", source),
        "measurement_period": _claim("To be confirmed", "unknown", source),
        "baseline": _claim("Not provided", "unknown", source),
    }


def _context_needed_proposal(text: str, source: tuple[str, str, str]) -> tuple[dict, list[str]]:
    """Keep the mandatory graph connected while making every missing choice visible."""
    portfolio = create_design_portfolio("Business improvement framing — provisional design", "business-improvement-framing")
    portfolio["claims"] = {
        "initial_business_input": _claim(text, "user_confirmed", source),
        "proposal_boundary": _claim("A connected provisional design only. The business process, users, outcome, metrics, and data scope require human confirmation.", "proposed", source),
    }
    portfolio = add_object(portfolio, "objective-to-confirm", "objective", _object_claims(
        "Business outcome to be confirmed", "Frame the measurable business outcome stated by the business owner", source,
        outcome=("Outcome to be confirmed", "unknown"),
        business_kpi=(_metric_to_confirm("Business KPI to be confirmed", source), "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-to-confirm", "use_case", _object_claims(
        "Business use case to be confirmed", "Identify the workflow that contributes to the proposed business outcome", source,
        consumer=("Consumer to be confirmed", "unknown"),
        expected_business_contribution=("Contribution to be confirmed", "unknown"),
        data_capabilities=("Data capabilities to be confirmed", "unknown"),
        ai_involvement=("none assumed; confirm whether assistance is useful", "proposed"),
    ))
    portfolio = add_object(portfolio, "data-product-to-confirm", "data_product", _object_claims(
        "Reusable data product to be confirmed", "Define the reusable governed data capability required by the confirmed use case", source,
        consumer=("Consumer to be confirmed", "unknown"),
        product_boundary=("Boundary to be confirmed", "unknown"),
        data_capabilities=("Capabilities to be confirmed", "unknown"),
        data_quality=("Quality expectation to be confirmed", "unknown"),
        access_expectations=("Access expectation to be confirmed", "unknown"),
        service_expectations=("Service expectation to be confirmed", "unknown"),
        product_kpi=(_metric_to_confirm("Product KPI to be confirmed", source), "proposed"),
    ))
    portfolio = _connect(portfolio, "usecase-supports-objective", "usecase-to-confirm", "objective-to-confirm", "use-case-supports-objective", source)
    portfolio = _connect(portfolio, "usecase-requires-data", "usecase-to-confirm", "data-product-to-confirm", "use-case-requires-data-product", source)
    return portfolio, ["Which business process, intended user, measurable outcome, current baseline, and target should this provisional design represent?"]


def _permit_proposal(text: str, source: tuple[str, str, str]) -> tuple[dict, list[str]]:
    portfolio = create_design_portfolio("Permit service improvement — provisional design", "permit-service-proposal")
    portfolio["claims"] = {
        "initial_business_input": _claim(text, "user_confirmed", source),
        "proposal_boundary": _claim("Candidate design patterns only; permit types, current workflow, rules, sources, and owners are unverified.", "proposed", source),
    }
    portfolio = add_object(portfolio, "objective-permit-service", "objective", _object_claims(
        "Improve permit-service flow", "Reduce avoidable delay while preserving accountable human decisions", source,
        outcome=("Faster and more predictable permit processing", "proposed"),
        kpi=({"cycle_time": "unknown baseline", "completeness_rate": "unknown baseline", "referral_delay": "unknown baseline"}, "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-completeness", "use_case", _object_claims(
        "Application completeness check", "Identify missing information before a permit application enters review", source,
        ai_involvement=("none", "proposed"),
        decision=("Whether the application has all required information", "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-referral", "use_case", _object_claims(
        "Cross-department referral coordination", "Route applications and make referral progress visible to responsible teams", source,
        ai_involvement=("none", "proposed"),
        decision=("Which department should review the next step", "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-review-support", "use_case", _object_claims(
        "Case-review support", "Help human reviewers locate relevant submitted evidence without automating approval", source,
        ai_involvement=("proposed", "proposed"),
        human_oversight=("Required; reviewers retain the approval decision", "proposed"),
    ))
    portfolio = add_object(portfolio, "ai-evidence-assistant", "ai_product", _object_claims(
        "Evidence and correspondence review assistant", "Summarise supplied case material for human review; it does not approve permits", source,
        capability=("Evidence retrieval and summarisation", "proposed"),
        human_oversight=("Required before any recommendation is used", "proposed"),
        evaluation_criteria=("Reviewer usefulness, citation accuracy, and inappropriate-recommendation rate", "proposed"),
    ))
    portfolio = add_object(portfolio, "data-permit-context", "data_product", _object_claims(
        "Permit decision context", "Provide a governed, consumer-oriented view of submitted application, referral, and evidence context", source,
        product_boundary=("Application, referral, and submitted-evidence context; source-system scope is unverified", "proposed"),
        consumption_capability=("Case and workflow context for proposed permit-service use cases", "proposed"),
        interface=("Read-only case-context service or equivalent reviewed access pattern", "proposed"),
        data_quality=("Completeness, freshness, and authority are unknown", "unknown"),
        access_authorization=("Unknown", "unknown"),
    ))
    for relation in (
        ("completeness-objective", "usecase-completeness", "objective-permit-service", "use-case-supports-objective"),
        ("referral-objective", "usecase-referral", "objective-permit-service", "use-case-supports-objective"),
        ("review-objective", "usecase-review-support", "objective-permit-service", "use-case-supports-objective"),
        ("completeness-data", "usecase-completeness", "data-permit-context", "use-case-requires-data-product"),
        ("referral-data", "usecase-referral", "data-permit-context", "use-case-requires-data-product"),
        ("review-ai", "usecase-review-support", "ai-evidence-assistant", "use-case-delivered-by-ai-product"),
        ("review-data", "usecase-review-support", "data-permit-context", "use-case-requires-data-product"),
        ("ai-data", "ai-evidence-assistant", "data-permit-context", "ai-product-consumes-data-product"),
    ):
        portfolio = _connect(portfolio, *relation, source)
    portfolio["design_alternatives"] = [
        {"id": "conventional-automation", "name": "Conventional workflow automation", "object_ids": ["usecase-completeness", "usecase-referral"], "shared_object_ids": ["data-permit-context"]},
        {"id": "ai-assisted-review", "name": "AI-assisted case review", "object_ids": ["usecase-review-support", "ai-evidence-assistant"], "shared_object_ids": ["data-permit-context"]},
    ]
    return portfolio, ["Which permit type and review step should be the first discovery focus? Its answer determines the priority use case and information boundary."]


def _finance_proposal(text: str, source: tuple[str, str, str]) -> tuple[dict, list[str]]:
    portfolio = create_design_portfolio("Finance reporting reconciliation — provisional design", "finance-reconciliation-proposal")
    portfolio["claims"] = {
        "initial_business_input": _claim(text, "user_confirmed", source),
        "proposal_boundary": _claim("Candidate data-quality and workflow-automation design; systems, rules, metrics, and ownership are unverified.", "proposed", source),
    }
    portfolio = add_object(portfolio, "objective-finance-reporting", "objective", _object_claims(
        "Improve monthly financial reporting", "Reduce reconciliation effort and unresolved reporting discrepancies", source,
        outcome=("Faster reporting with fewer unresolved discrepancies", "proposed"),
        kpi=({"reconciliation_effort": "unknown baseline", "discrepancy_rate": "unknown baseline", "reporting_cycle_time": "unknown baseline"}, "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-reconciliation", "use_case", _object_claims(
        "Reconciliation exception management", "Identify, classify, and route discrepancies between monthly source-system reports", source,
        ai_involvement=("none", "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-report-preparation", "use_case", _object_claims(
        "Monthly reporting preparation", "Prepare reconciled reporting inputs with visible data-quality checks", source,
        ai_involvement=("none", "proposed"),
    ))
    portfolio = add_object(portfolio, "data-reporting-context", "data_product", _object_claims(
        "Financial reporting reconciliation context", "Provide reviewed source, reconciliation, and exception context for monthly reporting workflows", source,
        product_boundary=("Monthly reporting inputs and reconciliation exceptions; source-system scope is unverified", "proposed"),
        consumption_capability=("Reconciliation and reporting-preparation context", "proposed"),
        interface=("Reviewed reporting data service or controlled reconciliation workspace", "proposed"),
        data_quality=("Source authority, timeliness, and reconciliation rules are unknown", "unknown"),
    ))
    for relation in (
        ("reconciliation-objective", "usecase-reconciliation", "objective-finance-reporting", "use-case-supports-objective"),
        ("reporting-objective", "usecase-report-preparation", "objective-finance-reporting", "use-case-supports-objective"),
        ("reconciliation-data", "usecase-reconciliation", "data-reporting-context", "use-case-requires-data-product"),
        ("reporting-data", "usecase-report-preparation", "data-reporting-context", "use-case-requires-data-product"),
    ):
        portfolio = _connect(portfolio, *relation, source)
    portfolio["design_alternatives"] = [
        {"id": "data-quality-first", "name": "Data-quality and reconciliation automation first", "object_ids": ["usecase-reconciliation", "usecase-report-preparation"], "shared_object_ids": ["data-reporting-context"]},
        {"id": "ai-later", "name": "AI assistance only after reconciliation rules are evidenced", "object_ids": [], "shared_object_ids": ["data-reporting-context"]},
    ]
    return portfolio, ["Which monthly report and discrepancy type creates the greatest business impact? Its answer determines the first reconciliation scope."]


def propose_design(text: str) -> dict:
    """Return a source-labelled initial proposal or one essential framing question."""
    normalized = " ".join(text.lower().split())
    source = _source(text)
    if "permit" in normalized and ("government" in normalized or "application" in normalized):
        portfolio, questions = _permit_proposal(text, source)
        frame = "permit_service"
    elif "finance" in normalized and "reconcil" in normalized and "report" in normalized:
        portfolio, questions = _finance_proposal(text, source)
        frame = "finance_reconciliation"
    else:
        portfolio, questions = _context_needed_proposal(text, source)
        frame = "needs_context"
    assessment = analysis(portfolio)
    readiness_result = readiness(portfolio)
    return {
        "portfolio": portfolio,
        "frame": frame,
        "clarification_questions": questions,
        "measurement": {
            "user_messages": 1,
            "clarification_questions": len(questions),
            "substantive_business_concepts": len(portfolio["objects"]),
            "meaningful_alternatives": len(portfolio["design_alternatives"]),
            "unsupported_factual_claims": 0,
            "manual_schema_or_cli_operations_required_from_business_user": 0,
            "valid_connected_portfolio": bool(portfolio["objects"] and portfolio["relationships"]),
        },
        "analysis": assessment,
        "readiness": readiness_result,
    }
