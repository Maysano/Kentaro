"""Structural completion checks and deterministic ODPS-family exports for DesignPortfolio."""
from __future__ import annotations

import json
from pathlib import Path

from .portfolio import is_claim, validate_portfolio
from .reports import validate_odps


def _value(claims: dict, field: str):
    claim = claims.get(field)
    return claim["value"] if is_claim(claim) else None


def _metric(claims: dict, field: str) -> dict | None:
    value = claims.get(field)
    if not isinstance(value, dict) or is_claim(value):
        return None
    required = ("name", "target", "unit", "measurement_period")
    if not all(is_claim(value.get(key)) for key in required):
        return None
    if not isinstance(value["target"]["value"], (int, float)) or not str(value["unit"]["value"]).strip() or not str(value["measurement_period"]["value"]).strip():
        return None
    return value


def structural_completion(portfolio: dict) -> dict:
    """Check required design content without confusing it with business approval."""
    checked = validate_portfolio(portfolio)
    if not checked["valid"]:
        return {"valid": False, "structurally_complete": False, "findings": checked["findings"]}
    design = checked["portfolio"]
    objects = {item["id"]: item for item in design["objects"]}
    findings = []
    def missing(code: str, object_id: str, message: str):
        findings.append({"code": code, "object_id": object_id, "message": message})
    objectives = [item for item in objects.values() if item["kind"] == "objective"]
    use_cases = [item for item in objects.values() if item["kind"] == "use_case"]
    products = [item for item in objects.values() if item["kind"] == "data_product"]
    if not objectives: missing("missing_objective", "portfolio", "At least one business objective is required.")
    if not use_cases: missing("missing_use_case", "portfolio", "At least one use case is required.")
    if not products: missing("missing_data_product", "portfolio", "At least one data product is required.")
    for objective in objectives:
        if not is_claim(objective["claims"].get("outcome")): missing("missing_objective_outcome", objective["id"], "Objective needs a sourced business outcome.")
        if not _metric(objective["claims"], "business_kpi"):
            missing("missing_objective_kpi", objective["id"], "Objective needs a KPI with name, target, unit, and measurement period claims.")
    relationships = design["relationships"]
    for use_case in use_cases:
        claims = use_case["claims"]
        for field in ("consumer", "expected_business_contribution", "data_capabilities"):
            if not is_claim(claims.get(field)): missing(f"missing_use_case_{field}", use_case["id"], f"Use case needs a sourced {field.replace('_', ' ')}.")
        if not any(edge["from_id"] == use_case["id"] and edge["kind"] == "use-case-supports-objective" for edge in relationships):
            missing("unlinked_use_case", use_case["id"], "Use case must support at least one business objective.")
    for product in products:
        claims = product["claims"]
        for field in ("consumer", "product_boundary", "data_capabilities", "data_quality", "access_expectations", "service_expectations"):
            if not is_claim(claims.get(field)):
                missing(f"missing_data_product_{field}", product["id"], f"Data product needs a sourced {field.replace('_', ' ')}.")
        if not _metric(claims, "product_kpi"):
            missing("missing_data_product_kpi", product["id"], "Data product needs a KPI with name, target, unit, and measurement period claims.")
        if not any(edge["to_id"] == product["id"] and edge["kind"] in {"use-case-requires-data-product", "ai-product-consumes-data-product"} for edge in relationships):
            missing("unlinked_data_product", product["id"], "Data product must support at least one identified use case or AI product.")
    question_for = {
        "missing_objective_outcome": "What measurable business outcome should this objective achieve?",
        "missing_objective_kpi": "What KPI, numeric target, unit, measurement period, and available baseline define this objective?",
        "unlinked_use_case": "Which business objective does this use case support?",
        "missing_use_case_consumer": "Who will use or consume the result of this use case?",
        "missing_use_case_expected_business_contribution": "What measurable business contribution should this use case make?",
        "missing_use_case_data_capabilities": "Which data capabilities does this use case require?",
        "missing_data_product_consumer": "Which identified consumer needs this data product?",
        "missing_data_product_product_boundary": "What is inside and outside this data product boundary?",
        "missing_data_product_data_capabilities": "Which reusable data capabilities must this product provide?",
        "missing_data_product_kpi": "What product KPI, numeric target, unit, and measurement period will show this product's value?",
        "missing_data_product_data_quality": "Which quality expectation matters for this product?",
        "missing_data_product_access_expectations": "Who needs access and under what access expectation?",
        "missing_data_product_service_expectations": "What availability, timeliness, or service expectation is needed?",
    }
    return {"valid": True, "structurally_complete": not findings, "portfolio_hash": checked["content_hash"], "findings": findings, "discovery_questions": sorted({question_for[item["code"]] for item in findings if item["code"] in question_for}), "limitations": ["Structural completion permits proposed values. It is not business approval, access confirmation, or production readiness."]}


def _language(value: object) -> dict:
    return {"en": str(value)}


def _confidence(edge: dict) -> str:
    claim = edge.get("provenance")
    if is_claim(claim) and claim["status"] in {"case_fact", "user_confirmed"}:
        return "high"
    return "low" if not claim or claim["status"] in {"unknown", "assumed", "proposed"} else "medium"


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _odps_product(item: dict) -> dict:
    claims = item["claims"]
    return {"schema": "https://opendataproducts.org/v4.0/schema/odps.json", "version": "4.0", "product": {
        "name": _value(claims, "name"), "productID": item["id"], "visibility": "organisation", "status": "development", "type": "dataset",
        "description": _value(claims, "purpose"), "valueProposition": _value(claims, "purpose"),
    }}


