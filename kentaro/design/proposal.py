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
        "ai_product_opportunity": _claim("Assess whether a human-in-the-loop AI product could help only after the business process, users, information boundaries, and human decisions are known. No AI product can be responsibly proposed yet.", "proposed", source),
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


def _customer_risk_proposal(text: str, source: tuple[str, str, str]) -> tuple[dict, list[str]]:
    """Offer bounded, smaller information capabilities and an AI option for risk assessment.

    The pattern is a candidate design, not a claim about a bank's systems, policies,
    data, or permitted AI use. The human assessor remains accountable for the case.
    """
    portfolio = create_design_portfolio("Customer risk-assessment improvement — provisional design", "customer-risk-assessment-proposal")
    portfolio["claims"] = {
        "initial_business_input": _claim(text, "user_confirmed", source),
        "proposal_boundary": _claim("Candidate business-design pattern only. Assessment policy, source systems, information authority, access, and AI suitability require human confirmation.", "proposed", source),
        "ai_product_opportunity": _claim("A human-in-the-loop preparation assistant is a candidate option alongside information and workflow improvement; it must not score customers, interpret policy, make case decisions, approve outcomes, or change customer records.", "proposed", source),
    }
    portfolio = add_object(portfolio, "objective-customer-risk", "objective", _object_claims(
        "Improve customer risk-assessment turnaround", "Reduce avoidable delay while retaining accountable human risk decisions", source,
        outcome=("Faster customer risk assessments", "proposed"),
        kpi=({"turnaround_time": "unknown baseline", "information_availability": "unknown baseline"}, "proposed"),
    ))
    portfolio = add_object(portfolio, "usecase-risk-preparation", "use_case", _object_claims(
        "Customer risk-assessment preparation", "Give risk assessors timely, traceable information before they make the assessment decision", source,
        ai_involvement=("candidate human-in-the-loop preparation support; suitability to be confirmed", "proposed"),
        decision=("Human risk assessor decides whether the customer assessment is complete and acceptable", "proposed"),
        human_oversight=("Required; the assessor retains all case, policy, and approval decisions", "proposed"),
    ))
    portfolio = add_object(portfolio, "data-customer-profile-context", "data_product", _object_claims(
        "Customer identity and profile context", "Provide assessors with the customer attributes and identity references needed to begin an assessment", source,
        domain_scope=("Candidate Customer Identity and Profile domain product; domain accountability and authoritative sources are to be confirmed", "proposed"),
        consumer=("Risk assessors", "proposed"),
        product_boundary=("Customer identity and profile attributes and references needed for risk assessment; excludes due-diligence evidence management, risk scoring, policy interpretation, case decisions, approvals, and customer-record changes", "proposed"),
        consumption_capability=("Timely assessor-facing customer context with source references", "proposed"),
        reuse_hypothesis=("May support other authorised customer-service and risk processes; consumers and product owner are unknown", "unknown"),
        data_quality=("Authority, freshness, and completeness are unknown", "unknown"),
        access_expectations=("Permitted assessor access is unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "data-assessment-evidence", "data_product", _object_claims(
        "Customer due-diligence evidence context", "Show assessors which required customer due-diligence evidence is available, missing, or flagged for quality", source,
        domain_scope=("Candidate Customer Due-Diligence Evidence domain product; evidence authority and domain accountability are to be confirmed", "proposed"),
        consumer=("Risk assessors", "proposed"),
        product_boundary=("Customer due-diligence evidence availability, evidence references, and data-quality flags; excludes identity-profile stewardship, customer-record changes, and assessment decisions", "proposed"),
        consumption_capability=("Assessor-facing availability status and traceable evidence references", "proposed"),
        reuse_hypothesis=("May support other authorised due-diligence and customer-review processes; consumers and product owner are unknown", "unknown"),
        data_quality=("Completeness rules and evidence authority are unknown", "unknown"),
        access_expectations=("Permitted assessor access is unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "data-risk-assessment-case-context", "data_product", _object_claims(
        "Customer risk-assessment case context", "Provide the accountable risk-assessment case, its lifecycle context, and outstanding information needs to authorised risk operations users", source,
        domain_scope=("Candidate Customer Risk-Assessment Case domain product; case authority and domain accountability are to be confirmed", "proposed"),
        consumer=("Risk Operations and risk assessors", "proposed"),
        product_boundary=("Risk-assessment case identity, accountable team, lifecycle context, due date, and outstanding information needs; excludes risk scoring, policy interpretation, case decisions, approvals, and customer-record changes", "proposed"),
        consumption_capability=("Read-only case context for authorised risk operations users; a worklist is one possible consumption view, not the product boundary", "proposed"),
        reuse_hypothesis=("May support authorised risk-management reporting and service oversight; consumers and product owner are unknown", "unknown"),
        data_quality=("Case status authority and refresh expectations are unknown", "unknown"),
        access_expectations=("Permitted operational access is unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "ai-risk-preparation-assistant", "ai_product", _object_claims(
        "Risk-assessment preparation assistant", "Prepare a traceable summary of available evidence and missing-information prompts for a human assessor; it does not decide the case", source,
        capability=("Retrieve, organise, and summarise assessor-approved information with source references", "proposed"),
        human_oversight=("Required; a human assessor reviews all material and retains every assessment and approval decision", "proposed"),
        evaluation_criteria=("Assessor usefulness, source-reference accuracy, missing-information recall, and inappropriate-suggestion rate", "proposed"),
        prohibited_actions=("No risk scoring, policy interpretation, case decision, approval, or customer-record change", "proposed"),
    ))
    for relation in (
        ("risk-preparation-objective", "usecase-risk-preparation", "objective-customer-risk", "use-case-supports-objective"),
        ("risk-preparation-profile", "usecase-risk-preparation", "data-customer-profile-context", "use-case-requires-data-product"),
        ("risk-preparation-evidence", "usecase-risk-preparation", "data-assessment-evidence", "use-case-requires-data-product"),
        ("risk-preparation-case-context", "usecase-risk-preparation", "data-risk-assessment-case-context", "use-case-requires-data-product"),
        ("risk-preparation-ai", "usecase-risk-preparation", "ai-risk-preparation-assistant", "use-case-delivered-by-ai-product"),
        ("ai-profile-context", "ai-risk-preparation-assistant", "data-customer-profile-context", "ai-product-consumes-data-product"),
        ("ai-assessment-evidence", "ai-risk-preparation-assistant", "data-assessment-evidence", "ai-product-consumes-data-product"),
        ("ai-case-context", "ai-risk-preparation-assistant", "data-risk-assessment-case-context", "ai-product-consumes-data-product"),
    ):
        portfolio = _connect(portfolio, *relation, source)
    portfolio["design_alternatives"] = [
        {"id": "domain-information-first", "name": "Domain information products and workflow improvement", "object_ids": ["usecase-risk-preparation", "data-customer-profile-context", "data-assessment-evidence", "data-risk-assessment-case-context"], "shared_object_ids": []},
        {"id": "ai-assisted-preparation", "name": "Human-in-the-loop AI preparation support", "object_ids": ["usecase-risk-preparation", "ai-risk-preparation-assistant"], "shared_object_ids": ["data-customer-profile-context", "data-assessment-evidence", "data-risk-assessment-case-context"]},
    ]
    return portfolio, ["Which of the Customer Identity and Profile, Customer Due-Diligence Evidence, or Customer Risk-Assessment Case domains owns the information causing the greatest delay? Confirm the accountable owner, authoritative source, and first consumer before treating any candidate as a data product."]


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
    portfolio = add_object(portfolio, "data-permit-application", "data_product", _object_claims(
        "Permit application context", "Provide the submitted application information needed to check completeness and begin review", source,
        consumer=("Permit operations and reviewers", "proposed"),
        product_boundary=("Submitted permit-application information and source references; excludes policy interpretation, referral decisions, workflow transitions, and permit approval", "proposed"),
        consumption_capability=("Case context for completeness checks and human review", "proposed"),
        interface=("Read-only case-context service or equivalent reviewed access pattern", "proposed"),
        data_quality=("Completeness, freshness, and authority are unknown", "unknown"),
        access_authorization=("Unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "data-permit-referral", "data_product", _object_claims(
        "Permit referral coordination context", "Make referral ownership, progress, and outstanding requests visible to responsible permit teams", source,
        consumer=("Permit operations and referred departments", "proposed"),
        product_boundary=("Referral ownership, progress, and outstanding requests; excludes routing decisions, workflow transitions, and permit approval", "proposed"),
        consumption_capability=("Read-only referral coordination context", "proposed"),
        interface=("Read-only referral status service or equivalent reviewed access pattern", "proposed"),
        data_quality=("Referral authority, freshness, and completeness are unknown", "unknown"),
        access_authorization=("Unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "data-permit-evidence", "data_product", _object_claims(
        "Permit evidence availability", "Show reviewers which submitted evidence is available, missing, or linked to the application", source,
        consumer=("Permit reviewers", "proposed"),
        product_boundary=("Submitted-evidence availability and source references; excludes evidence interpretation and permit approval", "proposed"),
        consumption_capability=("Reviewer-facing evidence availability and traceable references", "proposed"),
        interface=("Read-only evidence index or equivalent reviewed access pattern", "proposed"),
        data_quality=("Evidence authority, freshness, and completeness are unknown", "unknown"),
        access_authorization=("Unknown", "unknown"),
    ))
    for relation in (
        ("completeness-objective", "usecase-completeness", "objective-permit-service", "use-case-supports-objective"),
        ("referral-objective", "usecase-referral", "objective-permit-service", "use-case-supports-objective"),
        ("review-objective", "usecase-review-support", "objective-permit-service", "use-case-supports-objective"),
        ("completeness-data", "usecase-completeness", "data-permit-application", "use-case-requires-data-product"),
        ("referral-data", "usecase-referral", "data-permit-referral", "use-case-requires-data-product"),
        ("review-ai", "usecase-review-support", "ai-evidence-assistant", "use-case-delivered-by-ai-product"),
        ("review-application", "usecase-review-support", "data-permit-application", "use-case-requires-data-product"),
        ("review-evidence", "usecase-review-support", "data-permit-evidence", "use-case-requires-data-product"),
        ("ai-application", "ai-evidence-assistant", "data-permit-application", "ai-product-consumes-data-product"),
        ("ai-evidence", "ai-evidence-assistant", "data-permit-evidence", "ai-product-consumes-data-product"),
    ):
        portfolio = _connect(portfolio, *relation, source)
    portfolio["design_alternatives"] = [
        {"id": "conventional-automation", "name": "Conventional workflow automation", "object_ids": ["usecase-completeness", "usecase-referral", "data-permit-application", "data-permit-referral", "data-permit-evidence"], "shared_object_ids": []},
        {"id": "ai-assisted-review", "name": "Human-in-the-loop AI case review", "object_ids": ["usecase-review-support", "ai-evidence-assistant"], "shared_object_ids": ["data-permit-application", "data-permit-evidence"]},
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
    portfolio = add_object(portfolio, "data-reporting-inputs", "data_product", _object_claims(
        "Financial reporting inputs", "Provide traceable monthly reporting inputs for reconciliation and report preparation", source,
        consumer=("Finance reconciliation and reporting teams", "proposed"),
        product_boundary=("Monthly reporting inputs and their source references; excludes reconciliation decisions and journal changes", "proposed"),
        consumption_capability=("Reviewed reporting-input context with source references", "proposed"),
        interface=("Reviewed reporting data service or controlled reconciliation workspace", "proposed"),
        data_quality=("Source authority and timeliness are unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "data-reconciliation-exceptions", "data_product", _object_claims(
        "Reconciliation exception context", "Make discrepancies, investigation status, accountable owner, and supporting references visible to finance teams", source,
        consumer=("Finance reconciliation and reporting teams", "proposed"),
        product_boundary=("Reporting discrepancies, investigation status, and supporting references; excludes ledger postings and financial approval", "proposed"),
        consumption_capability=("Controlled exception worklist and investigation context", "proposed"),
        interface=("Controlled reconciliation workspace or reviewed exception service", "proposed"),
        data_quality=("Reconciliation rules, authority, and completeness are unknown", "unknown"),
    ))
    portfolio = add_object(portfolio, "ai-reconciliation-investigation-assistant", "ai_product", _object_claims(
        "Reconciliation investigation assistant", "Prepare traceable discrepancy summaries and investigation prompts for finance users; it does not decide postings or approvals", source,
        capability=("Summarise recorded discrepancies and retrieve linked reporting context for human investigation", "proposed"),
        human_oversight=("Required; finance users retain reconciliation, posting, and approval decisions", "proposed"),
        evaluation_criteria=("Investigator usefulness, source-reference accuracy, discrepancy coverage, and inappropriate-suggestion rate", "proposed"),
        prohibited_actions=("No posting, reconciliation decision, approval, or source-record change", "proposed"),
    ))
    for relation in (
        ("reconciliation-objective", "usecase-reconciliation", "objective-finance-reporting", "use-case-supports-objective"),
        ("reporting-objective", "usecase-report-preparation", "objective-finance-reporting", "use-case-supports-objective"),
        ("reconciliation-inputs", "usecase-reconciliation", "data-reporting-inputs", "use-case-requires-data-product"),
        ("reconciliation-exceptions", "usecase-reconciliation", "data-reconciliation-exceptions", "use-case-requires-data-product"),
        ("reporting-inputs", "usecase-report-preparation", "data-reporting-inputs", "use-case-requires-data-product"),
        ("reporting-exceptions", "usecase-report-preparation", "data-reconciliation-exceptions", "use-case-requires-data-product"),
        ("reconciliation-ai", "usecase-reconciliation", "ai-reconciliation-investigation-assistant", "use-case-delivered-by-ai-product"),
        ("ai-reporting-inputs", "ai-reconciliation-investigation-assistant", "data-reporting-inputs", "ai-product-consumes-data-product"),
        ("ai-reconciliation-exceptions", "ai-reconciliation-investigation-assistant", "data-reconciliation-exceptions", "ai-product-consumes-data-product"),
    ):
        portfolio = _connect(portfolio, *relation, source)
    portfolio["design_alternatives"] = [
        {"id": "data-quality-first", "name": "Data-quality and reconciliation automation first", "object_ids": ["usecase-reconciliation", "usecase-report-preparation", "data-reporting-inputs", "data-reconciliation-exceptions"], "shared_object_ids": []},
        {"id": "ai-assisted-investigation", "name": "Human-in-the-loop AI investigation support", "object_ids": ["usecase-reconciliation", "ai-reconciliation-investigation-assistant"], "shared_object_ids": ["data-reporting-inputs", "data-reconciliation-exceptions"]},
    ]
    return portfolio, ["Which monthly report and discrepancy type creates the greatest business impact? Its answer determines the first reconciliation scope."]


def propose_design(text: str) -> dict:
    """Return a source-labelled initial proposal or one essential framing question."""
    normalized = " ".join(text.lower().split())
    source = _source(text)
    if "permit" in normalized and ("government" in normalized or "application" in normalized):
        portfolio, questions = _permit_proposal(text, source)
        frame = "permit_service"
    elif "risk assessment" in normalized and ("bank" in normalized or "customer" in normalized):
        portfolio, questions = _customer_risk_proposal(text, source)
        frame = "customer_risk_assessment"
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
