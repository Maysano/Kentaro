"""Deterministic local Decision Context and delivery-handover packages.

The package is a point-in-time handover of a DesignPortfolio.  It deliberately
does not create Maysano records, grant approval, or claim implementation or
production readiness.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .portfolio import content_hash, iter_claims, validate_portfolio
from .render import render_canvas
from .reports import executive_summary, readiness
from .specifications import build_specifications, structural_completion


HANDOVER_SCHEMA_VERSION = 1
PACKAGE_MODEL = "KentaroDeliveryHandover"


def _json(value: object) -> str:
    """Use JSON's YAML 1.2 subset to keep the portable core dependency-free."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _write(path: Path, value: str | object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else _json(value), encoding="utf-8")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object_summary(item: dict) -> dict:
    return {
        "id": item["id"],
        "kind": item["kind"],
        "name": item["claims"]["name"],
        "purpose": item["claims"]["purpose"],
        "owner": item["claims"]["owner"],
        "lifecycle_status": item["claims"]["lifecycle_status"],
    }


def decision_context(portfolio: dict, *, assessment_stage: str | None = None) -> dict:
    """Derive a provenance-preserving Decision Context from a valid local design."""
    check = validate_portfolio(portfolio)
    if not check["valid"]:
        raise ValueError("DesignPortfolio is invalid")
    design = check["portfolio"]
    assessment = readiness(design, assessment_stage=assessment_stage)
    objects = design["objects"]
    context = {
        "schema_version": HANDOVER_SCHEMA_VERSION,
        "model": "DecisionContext",
        "status": "draft",
        "serialization": "json-compatible-yaml",
        "source": {
            "portfolio_model": design["model"],
            "portfolio_id": design["portfolio_id"],
            "portfolio_title": design["title"],
            "source_revision": design["revision"],
            "portfolio_hash": check["content_hash"],
            "assessment_stage": assessment["assessment_stage"],
        },
        "business_context": {
            "portfolio_claims": design["claims"],
            "objectives": [_object_summary(item) for item in objects if item["kind"] == "objective"],
            "use_cases": [_object_summary(item) for item in objects if item["kind"] == "use_case"],
        },
        "product_context": {
            "ai_products": [_object_summary(item) for item in objects if item["kind"] == "ai_product"],
            "data_products": [_object_summary(item) for item in objects if item["kind"] == "data_product"],
            "declared_relationships": design["relationships"],
        },
        "decision_records": [
            {
                "decision_id": finding["finding_id"],
                "affected_object_id": finding["affected_object_id"],
                "field": finding["field"],
                "category": finding["category"],
                "severity": finding["severity"],
                "state": "unresolved",
                "required_human_action": finding["required_resolution"],
                "source_claim_ids": finding["source_claim_ids"],
                "dependency_references": finding["dependency_references"],
            }
            for finding in assessment["findings"]
        ],
        "constraints": [
            {
                "affected_object_id": finding["affected_object_id"],
                "field": finding["field"],
                "category": finding["category"],
                "explanation": finding["explanation"],
            }
            for finding in assessment["findings"]
            if finding["category"] == "implementation_blocker"
        ],
        "outstanding_decisions": [
            finding["finding_id"] for finding in assessment["findings"] if finding["category"] == "decision_dependency"
        ],
        "limitations": [
            "This is a local design-derived draft, not a Maysano record or approval.",
            "Claims retain their source status; proposed, assumed, and unknown values are not established evidence.",
            "The package does not establish delivery authorization, implementation readiness, or production readiness.",
        ],
    }
    return context


def _evidence_manifest(design: dict) -> dict:
    entries = []
    for field, claim in iter_claims(design["claims"]):
        entries.append({"claim_id": f"claim:portfolio:{field}", "object_id": "portfolio", "field": field, "claim": claim})
    for item in design["objects"]:
        for field, claim in iter_claims(item["claims"]):
            entries.append({"claim_id": f"claim:{item['id']}:{field}", "object_id": item["id"], "field": field, "claim": claim})
    for edge in design["relationships"]:
        if edge.get("provenance"):
            entries.append({"claim_id": f"relationship:{edge['id']}", "relationship_id": edge["id"], "claim": edge["provenance"]})
    return {
        "schema_version": 1,
        "model": "KentaroEvidenceManifest",
        "status": "draft",
        "entries": entries,
        "limitations": ["This inventory records claim provenance only. It is not a verified evidence store or approval history."],
    }


