import io
import json
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from kentaro.cli import main
from kentaro.governance import append_evidence_event, build_evidence_event, evaluate_execution_request, load_bundle, validate_bundle, verify_evidence_log


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "examples/configs/demo.toml"
EXAMPLE = ROOT / "examples/governance/retention-review.json"
EVALUATED_AT = "2026-10-17T09:00:00Z"


def object_by_id(bundle, object_id):
    return next(item for item in bundle["objects"] if item["id"] == object_id)


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.bundle = load_bundle(EXAMPLE)

    def evaluate(self, bundle=None):
        return evaluate_execution_request(bundle or self.bundle, "request-retention-note", evaluated_at=EVALUATED_AT)

    def test_example_bundle_validates_and_allowed_is_not_execution_permission(self):
        self.assertEqual(validate_bundle(self.bundle), {"valid": True, "findings": []})
        result = self.evaluate()
        self.assertEqual(result["outcome"], "allowed")
        self.assertFalse(result["execution_permitted"])
        self.assertEqual(result["rules"][0]["id"], "structurally_in_scope")

    def test_execution_package_cannot_expand_work_envelope(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "package-retention-review")["tools"].append("external.send_email")
        result = validate_bundle(bundle)
        self.assertFalse(result["valid"])
        self.assertTrue(any(finding["code"] == "package_expands_envelope" for finding in result["findings"]))

    def test_missing_owner_escalates(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "work-retention-review")["owner"] = None
        self.assertEqual(self.evaluate(bundle)["outcome"], "escalated")

    def test_expired_approval_data_escalates_without_processing_approval(self):
        bundle = deepcopy(self.bundle)
        request = object_by_id(bundle, "request-retention-note")
        request["approval_required"] = True
        request["approval_expires_at"] = "2026-10-16T00:00:00Z"
        result = self.evaluate(bundle)
        self.assertEqual(result["outcome"], "escalated")
        self.assertEqual(result["rules"][0]["id"], "expired_approval")
        self.assertFalse(result["execution_permitted"])

    def test_approval_required_is_recorded_without_external_approval(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "request-retention-note")["approval_required"] = True
        with patch("kentaro.api.live.urlopen") as urlopen:
            result = self.evaluate(bundle)
        self.assertEqual(result["outcome"], "approval_required")
        self.assertFalse(result["execution_permitted"])
        urlopen.assert_not_called()

    def test_tool_outside_work_envelope_is_denied(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "request-retention-note")["tool"] = "external.send_email"
        result = self.evaluate(bundle)
        self.assertEqual(result["outcome"], "denied")
        self.assertEqual(result["rules"][0]["id"], "tool_outside_envelope")

    def test_stale_context_escalates(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "context-retention-review")["freshness"] = "stale"
        self.assertEqual(self.evaluate(bundle)["outcome"], "escalated")

    def test_conflicting_context_escalates(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "context-retention-review")["conflicts"] = ["Decision owner differs between sources"]
        self.assertEqual(self.evaluate(bundle)["outcome"], "escalated")

    def test_authority_escalation_is_denied(self):
        bundle = deepcopy(self.bundle)
        object_by_id(bundle, "request-retention-note")["requested_authority"] = 2
        result = self.evaluate(bundle)
        self.assertEqual(result["outcome"], "denied")
        self.assertEqual(result["rules"][0]["id"], "authority_escalation")

    def test_evidence_is_redacted_hash_chained_and_reproduces_context_and_authority(self):
        evaluation = self.evaluate()
        event = build_evidence_event(self.bundle, evaluation, actor="test-user", occurred_at=EVALUATED_AT)
        rendered = json.dumps(event)
        self.assertNotIn("synthetic-secret-never-export", rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertEqual(event["payload"]["context_packages"][0]["id"], "context-retention-review")
        self.assertEqual(event["payload"]["evaluated_objects"][1]["id"], "work-retention-review")
        self.assertEqual(event["payload"]["evaluated_objects"][2]["id"], "mandate-commercial-analysis")
        self.assertEqual(event["actor"], "test-user")
        self.assertEqual(event["source_references"][0]["version"], 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            first = append_evidence_event(path, event, hash_chain=True)
            second = append_evidence_event(path, event, hash_chain=True)
            self.assertIsNone(first["previous_hash"])
            self.assertEqual(second["previous_hash"], first["record_hash"])
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 2)
            self.assertEqual(verify_evidence_log(path)["findings"], [])
            self.assertTrue(verify_evidence_log(path)["valid"])
            path.write_text(path.read_text(encoding="utf-8").replace('"actor": "test-user"', '"actor": "tampered"', 1), encoding="utf-8")
            self.assertFalse(verify_evidence_log(path)["valid"])

    def test_cli_validates_evaluates_and_exports_local_only(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "evidence.jsonl"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(main(["--config", str(CONFIG), "object", "validate", "--input", str(EXAMPLE)]), 0)
                self.assertEqual(main(["--config", str(CONFIG), "policy", "evaluate", "--input", str(EXAMPLE), "--request-id", "request-retention-note", "--evaluated-at", EVALUATED_AT]), 0)
                self.assertEqual(main(["--config", str(CONFIG), "evidence", "export", "--input", str(EXAMPLE), "--request-id", "request-retention-note", "--output", str(output), "--actor", "test-user", "--hash-chain", "--evaluated-at", EVALUATED_AT]), 0)
                self.assertEqual(main(["--config", str(CONFIG), "evidence", "verify", "--input", str(output)]), 0)
            output_text = stdout.getvalue()
            self.assertIn('"valid": true', output_text)
            self.assertIn('"outcome": "allowed"', output_text)
            self.assertEqual(stderr.getvalue(), "")
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
