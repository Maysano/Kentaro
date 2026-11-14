"""Acceptance coverage for local assumption-change impact assessment."""
from __future__ import annotations

import unittest
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from kentaro.cli import main
from kentaro.design.impact import assess_impact, impact_report
from kentaro.design.portfolio import add_object, add_relationship, create_design_portfolio, make_claim, record_assumption_change, record_decision, save_portfolio, validate_portfolio
from kentaro.design.reports import readiness


class DesignImpactTests(unittest.TestCase):
    def _portfolio(self):
        source = ("bank-workshop", "v1", "risk-delay-design")
        claim = lambda value: make_claim(value, "user_confirmed", *source, asserted_at="2026-11-14T00:00:00+00:00")
        portfolio = create_design_portfolio("Customer risk assessment", "bank-risk")
        for object_id, kind, name in (
            ("risk-objective", "objective", "Reduce risk-assessment time"),
            ("risk-use-case", "use_case", "Assess customer risk"),
            ("risk-ai", "ai_product", "AI-assisted risk assessment"),
            ("customer-data", "data_product", "Customer information"),
            ("independent-use-case", "use_case", "Maintain address data"),
            ("independent-data", "data_product", "Address information"),
        ):
            portfolio = add_object(portfolio, object_id, kind, {"name": claim(name), "purpose": claim(name), "owner": claim("Business owner"), "lifecycle_status": claim("design")})
        confirmed = make_claim("relationship", "user_confirmed", *source, asserted_at="2026-11-14T00:00:00+00:00")
        portfolio = add_relationship(portfolio, "risk-supports", "risk-use-case", "risk-objective", "use-case-supports-objective", provenance=confirmed)
        portfolio = add_relationship(portfolio, "risk-ai-link", "risk-use-case", "risk-ai", "use-case-delivered-by-ai-product", provenance=confirmed)
        portfolio = add_relationship(portfolio, "risk-data-link", "risk-ai", "customer-data", "ai-product-consumes-data-product", provenance=confirmed)
        portfolio = add_relationship(portfolio, "independent-link", "independent-use-case", "independent-data", "use-case-requires-data-product", provenance=confirmed)
        portfolio = record_assumption_change(portfolio, "manual-gathering-delay", statement="Manual information gathering causes most delays.", scope="Customer risk assessment", state="introduced", claim_references=["claim:risk-use-case:purpose"], evidence_references=["ops-analysis:v1"], related_object_ids=["risk-ai"] , assessment_id="assumption-v1", assessed_at="2026-11-14T00:00:00+00:00")
        return record_decision(portfolio, "select-ai", subject="AI-assisted risk assessment", scope="Retail risk assessment", resolution="Select AI-assisted option", rationale="Information gathering is the primary delay", actor="Risk decision owner", related_object_ids=["risk-ai"], alternatives=["Human-only", "AI-assisted"], evidence_references=["ops-analysis:v1"], assumption_ids=["manual-gathering-delay"], decided_at="2026-11-14T00:00:00+00:00")

    def test_challenged_assumption_preserves_history_and_limits_impact_to_connected_branch(self):
        portfolio = self._portfolio()
        changed = record_assumption_change(portfolio, "manual-gathering-delay", statement="Approval and regulatory review cause most delays.", scope="Customer risk assessment", state="challenged", claim_references=["claim:risk-use-case:purpose"], evidence_references=["ops-analysis:v2"], related_object_ids=["risk-ai"], related_decision_ids=["select-ai"], assessment_id="assumption-v2", assessed_at="2026-11-14T01:00:00+00:00")
        self.assertTrue(validate_portfolio(changed)["valid"])
        self.assertEqual(changed["decisions"][0]["resolution"], "Select AI-assisted option")
        assessment = assess_impact(changed, "assumption-v2")
        by_id = {item["object_id"]: item for item in assessment["elements"]}
        self.assertEqual(by_id["risk-ai"]["classification"], "review_required")
        self.assertEqual(by_id["customer-data"]["classification"], "review_required")
        self.assertEqual(by_id["independent-data"]["classification"], "unaffected")
        self.assertTrue(assessment["decisions"][0]["requires_reassessment"])
        finding = next(item for item in readiness(changed)["findings"] if item["field"] == "assumption_reassessment_required")
        self.assertEqual(finding["decision_id"], "select-ai")
        self.assertIn("What changed", impact_report(changed, "assumption-v2")["markdown"])

    def test_subsequent_human_decision_resolves_reassessment_without_rewriting_original(self):
        changed = record_assumption_change(self._portfolio(), "manual-gathering-delay", statement="Approval and regulatory review cause most delays.", scope="Customer risk assessment", state="contradicted", evidence_references=["ops-analysis:v2"], related_object_ids=["risk-ai"], assessment_id="assumption-v2", assessed_at="2026-11-14T01:00:00+00:00")
        resolved = record_decision(changed, "select-ai-v2", subject="AI-assisted risk assessment", scope="Retail risk assessment", resolution="Retain only for evidence preparation", rationale="New analysis moves the value proposition from speed to preparation", actor="Risk decision owner", related_object_ids=["risk-ai"], alternatives=["Human-only", "AI-assisted preparation"], evidence_references=["ops-analysis:v2"], assumption_ids=["manual-gathering-delay"], resolves_assessment_ids=["assumption-v2"], supersedes="select-ai", decided_at="2026-11-14T02:00:00+00:00")
        self.assertEqual(resolved["decisions"][0]["resolution"], "Select AI-assisted option")
        self.assertFalse(assess_impact(resolved, "assumption-v2")["decisions"][0]["requires_reassessment"])
        self.assertFalse(any(item.get("decision_id") == "select-ai" for item in readiness(resolved)["findings"] if item["field"] == "assumption_reassessment_required"))

    def test_cli_records_and_reports_a_local_assumption_change(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                input_path = Path(directory) / ".kentaro/workspace/risk/portfolio.json"
                save_portfolio(self._portfolio(), input_path)
                self.assertEqual(main(["design", "record-assumption-change", "--input", str(input_path), "--id", "manual-gathering-delay", "--statement", "Approval and regulatory review cause most delays.", "--scope", "Customer risk assessment", "--state", "challenged", "--evidence-reference", "ops-analysis:v2", "--related-object-id", "risk-ai", "--assessment-id", "assumption-v2"]), 0)
                self.assertEqual(main(["design", "assess-impact", "--input", str(input_path), "--assessment-id", "assumption-v2"]), 0)
                output = Path(directory) / ".kentaro/workspace/risk/impact"
                self.assertEqual(main(["design", "impact-report", "--input", str(input_path), "--output-dir", str(output), "--assessment-id", "assumption-v2"]), 0)
                self.assertTrue((output / "decision-owner-impact.md").is_file())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