def _delivery_brief(design: dict, context: dict, assessment: dict) -> str:
    names = lambda kind: ", ".join(item["claims"]["name"]["value"] for item in design["objects"] if item["kind"] == kind) or "None recorded"
    open_decisions = context["outstanding_decisions"]
    return "\n".join((
        f"# {design['title']} — Delivery Brief", "",
        "## Handover boundary", "",
        "This package is a deterministic local draft derived from a DesignPortfolio. It does not create or update a Maysano record, request approval, authorize delivery, or establish production readiness.", "",
        "## What is being handed over", "",
        f"- Objectives: {names('objective')}",
        f"- Use cases: {names('use_case')}",
        f"- AI products: {names('ai_product')}",
        f"- Data products: {names('data_product')}", "",
        "## Delivery constraints and decisions", "",
        f"Assessment stage: `{assessment['assessment_stage']}`. The Decision Context records {len(open_decisions)} decision dependencies and {len(assessment['findings'])} unresolved finding(s). Review them with accountable humans before any implementation commitment.", "",
        "## Specification mapping", "",
        "A review package intentionally excludes final ODPS, ODPC, and ODPG artefacts until the DesignPortfolio passes structural completion. A reviewed final ZIP contains deterministic, SDK-validated specifications. This boundary prevents unknown targets or disconnected objects from being presented as completed specifications.", "",
        "## For a coding agent", "",
        "Treat proposed, assumed, and unknown claims as unresolved input. Preserve source identifiers, revisions, and claim status. Do not infer approval, operational access, implementation detail, or production readiness from this package.", "",
    ))


def _readme(design: dict) -> str:
    return "\n".join((
        f"# {design['title']} handover package", "",
        "This is a local, deterministic snapshot of a Kentaro DesignPortfolio.", "",
        "- `decision-context.yaml` is JSON-compatible YAML and preserves the business, product, and decision context.",
        "- `portfolio/` contains the frozen source design and its rendered canvas.",
        "- `governance/` contains provenance and deterministic readiness findings; it does not contain approvals or platform records.",
        "- `specifications/ai-products/` holds draft AI-product definitions. A review package does not include final ODPS, ODPC, or ODPG files; a structurally complete, human-confirmed final ZIP includes their deterministic, SDK-validated exports.",
        "",
        "Regenerate a new package after the source revision or content changes. Validate the package and use handover status to detect staleness before consuming it.", "",
    ))


def _specification_status() -> list[dict]:
    return [
        {"kind": kind, "status": "unsupported", "reason": "No deterministic DesignPortfolio mapping contract has been implemented."}
        for kind in ("ODPC", "ODPG", "ODPS")
    ]


def _validated_specification_status(validations: list[dict]) -> list[dict]:
    return [{"kind": item.get("spec", "ODPS").upper(), "path": item["path"], "status": "validated", "sdk_version": item.get("sdk_version")} for item in validations]


