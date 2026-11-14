"""Deterministic assessment of text material prepared for AI use.

The module reports only observable text indicators.  It deliberately does not
claim that a policy is complete, approved, legally compliant, or safe for
production use.
"""
from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path


SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}
DIMENSIONS = (
    ("readability", "Readability and source coverage"),
    ("terminology", "Terms and terminology"),
    ("interpretation", "Practical interpretation"),
    ("decision_rules", "Decision rules and exceptions"),
    ("human_ai_boundary", "Human and AI boundary"),
    ("ownership", "Ownership and freshness"),
    ("verification", "Verification cases"),
)


def _line_reference(lines: list[str], line_number: int) -> dict:
    text = lines[line_number - 1].strip()
    return {"line": line_number, "excerpt": text[:240]}


def _first_match(lines: list[str], patterns: tuple[str, ...]) -> dict | None:
    expression = re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.IGNORECASE)
    for number, line in enumerate(lines, start=1):
        if expression.search(line):
            return _line_reference(lines, number)
    return None


def _all_matches(lines: list[str], patterns: tuple[str, ...], *, limit: int = 3) -> list[dict]:
    expression = re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.IGNORECASE)
    matches = []
    for number, line in enumerate(lines, start=1):
        if expression.search(line):
            matches.append(_line_reference(lines, number))
            if len(matches) == limit:
                break
    return matches


def _finding(dimension: str, status: str, message: str, work_type: str, evidence: list[dict] | None = None) -> dict:
    return {
        "dimension": dimension,
        "status": status,
        "message": message,
        "work_type": work_type,
        "evidence": evidence or [],
    }


def _title(lines: list[str], fallback: str) -> str:
    for line in lines:
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    for line in lines:
        if line.strip():
            return line.strip()[:120]
    return fallback


def _intended_use_target(intended_use: str) -> tuple[int, str]:
    value = intended_use.lower()
    if re.search(r"\b(agent|autonom|workflow|act(?:ion|ing)?|decision)\b", value):
        return 4, "The stated use can guide an agent, workflow, action, or decision; explicit boundaries, review, and tests are needed."
    if re.search(r"\b(generate|draft|write|review|check|evaluate|assess)\b", value):
        return 3, "The stated use generates, reviews, or evaluates content; practical interpretation and decision rules are needed."
    return 2, "The stated use is treated as retrieval or question answering unless a more consequential use is supplied."


def _current_level(findings: list[dict]) -> tuple[int, str]:
    observed = {item["dimension"] for item in findings if item["status"] == "observed"}
    level = 1
    if {"readability", "terminology"}.issubset(observed):
        level = 2
    if level >= 2 and {"interpretation", "decision_rules"}.issubset(observed):
        level = 3
    if level >= 3 and {"human_ai_boundary", "ownership", "verification"}.issubset(observed):
        level = 4
    labels = {
        1: "Source material only",
        2: "Readable, traceable source material",
        3: "Material with operational interpretation indicators",
        4: "Material with governance and verification indicators",
    }
    return level, labels[level]


def _markdown_cell(value: object) -> str:
    """Keep source-derived values data within a Markdown table cell."""
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def _work_size(findings: list[dict]) -> tuple[str, str]:
    gaps = sum(item["status"] != "observed" for item in findings)
    if gaps <= 1:
        return "S", "Few observable gaps; human review still determines whether the material is sufficient."
    if gaps <= 4:
        return "M", "Several observable gaps require clarification or enrichment with the accountable owner."
    return "L", "Most governance and operational indicators are absent from this source; expect material owner-led enrichment."


