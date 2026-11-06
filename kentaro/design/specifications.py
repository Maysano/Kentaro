"""Structural completion checks and deterministic ODPS-family exports for DesignPortfolio."""
from __future__ import annotations

import json
from pathlib import Path

from .portfolio import is_claim, validate_portfolio
from .reports import validate_odps


ODPC_CONFIRMED_STATUSES = {"case_fact", "user_confirmed"}


def _confirmed_claim(value: object) -> bool:
    return is_claim(value) and value["status"] in ODPC_CONFIRMED_STATUSES


def ai_product_odpc_coverage(item: dict) -> dict:
    """Report whether an AI product has confirmed ODPC v1.1 export inputs."""
    claims = item.get("claims", {})
    odpc = claims.get("odpc") if isinstance(claims, dict) else None
    odpc = odpc if isinstance(odpc, dict) and not is_claim(odpc) else {}
    missing = []
    identity = ("product_id", "product_version", "product_type")
    if not all(_confirmed_claim(odpc.get(field)) for field in identity):
        missing.append({"code": "missing_ai_product_odpc_identity", "paths": [f"odpc.{field}" for field in identity], "message": "AI product needs a confirmed ODPC product ID, product version, and product type."})
    owner = odpc.get("owner")
    if not isinstance(owner, dict) or not any(_confirmed_claim(owner.get(field)) for field in ("organization", "team", "role")):
        missing.append({"code": "missing_ai_product_odpc_owner", "paths": ["odpc.owner.organization", "odpc.owner.team", "odpc.owner.role"], "message": "AI product needs a confirmed structured ODPC owner (organization, team, or role)."})
    governance_fields = ("autonomy_level", "human_oversight_required", "human_oversight_requirements", "consequential_action_approval_required", "consequential_action_approval_requirements", "risk_classification", "known_limitations")
    if not all(_confirmed_claim(odpc.get(field)) for field in governance_fields):
        missing.append({"code": "missing_ai_product_odpc_governance", "paths": [f"odpc.{field}" for field in governance_fields], "message": "AI product needs confirmed autonomy, human oversight, consequential-action approval, risk classification, and known limitations."})
    evaluations = odpc.get("evaluation")
    valid_evaluation = False
    if isinstance(evaluations, dict):
        required = ("id", "name", "measurement_method", "target_value", "unit", "status")
        valid_evaluation = any(isinstance(metric, dict) and all(_confirmed_claim(metric.get(field)) for field in required) for metric in evaluations.values())
    if not valid_evaluation:
        missing.append({"code": "missing_ai_product_odpc_evaluation", "paths": ["odpc.evaluation.<metric>.id", "odpc.evaluation.<metric>.name", "odpc.evaluation.<metric>.measurement_method", "odpc.evaluation.<metric>.target_value", "odpc.evaluation.<metric>.unit", "odpc.evaluation.<metric>.status"], "message": "AI product needs one confirmed ODPC evaluation metric with its method, target, unit, and status."})
    invalid = []
    if not missing:
        try:
            from open_data_products import validate_ai_product
            invalid = list(validate_ai_product(_ai_product_profile(item)).errors)
        except ImportError:
            invalid = ["The pinned open-data-products validator is unavailable."]
    question = None
    if missing:
        first = missing[0]
        if first["code"] == "missing_ai_product_odpc_identity":
            question = f"For {item['claims']['name']['value']}, what stable product ID, product version, and product type should the ODPC AI Product use?"
        else:
            question = f"For {item['claims']['name']['value']}, what confirmed ODPC AI-product information is needed next: {first['message']}"
    if invalid:
        missing = [{"code": "invalid_ai_product_odpc_profile", "paths": ["odpc"], "message": "AI product ODPC input is present but does not satisfy the ODPC v1.1 profile: " + "; ".join(invalid)}]
        question = f"For {item['claims']['name']['value']}, please correct the ODPC AI-product values reported in the validation detail."
    return {"object_id": item["id"], "coverage": "invalid" if invalid else "validated" if not missing else "awaiting_odpc_input", "missing": missing, "question": question}