def generate_handover(
    portfolio: dict,
    destination: str | Path,
    *,
    assessment_stage: str | None = None,
    package_status: str = "draft",
    review_confirmation: dict | None = None,
) -> dict:
    """Create a local review package; final delivery is created by export_handover."""
    if package_status not in {"draft", "reviewed"}:
        raise ValueError("Handover package status must be draft or reviewed")
    if package_status == "reviewed" and review_confirmation is None:
        raise ValueError("A reviewed handover requires an explicit user confirmation record")
    check = validate_portfolio(portfolio)
    if not check["valid"]:
        raise ValueError("DesignPortfolio is invalid")
    target = Path(destination).expanduser().resolve()
    if target.exists():
        raise ValueError("Handover destination already exists; choose a new local package directory.")
    target.parent.mkdir(parents=True, exist_ok=True)
    design = check["portfolio"]
    assessment = readiness(design, assessment_stage=assessment_stage)
    context = decision_context(design, assessment_stage=assessment_stage)
    completion = structural_completion(design)
    if package_status == "reviewed" and not completion["structurally_complete"]:
        raise ValueError("Final handover requires structural completion: resolve required KPI, relationship, and data-product findings before confirmation.")
    temporary = Path(tempfile.mkdtemp(prefix="kentaro-handover-", dir=target.parent))
    try:
        _write(temporary / "decision-context.yaml", context)
        _write(temporary / "executive-summary.md", executive_summary(design, assessment))
        _write(temporary / "delivery-brief.md", _delivery_brief(design, context, assessment))
        _write(temporary / "README.md", _readme(design))
        _write(temporary / "portfolio" / "design-portfolio.json", design)
        _write(temporary / "portfolio" / "relationships.yaml", {"serialization": "json-compatible-yaml", "relationships": design["relationships"]})
        _write(temporary / "portfolio" / "canvas.html", render_canvas(design, assessment_stage=assessment_stage))
        _write(temporary / "governance" / "evidence-manifest.json", _evidence_manifest(design))
        _write(temporary / "governance" / "unresolved-decisions.json", {"status": "draft", "decision_records": context["decision_records"], "outstanding_decisions": context["outstanding_decisions"]})
        _write(temporary / "governance" / "readiness-report.json", assessment)
        _write(temporary / "governance" / "structural-completion.json", completion)
        if review_confirmation is not None:
            _write(temporary / "governance" / "user-confirmation.json", review_confirmation)
        for item in (entry for entry in design["objects"] if entry["kind"] == "ai_product"):
            _write(temporary / "specifications" / "ai-products" / f"{item['id']}.json", {
                "schema_version": 1,
                "model": "KentaroAIProductDefinition",
                "status": "draft",
                "source": {"portfolio_id": design["portfolio_id"], "source_revision": design["revision"], "portfolio_hash": check["content_hash"]},
                "definition": item,
                "limitations": ["This draft definition is not an operational AI-product specification or delivery authorization."],
            })
        specifications = None
        specification_status = _specification_status()
        if package_status == "reviewed":
            specifications = build_specifications(design, temporary / "specifications")
            specification_status = _validated_specification_status(specifications["validations"])
        validation = {
            "schema_version": 1,
            "valid": True,
            "package_status": package_status,
            "source_portfolio_valid": True,
            "source_portfolio_hash": check["content_hash"],
            "readiness": assessment["summary"],
            "structural_completion": completion,
            "specification_status": specification_status,
            "limitations": ["Validation checks package integrity and source alignment. A reviewed status records a local user confirmation only; it does not establish external approval, implementation readiness, or production readiness."],
        }
        _write(temporary / "validation" / "results.json", validation)
        artefacts = []
        for path in sorted(path for path in temporary.rglob("*") if path.is_file()):
            artefacts.append({"path": path.relative_to(temporary).as_posix(), "sha256": _digest(path)})
        package = {
            "schema_version": HANDOVER_SCHEMA_VERSION,
            "model": PACKAGE_MODEL,
            "status": package_status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": {"portfolio_id": design["portfolio_id"], "source_revision": design["revision"], "portfolio_hash": check["content_hash"], "assessment_stage": assessment["assessment_stage"]},
            "artefacts": artefacts,
            "specification_status": specification_status,
            "limitations": ["No Maysano graph or governance objects were created or modified.", "A reviewed status is a local user confirmation, not approval or production-readiness authority."],
        }
        _write(temporary / "manifest.json", package)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return {"package": target, "manifest": package, "validation": validation}


def prepare_handover_review(portfolio: dict, destination: str | Path, *, assessment_stage: str | None = None) -> dict:
    """Create local material for a human review before final handover export."""
    return generate_handover(portfolio, destination, assessment_stage=assessment_stage, package_status="draft")