def assess_context(source: str | Path, *, intended_use: str) -> dict:
    """Assess one UTF-8 Markdown or text source without sending it anywhere."""
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Context input is not a file: {path}")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        allowed = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Context input must be one of {allowed}; convert other formats to reviewed text first")
    if not intended_use.strip():
        raise ValueError("--intended-use must not be empty")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Context input must be UTF-8 text") from error
    if not text.strip():
        raise ValueError("Context input is empty")

    lines = text.splitlines()
    findings: list[dict] = []

    inaccessible = _all_matches(lines, (r"!\[[^\]]*\]\([^)]*\)", r"```(?:mermaid|plantuml)\b", r"<img\b"))
    if inaccessible:
        findings.append(_finding("readability", "needs_review", "Images or diagrams are represented in the text source; verify that their decision-relevant content has been converted to text.", "conversion", inaccessible))
    else:
        findings.append(_finding("readability", "observed", "The supplied source is directly readable UTF-8 text; visual-only source coverage was not detected.", "conversion", [_line_reference(lines, 1)]))

    definitions = _all_matches(lines, (r"\bdefinition\b", r"\bdefinitions\b", r"\bglossary\b", r"\bterminology\b", r"\bmeans\b", r"\bdefined as\b"))
    vague = _all_matches(lines, (r"\bas soon as possible\b", r"\bpromptly\b", r"\bsignificant\b", r"\bappropriate\b", r"\bwhen necessary\b", r"\bwhere possible\b"))
    if definitions and not vague:
        findings.append(_finding("terminology", "observed", "Definition or glossary indicators were found and no configured ambiguous-term indicator was found.", "clarification", definitions))
    elif vague:
        findings.append(_finding("terminology", "needs_review", "Potentially ambiguous terms need an owner-confirmed definition for AI use.", "clarification", vague))
    else:
        findings.append(_finding("terminology", "not_evident", "No glossary or definition indicator was found in this source; terminology may be defined elsewhere.", "clarification"))

    interpretation = _all_matches(lines, (r"^\s{0,3}#{1,6}\s+.*\b(principle|policy|guidance|interpretation|purpose)\b", r"\bin practice\b", r"\bfor example\b", r"\be\.g\.\b"))
    if interpretation:
        findings.append(_finding("interpretation", "observed", "Practical interpretation or example indicators were found.", "expert_enrichment", interpretation))
    else:
        findings.append(_finding("interpretation", "not_evident", "No practical interpretation or example indicator was found; a reviewer must confirm how the material applies in real cases.", "expert_enrichment"))

    rules = _all_matches(lines, (r"\bmust\b", r"\bshall\b", r"\brequired\b", r"\bonly if\b", r"\bdo not\b"))
    exceptions = _all_matches(lines, (r"\bunless\b", r"\bexcept\b", r"\bexception\b", r"\botherwise\b", r"\bescalat(?:e|ion)\b"))
    if rules and exceptions:
        findings.append(_finding("decision_rules", "observed", "Decision-rule and exception/escalation indicators were found.", "expert_enrichment", rules[:2] + exceptions[:1]))
    elif rules:
        findings.append(_finding("decision_rules", "needs_review", "Rule indicators were found, but no exception or escalation indicator was found in this source.", "expert_enrichment", rules))
    else:
        findings.append(_finding("decision_rules", "not_evident", "No decision-rule indicator was found; applicability and exceptions may be held outside this source.", "expert_enrichment"))

    boundary = _all_matches(lines, (r"\bAI\b", r"\bartificial intelligence\b", r"\bagent\b", r"\bhuman\b", r"\bapproval\b", r"\bescalat(?:e|ion)\b", r"\bdo not\b"))
    boundary_has_ai = _first_match(lines, (r"\bAI\b", r"\bartificial intelligence\b", r"\bagent\b"))
    boundary_has_human = _first_match(lines, (r"\bhuman\b", r"\bapproval\b", r"\bescalat(?:e|ion)\b"))
    if boundary_has_ai and boundary_has_human:
        findings.append(_finding("human_ai_boundary", "observed", "AI/agent and human-review or escalation indicators were found.", "approval_and_testing", boundary))
    else:
        findings.append(_finding("human_ai_boundary", "needs_review", "The source does not show both AI/agent scope and a human review or escalation boundary.", "approval_and_testing", boundary))

    ownership = _all_matches(lines, (r"\bowner\b", r"\baccountable\b", r"\bapproved by\b", r"\bversion\b", r"\breview date\b", r"\blast updated\b", r"\bnext review\b"))
    ownership_has_owner = _first_match(lines, (r"\bowner\b", r"\baccountable\b", r"\bapproved by\b"))
    ownership_has_freshness = _first_match(lines, (r"\bversion\b", r"\breview date\b", r"\blast updated\b", r"\bnext review\b"))
    if ownership_has_owner and ownership_has_freshness:
        findings.append(_finding("ownership", "observed", "Ownership/approval and version/review indicators were found.", "approval_and_testing", ownership))
    else:
        findings.append(_finding("ownership", "needs_review", "The source does not show both accountable ownership and a version or review-cycle indicator.", "approval_and_testing", ownership))

    verification = _all_matches(lines, (r"\btest case\b", r"\bscenario\b", r"\bexample\b", r"\bexpected (?:result|behavio[u]?r)\b", r"\bacceptance criteria\b"))
    if verification:
        findings.append(_finding("verification", "observed", "Test, scenario, example, or expected-behaviour indicators were found.", "approval_and_testing", verification))
    else:
        findings.append(_finding("verification", "not_evident", "No test or scenario indicator was found; this does not show whether tests exist elsewhere.", "approval_and_testing"))

    current_level, current_label = _current_level(findings)
    target_level, target_reason = _intended_use_target(intended_use)
    workload, workload_reason = _work_size(findings)
    source_hash = sha256(text.encode("utf-8")).hexdigest()
    return {
        "schema_version": 1,
        "model": "KentaroContextAssessment",
        "local_only": True,
        "source": {
            "path": str(path),
            "name": _title(lines, path.stem),
            "format": path.suffix.lower().lstrip("."),
            "sha256": source_hash,
            "line_count": len(lines),
        },
        "intended_use": intended_use,
        "assessment": {
            "current_level": {"level": current_level, "label": current_label},
            "recommended_target_level": {"level": target_level, "reason": target_reason},
            "indicative_workload": {"class": workload, "reason": workload_reason},
            "findings": findings,
        },
        "suggested_test_cases": [
            "ordinary case", "boundary case", "exception", "conflicting instruction", "missing information"
        ],
        "limitations": [
            "This is a deterministic indicator scan of one supplied text source, not a semantic audit.",
            "A missing indicator means only that it was not found in this source; it may exist elsewhere.",
            "The assessment does not establish content accuracy, legal compliance, approval, data access, production readiness, or authority to act.",
            "Convert PDFs, images, diagrams, and tables to reviewed text before assessment; this command does not interpret them.",
        ],
    }