def ai_product_odpc_coverages(portfolio: dict) -> list[dict]:
    """Return ODPC v1.1 coverage for each local AI-product object."""
    return [ai_product_odpc_coverage(item) for item in portfolio["objects"] if item["kind"] == "ai_product"]


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
    odpc_coverages = ai_product_odpc_coverages(design)
    odpc_findings = [finding for coverage in odpc_coverages for finding in coverage["missing"]]
    questions = sorted({question_for[item["code"]] for item in findings if item["code"] in question_for})
    questions.extend(coverage["question"] for coverage in odpc_coverages if coverage["question"])
    return {"valid": True, "structurally_complete": not findings, "portfolio_hash": checked["content_hash"], "findings": findings, "odpc_ai_product_coverage": odpc_coverages, "odpc_findings": odpc_findings, "discovery_questions": questions, "limitations": ["Structural completion permits proposed values. It is not business approval, access confirmation, or production readiness.", "Missing ODPC AI-product inputs are non-blocking business-design gaps; they prevent only normative ODPC export."]}


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


def _odpc_value(claims: dict, field: str):
    return _value(claims, field)


def _language_list(value: object) -> list[dict]:
    values = value if isinstance(value, list) else [value]
    return [_language(item) for item in values if str(item).strip()]


def _ai_product_profile(item: dict) -> dict:
    """Map confirmed, sourced local claims to the ODPC v1.1 AIProduct profile."""
    claims = item["claims"]
    odpc = claims["odpc"]
    owner = {field: _odpc_value(odpc["owner"], field) for field in ("organization", "team", "role") if is_claim(odpc["owner"].get(field))}
    metrics = []
    for metric in odpc["evaluation"].values():
        metrics.append({
            "id": _odpc_value(metric, "id"), "name": _language(_odpc_value(metric, "name")),
            "measurementMethod": _language(_odpc_value(metric, "measurement_method")),
            "targetValue": _odpc_value(metric, "target_value"), "unit": _odpc_value(metric, "unit"), "status": _odpc_value(metric, "status"),
        })
    product = {
        "productID": _odpc_value(odpc, "product_id"), "productVersion": _odpc_value(odpc, "product_version"),
        "name": _language(_value(claims, "name")), "description": _language(_value(claims, "purpose")), "purpose": _language(_value(claims, "purpose")),
        "owner": owner, "productType": _odpc_value(odpc, "product_type"),
        "governance": {
            "autonomyLevel": _odpc_value(odpc, "autonomy_level"),
            "humanOversight": {"required": _odpc_value(odpc, "human_oversight_required"), "requirements": _language_list(_odpc_value(odpc, "human_oversight_requirements"))},
            "consequentialActionApproval": {"required": _odpc_value(odpc, "consequential_action_approval_required"), "requirements": _language_list(_odpc_value(odpc, "consequential_action_approval_requirements"))},
            "riskClassification": _odpc_value(odpc, "risk_classification"), "knownLimitations": _language_list(_odpc_value(odpc, "known_limitations")),
        },
        "evaluation": metrics,
    }
    return {"schema": "https://opendataproducts.org/odpc-v1.1/schema/ai-product.yaml", "version": "1.1", "kind": "AIProduct", "aiProduct": product}