def export_handover(
    portfolio: dict,
    destination: str | Path,
    *,
    reviewer: str,
    confirmation: str,
    acknowledge_all_open_decisions: bool,
    assessment_stage: str | None = None,
) -> dict:
    """Create the final portable ZIP only after an explicit local user confirmation."""
    if not reviewer.strip() or not confirmation.strip():
        raise ValueError("Final handover export requires the confirming user's name and confirmation statement")
    if not acknowledge_all_open_decisions:
        raise ValueError("Final handover export requires explicit acknowledgement of all open decisions")
    target = Path(destination).expanduser().resolve()
    if target.suffix.lower() != ".zip":
        raise ValueError("Final handover output must use a .zip filename")
    if target.exists():
        raise ValueError("Handover export already exists; choose a new ZIP filename.")
    context = decision_context(portfolio, assessment_stage=assessment_stage)
    confirmation_record = {
        "schema_version": 1,
        "model": "KentaroUserConfirmation",
        "status": "reviewed",
        "reviewer": reviewer.strip(),
        "confirmation": confirmation.strip(),
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "source": context["source"],
        "acknowledged_open_decision_ids": context["outstanding_decisions"],
        "limitations": ["This local confirmation authorizes generation of this handover export only. It is not a Maysano approval, implementation authorization, or production-readiness decision."],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kentaro-handover-export-", dir=target.parent) as temporary:
        staging = Path(temporary) / "handover"
        generated = generate_handover(
            portfolio,
            staging,
            assessment_stage=assessment_stage,
            package_status="reviewed",
            review_confirmation=confirmation_record,
        )
        archive = Path(temporary) / target.name
        with zipfile.ZipFile(archive, mode="x", compression=zipfile.ZIP_DEFLATED) as stream:
            for path in sorted(path for path in staging.rglob("*") if path.is_file()):
                stream.write(path, path.relative_to(staging).as_posix())
        archive.replace(target)
    return {"package": target, "manifest": generated["manifest"], "validation": generated["validation"], "confirmation": confirmation_record}


def _load_manifest(package: str | Path) -> tuple[Path, dict, Callable[[str], bytes]]:
    root = Path(package).expanduser().resolve()
    try:
        if root.is_dir():
            read_file = lambda relative: (root / relative).read_bytes()
            manifest_data = json.loads(read_file("manifest.json"))
        elif root.is_file() and zipfile.is_zipfile(root):
            def read_file(relative):
                with zipfile.ZipFile(root) as stream:
                    return stream.read(relative)
            manifest_data = json.loads(read_file("manifest.json"))
        else:
            raise OSError("Package must be a directory or ZIP archive")
    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise ValueError("Handover package requires a readable manifest.json") from error
    if manifest_data.get("model") != PACKAGE_MODEL or manifest_data.get("schema_version") != HANDOVER_SCHEMA_VERSION:
        raise ValueError("Unsupported handover manifest")
    return root, manifest_data, read_file


def validate_handover(package: str | Path) -> dict:
    """Verify package artifact hashes without claiming source freshness."""
    _, manifest_data, read_file = _load_manifest(package)
    findings = []
    for artefact in manifest_data.get("artefacts", []):
        relative = Path(artefact.get("path", ""))
        if not relative.parts or relative.is_absolute() or ".." in relative.parts:
            findings.append({"code": "unsafe_artifact_path", "path": artefact.get("path")})
            continue
        try:
            content = read_file(relative.as_posix())
        except (OSError, KeyError, zipfile.BadZipFile):
            findings.append({"code": "missing_artifact", "path": relative.as_posix()})
            continue
        if hashlib.sha256(content).hexdigest() != artefact.get("sha256"):
            findings.append({"code": "artifact_digest_mismatch", "path": relative.as_posix()})
    return {
        "valid": not findings,
        "package_status": manifest_data["status"],
        "source": manifest_data["source"],
        "findings": findings,
        "specification_status": manifest_data.get("specification_status", []),
        "limitations": ["Integrity validation does not establish the current source state, approval, implementation readiness, or production readiness."],
    }


def inspect_handover(package: str | Path) -> dict:
    """Return a skim-friendly package summary together with integrity findings."""
    root, manifest_data, read_file = _load_manifest(package)
    integrity = validate_handover(root)
    try:
        context = json.loads(read_file("decision-context.yaml"))
    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise ValueError("Handover package requires a readable decision-context.yaml") from error
    return {
        "valid": integrity["valid"],
        "package_status": manifest_data["status"],
        "source": manifest_data["source"],
        "artefact_count": len(manifest_data.get("artefacts", [])),
        "decision_context": {
            "objective_count": len(context["business_context"]["objectives"]),
            "use_case_count": len(context["business_context"]["use_cases"]),
            "ai_product_count": len(context["product_context"]["ai_products"]),
            "data_product_count": len(context["product_context"]["data_products"]),
            "unresolved_decision_count": len(context["outstanding_decisions"]),
            "constraint_count": len(context["constraints"]),
        },
        "integrity_findings": integrity["findings"],
        "specification_status": manifest_data.get("specification_status", []),
        "limitations": integrity["limitations"],
    }


def handover_status(portfolio: dict, package: str | Path) -> dict:
    """Compare a package against the current DesignPortfolio and its own integrity."""
    check = validate_portfolio(portfolio)
    if not check["valid"]:
        return {"valid": False, "findings": check["findings"]}
    _, package_manifest, _ = _load_manifest(package)
    source = package_manifest["source"]
    stale = source.get("portfolio_hash") != check["content_hash"] or source.get("source_revision") != check["portfolio"]["revision"]
    integrity = validate_handover(package)
    return {
        "valid": integrity["valid"],
        "stale": stale,
        "package_status": package_manifest["status"],
        "current_source": {"portfolio_id": check["portfolio"]["portfolio_id"], "source_revision": check["portfolio"]["revision"], "portfolio_hash": check["content_hash"]},
        "package_source": source,
        "integrity_findings": integrity["findings"],
        "limitations": ["Staleness means the local source changed after generation; it does not by itself determine approval or delivery fitness."],
    }