def render_context_report(assessment: dict) -> str:
    """Render a compact Markdown report without changing the assessment."""
    data = assessment["assessment"]
    source = assessment["source"]
    lines = [
        "# Context assessment",
        "",
        f"**Source:** {_markdown_cell(source['name'])} · **Format:** {_markdown_cell(source['format'])} · **Source digest:** `{source['sha256']}`",
        f"**Intended use:** {_markdown_cell(assessment['intended_use'])}",
        "",
        "## Assessment summary",
        "",
        f"- **Current indicator level:** {data['current_level']['level']} · {data['current_level']['label']}",
        f"- **Recommended target level:** {data['recommended_target_level']['level']} · {data['recommended_target_level']['reason']}",
        f"- **Indicative work size:** {data['indicative_workload']['class']} · {data['indicative_workload']['reason']}",
        "",
        "## Evidence-linked findings",
        "",
        "| Dimension | Status | Finding | Evidence | Work type |",
        "|---|---|---|---|---|",
    ]
    labels = dict(DIMENSIONS)
    for item in data["findings"]:
        evidence = "; ".join(f"line {ref['line']}: {_markdown_cell(ref['excerpt'])}" for ref in item["evidence"]) or "Not evident in this source"
        lines.append(f"| {_markdown_cell(labels[item['dimension']])} | {_markdown_cell(item['status'].replace('_', ' '))} | {_markdown_cell(item['message'])} | {evidence} | {_markdown_cell(item['work_type'].replace('_', ' '))} |")
    lines.extend([
        "",
        "## Suggested review cases",
        "",
        *[f"- {case}" for case in assessment["suggested_test_cases"]],
        "",
        "## Limits",
        "",
        *[f"- {limit}" for limit in assessment["limitations"]],
        "",
    ])
    return "\n".join(lines)


def write_context_assessment(assessment: dict, output_dir: str | Path) -> dict:
    """Write the JSON evidence record and its Markdown report to a local directory."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "context-assessment.json"
    markdown_path = destination / "context-assessment.md"
    if json_path.exists() or markdown_path.exists():
        raise ValueError(f"Context assessment output already exists in {destination}")
    json_path.write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_context_report(assessment), encoding="utf-8")
    return {"output_dir": str(destination), "json": str(json_path), "report": str(markdown_path)}