def build_specifications(portfolio: dict, destination: str | Path) -> dict:
    """Write and validate only supported, deterministic ODPS/ODPC/ODPG artifacts."""
    completion = structural_completion(portfolio)
    if not completion.get("structurally_complete"):
        raise ValueError("Cannot generate final specifications until structural completion findings are resolved.")
    design = validate_portfolio(portfolio)["portfolio"]
    root = Path(destination)
    products = [item for item in design["objects"] if item["kind"] == "data_product"]
    ai_products = [item for item in design["objects"] if item["kind"] == "ai_product"]
    objectives = [item for item in design["objects"] if item["kind"] == "objective"]
    use_cases = [item for item in design["objects"] if item["kind"] == "use_case"]
    product_refs = []
    artifacts = []
    for item in products:
        path = root / "data-products" / f"{item['id']}.odps.yaml"
        _write(path, _odps_product(item)); artifacts.append(path)
        product_refs.append({"id": item["id"], "productID": item["id"], "productVersion": design["revision"], "name": _language(_value(item["claims"], "name")), "description": _language(_value(item["claims"], "purpose")), "valueProposition": _language(_value(item["claims"], "purpose")), "status": "draft", "productModel": {"standard": "ODPS", "version": "4.0", "format": "yaml", "$ref": f"data-products/{item['id']}.odps.yaml"}})
    objective_defs = []
    for item in objectives:
        metric = _metric(item["claims"], "business_kpi")
        kpi = {"id": f"kpi-{item['id']}", "name": _language(_value(metric, "name")), "description": _language(f"Business KPI for {_value(item['claims'], 'name')}"), "unit": _value(metric, "unit"), "target": {"value": _value(metric, "target")}, "x-kentaro-measurement-period": _value(metric, "measurement_period")}
        baseline = _value(metric, "baseline") if is_claim(metric.get("baseline")) else None
        if isinstance(baseline, (int, float)): kpi["baseline"] = {"value": baseline}
        objective_defs.append({"id": item["id"], "name": _language(_value(item["claims"], "name")), "description": _language(_value(item["claims"], "purpose")), "expectedOutcomes": [_language(_value(item["claims"], "outcome"))], "kpis": [kpi], "status": "draft"})
    use_case_defs = [{"id": item["id"], "name": _language(_value(item["claims"], "name")), "description": _language(_value(item["claims"], "purpose")), "stakeholders": [str(_value(item["claims"], "consumer"))], "expectedOutcome": _language(_value(item["claims"], "expected_business_contribution")), "dataNeeds": {"summary": _language(_value(item["claims"], "data_capabilities"))}, "status": "draft"} for item in use_cases]
    catalog = {"schema": "https://opendataproducts.org/odpc-v1.0/schema/odpc.yaml", "version": "1.0", "kind": "Catalog", "catalog": {"metadata": {"id": design["portfolio_id"], "name": _language(design["title"]), "description": _language("Draft catalog derived from a Kentaro DesignPortfolio"), "status": "draft"}, "productReferences": product_refs, "useCases": use_case_defs, "businessObjectives": objective_defs}}
    odpc_path = root / "odpc.yaml"; _write(odpc_path, catalog); artifacts.append(odpc_path)
    nodes = []
    for item in objectives: nodes.extend(({"id": item["id"], "type": "BusinessObjective", "$ref": f"odpc.yaml#/catalog/businessObjectives/{item['id']}"}, {"id": f"kpi-{item['id']}", "type": "KPI", "$ref": f"odpc.yaml#/catalog/businessObjectives/{item['id']}/kpis/0"}))
    for item in use_cases: nodes.append({"id": item["id"], "type": "UseCase", "$ref": f"odpc.yaml#/catalog/useCases/{item['id']}"})
    for item in ai_products: nodes.append({"id": item["id"], "type": "Agent", "$ref": f"ai-products/{item['id']}.json"})
    for item in products:
        nodes.extend(({"id": item["id"], "type": "DataProduct", "$ref": f"data-products/{item['id']}.odps.yaml"}, {"id": f"kpi-{item['id']}", "type": "KPI", "$ref": f"#product-kpi:{item['id']}"}))
    edges = []
    mapping = {"use-case-supports-objective": "supports", "use-case-requires-data-product": "uses", "ai-product-consumes-data-product": "uses", "use-case-delivered-by-ai-product": "dependsOn", "product-depends-on-product": "dependsOn", "data-product-reused-by-use-case": "uses"}
    for edge in design["relationships"]:
        if edge["kind"] in mapping: edges.append({"from": edge["from_id"], "to": edge["to_id"], "type": mapping[edge["kind"]], "confidence": _confidence(edge), "x-kentaro-relationship-id": edge["id"]})
    for item in objectives: edges.append({"from": f"kpi-{item['id']}", "to": item["id"], "type": "measures", "confidence": "low", "x-kentaro-derived-from": "business_kpi"})
    for item in products: edges.append({"from": item["id"], "to": f"kpi-{item['id']}", "type": "tracks", "confidence": "low", "x-kentaro-derived-from": "product_kpi"})
    graph = {"schema": "https://opendataproducts.org/odpg-v1.0/schema/odpg.yaml", "version": "1.0", "kind": "Graph", "graph": {"metadata": {"id": f"graph-{design['portfolio_id']}", "name": _language(design["title"]), "description": _language("Draft ODPG graph derived from the DesignPortfolio"), "status": "draft"}, "nodes": nodes, "edges": edges}}
    odpg_path = root / "odpg.yaml"; _write(odpg_path, graph); artifacts.append(odpg_path)
    validations = [{**validate_odps(path), "path": path.relative_to(root).as_posix()} for path in artifacts]
    if not all(item.get("valid") for item in validations): raise ValueError("Generated ODPS family specification failed SDK validation")
    return {"artifacts": artifacts, "validations": validations, "completion": completion}