def _ai_product_catalog_nodes(item: dict, profile: dict) -> list[dict]:
    product = profile["aiProduct"]
    reference = {
        "kind": "productReference", "id": item["id"], "productID": product["productID"], "productVersion": product["productVersion"],
        "name": product["name"], "description": product["description"], "productCategory": "ai_product", "owner": product["owner"],
        "productModel": {"standard": "ODPC", "version": "1.1", "profile": "AIProduct", "format": "yaml", "schema": "https://opendataproducts.org/odpc-v1.1/schema/ai-product.yaml", "$ref": f"ai-products/{item['id']}.odpc.yaml"},
    }
    inline = {"kind": "aiProduct", "id": item["id"], **product}
    return [{"node": inline}, {"node": reference}]


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
    catalog_nodes = []
    artifacts = []
    for item in products:
        path = root / "data-products" / f"{item['id']}.odps.yaml"
        _write(path, _odps_product(item)); artifacts.append(path)
        catalog_nodes.append({"node": {"kind": "productReference", "id": item["id"], "productID": item["id"], "productVersion": design["revision"], "name": _language(_value(item["claims"], "name")), "description": _language(_value(item["claims"], "purpose")), "productCategory": "data_product", "productModel": {"standard": "ODPS", "version": "4.0", "format": "yaml", "$ref": f"data-products/{item['id']}.odps.yaml"}}})
    for item in objectives:
        catalog_nodes.append({"node": {"kind": "businessObjective", "id": item["id"], "name": _language(_value(item["claims"], "name")), "description": _language(_value(item["claims"], "purpose"))}})
    for item in use_cases:
        catalog_nodes.append({"node": {"kind": "useCase", "id": item["id"], "name": _language(_value(item["claims"], "name")), "description": _language(_value(item["claims"], "purpose"))}})
    ai_profiles = {}
    for item, coverage in zip(ai_products, completion["odpc_ai_product_coverage"]):
        if coverage["coverage"] != "validated":
            continue
        profile = _ai_product_profile(item)
        path = root / "ai-products" / f"{item['id']}.odpc.yaml"
        _write(path, profile); artifacts.append(path); ai_profiles[item["id"]] = profile
        catalog_nodes.extend(_ai_product_catalog_nodes(item, profile))
    catalog_nodes.sort(key=lambda entry: 0 if entry["node"]["kind"] == "aiProduct" else 1 if entry["node"].get("productCategory") == "ai_product" else 2)
    catalog = {"schema": "https://opendataproducts.org/odpc-v1.1/schema/odpc.yaml", "version": "1.1", "kind": "Catalog", "catalog": {"metadata": {"id": design["portfolio_id"], "name": _language(design["title"]), "description": _language("Catalog derived from a Kentaro DesignPortfolio"), "status": "draft"}, "nodes": catalog_nodes}}
    odpc_path = root / "odpc.yaml"; _write(odpc_path, catalog); artifacts.append(odpc_path)
    nodes = []
    for item in objectives: nodes.append({"id": item["id"], "type": "BusinessObjective", "$ref": "odpc.yaml"})
    for item in use_cases: nodes.append({"id": item["id"], "type": "UseCase", "$ref": "odpc.yaml"})
    for item in ai_products:
        if item["id"] in ai_profiles: nodes.append({"id": item["id"], "type": "AIProduct", "$ref": f"ai-products/{item['id']}.odpc.yaml"})
    for item in products:
        nodes.extend(({"id": item["id"], "type": "DataProduct", "$ref": f"data-products/{item['id']}.odps.yaml"}, {"id": f"kpi-{item['id']}", "type": "KPI", "$ref": f"#product-kpi:{item['id']}"}))
    edges = []
    mapping = {"use-case-supports-objective": "supports", "use-case-requires-data-product": "uses", "ai-product-consumes-data-product": "uses", "use-case-delivered-by-ai-product": "dependsOn", "product-depends-on-product": "dependsOn", "data-product-reused-by-use-case": "uses"}
    node_ids = {node["id"] for node in nodes}
    for edge in design["relationships"]:
        if edge["kind"] in mapping and edge["from_id"] in node_ids and edge["to_id"] in node_ids: edges.append({"from": edge["from_id"], "to": edge["to_id"], "type": mapping[edge["kind"]], "confidence": _confidence(edge), "x-kentaro-relationship-id": edge["id"]})
    graph = {"schema": "https://opendataproducts.org/odpg-v1.0/schema/odpg.yaml", "version": "1.0", "kind": "Graph", "graph": {"metadata": {"id": f"graph-{design['portfolio_id']}", "name": _language(design["title"]), "description": _language("Draft ODPG graph derived from the DesignPortfolio"), "status": "draft"}, "nodes": nodes, "edges": edges}}
    odpg_path = root / "odpg.yaml"; _write(odpg_path, graph); artifacts.append(odpg_path)
    validations = [{**validate_odps(path), "path": path.relative_to(root).as_posix()} for path in artifacts]
    if ai_profiles:
        from open_data_products import validate_ai_product_bundle
        bundle = validate_ai_product_bundle(next(iter(ai_profiles.values())), catalog, graph)
        validations.append({"spec": "ODPC AIProduct bundle", "path": "ai-products", "valid": bundle.valid, "errors": bundle.errors, "sdk_version": "0.5.0"})
    if not all(item.get("valid") for item in validations): raise ValueError("Generated ODPS family specification failed SDK validation")
    return {"artifacts": artifacts, "validations": validations, "completion": completion}
