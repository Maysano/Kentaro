"""Redacted, append-oriented local evidence output; not a platform audit log."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .schemas import index_objects


SENSITIVE_KEY = re.compile(r"(?:api[_-]?key|authorization|credential|password|secret|token)", re.IGNORECASE)
BEARER_VALUE = re.compile(r"^Bearer\s+.+$", re.IGNORECASE)


def _redact(value: object, key: str | None = None) -> object:
    if key and SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, str) and BEARER_VALUE.match(value):
        return "[REDACTED]"
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        return {str(item_key): _redact(item_value, str(item_key)) for item_key, item_value in value.items()}
    return value


def build_evidence_event(bundle: dict, evaluation: dict, *, actor: str, output_references: list[dict] | None = None, occurred_at: str | None = None) -> dict:
    """Build one redacted local evidence event without persisting it."""
    if not isinstance(actor, str) or not actor:
        raise ValueError("Evidence actor must be a nonempty string")
    if output_references is not None and not isinstance(output_references, list):
        raise ValueError("Evidence output_references must be a list")
    index = index_objects(bundle)
    request_ref = evaluation["execution_request"]
    request = index[(request_ref["id"], request_ref["version"])]
    evaluated = evaluation["evaluated_objects"]
    chain = [index[(reference["id"], reference["version"])] for reference in evaluated]
    context_packages = [item for item in index.values() if item["object_type"] == "context_package"]
    payload = {
        "context_packages": [{"id": item["id"], "version": item["version"], "source_references": item["source_references"]} for item in context_packages],
        "execution_request": request,
        "evaluated_objects": evaluated,
        "policy_evaluation": evaluation,
        "output_references": output_references or [],
        "corrections": [item for item in index.values() if item["object_type"] == "correction"],
    }
    timestamp = occurred_at or datetime.now(timezone.utc).isoformat()
    event_id_material = f"{request['id']}:{request['version']}:{evaluation['evaluated_at']}:{timestamp}".encode("utf-8")
    return _redact({
        "id": "evidence-" + hashlib.sha256(event_id_material).hexdigest()[:16],
        "object_type": "evidence_event",
        "schema_version": 1,
        "version": 1,
        "created_at": timestamp,
        "occurred_at": timestamp,
        "actor": actor,
        "event_type": "policy_evaluation",
        "source_references": [reference for item in context_packages for reference in item["source_references"]],
        "relationship_references": [
            {"id": request["id"], "version": request["version"]},
            *[{"id": item["id"], "version": item["version"]} for item in chain],
        ],
        "work_envelope_reference": {"id": chain[1]["id"], "version": chain[1]["version"]},
        "payload": payload,
    })


def _previous_hash(path: Path) -> str | None:
    if not path.exists() or not path.stat().st_size:
        return None
    with path.open(encoding="utf-8") as stream:
        lines = [line for line in stream if line.strip()]
    if not lines:
        return None
    try:
        previous = json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise ValueError("Existing evidence log is not valid JSON Lines") from error
    value = previous.get("record_hash")
    if value is not None and not isinstance(value, str):
        raise ValueError("Existing evidence record hash is invalid")
    return value


def append_evidence_event(path: str | Path, event: dict, *, hash_chain: bool = False) -> dict:
    """Append a redacted event to a local JSONL evidence log and return its stored form."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stored = _redact(event)
    if hash_chain:
        predecessor = _previous_hash(destination)
        stored["previous_hash"] = predecessor
        payload = json.dumps(stored, sort_keys=True, separators=(",", ":")).encode("utf-8")
        stored["record_hash"] = hashlib.sha256(payload).hexdigest()
    with destination.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(stored, sort_keys=True) + "\n")
    return stored


def verify_evidence_log(path: str | Path) -> dict:
    """Verify optional JSONL hash chaining; this does not confer immutable storage."""
    source = Path(path)
    try:
        lines = [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as error:
        raise ValueError("Unable to read local evidence log") from error
    findings: list[dict] = []
    predecessor = None
    chained_records = 0
    for line_number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            findings.append({"line": line_number, "code": "invalid_json", "message": "Evidence record is not valid JSON."})
            continue
        if not isinstance(record, dict):
            findings.append({"line": line_number, "code": "invalid_record", "message": "Evidence record must be a JSON object."})
            continue
        record_hash = record.get("record_hash")
        if record_hash is None:
            if chained_records:
                findings.append({"line": line_number, "code": "missing_record_hash", "message": "Hash-chained log contains an unchained record."})
            continue
        if not isinstance(record_hash, str):
            findings.append({"line": line_number, "code": "invalid_record_hash", "message": "record_hash must be a string."})
            continue
        candidate = dict(record)
        candidate.pop("record_hash")
        expected_hash = hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if record_hash != expected_hash:
            findings.append({"line": line_number, "code": "record_hash_mismatch", "message": "Evidence record content does not match its record_hash."})
        if record.get("previous_hash") != predecessor:
            findings.append({"line": line_number, "code": "predecessor_mismatch", "message": "Evidence record previous_hash does not match the prior record."})
        predecessor = record_hash
        chained_records += 1
    return {
        "valid": not findings,
        "records": len(lines),
        "hash_chained_records": chained_records,
        "findings": findings,
    }
