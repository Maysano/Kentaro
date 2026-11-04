"""Deterministic coverage for graph-safe lifecycle and decision extensions."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.design.company_context import (
    attach_context_marker,
    initialize_company_context,
    revalidate_company_context,
    unavailable_context,
)
from kentaro.design.engagement import build_engagement_state
from kentaro.design.portfolio import (
    add_object,
    add_relationship,
    create_design_portfolio,
    make_claim,
    migrate_portfolio,
    record_decision,
    validate_portfolio,
)
from kentaro.design.proposal import propose_design
from kentaro.design.reports import readiness


def _snapshot(version: str = "1") -> dict:
    return {
        "scope": "company-a", "retrieved_at": f"2026-11-04T0{version}:00:00+00:00",
        "source_label": "Live Maysano pilot API",
        "records": [{"id": "risk-context", "kind": "data_product", "title": "Customer risk assessment context", "version": version, "source_ref": "maysano:/products/risk-context"}],
        "relationships": [], "limitations": [],
    }


class DesignLifecycleTests(unittest.TestCase):
    def _connected_portfolio(self):
        context = initialize_company_context(_snapshot(), source_kind="maysano", session_mode="graph_connected")
        return propose_design("Improve customer risk assessment for a bank", company_context=context)["portfolio"]

    def test_graph_connected_initialization_records_only_safe_provenance(self):
        portfolio = self._connected_portfolio()
        marker = portfolio["claims"]["company_graph_context"]["value"]
        self.assertEqual(marker["session_mode"], "graph_connected")
        self.assertEqual(marker["verification_status"], "verified")
        self.assertEqual(marker["source_references"][0]["source_revision"], "1")
        self.assertNotIn("records", marker)

    def test_graph_connected_failure_is_not_an_unverified_auto_fallback(self):
        context = unavailable_context("timeout", session_mode="graph_connected")
        portfolio = propose_design("Improve customer risk assessment for a bank", company_context=context)["portfolio"]
        marker = portfolio["claims"]["company_graph_context"]["value"]
        self.assertEqual(marker["verification_status"], "source_unavailable")
        self.assertTrue(marker["requires_revalidation"])
        self.assertIn("Retry retrieval", marker["next_action"])

    def test_auto_and_local_context_remain_explicitly_unverified(self):
        auto = propose_design("Improve customer risk assessment for a bank", company_context=unavailable_context())["portfolio"]
        local = propose_design("Improve customer risk assessment for a bank", company_context=unavailable_context("local selected", session_mode="local"))["portfolio"]
        self.assertEqual(auto["claims"]["company_graph_context"]["value"]["verification_status"], "unverified")
        self.assertEqual(local["claims"]["company_graph_context"]["value"]["session_mode"], "local")

    def test_revalidation_marks_changed_source_and_affected_local_elements(self):
        portfolio = self._connected_portfolio()
        refreshed = initialize_company_context(_snapshot("2"), source_kind="maysano", session_mode="graph_connected")
        updated, result = revalidate_company_context(portfolio, refreshed)
        marker = updated["claims"]["company_graph_context"]["value"]
        self.assertTrue(result["changed"])
        self.assertEqual(marker["verification_status"], "stale")
        self.assertTrue(marker["affected_object_ids"])
        self.assertIn("company_graph_reconsideration_required", {item["field"] for item in readiness(updated)["findings"]})
        _, repeated = revalidate_company_context(updated, refreshed)
        self.assertTrue(repeated["changed"])

    def test_unavailable_revalidation_never_claims_current_graph(self):
        updated, result = revalidate_company_context(self._connected_portfolio(), unavailable_context("timeout", session_mode="graph_connected"))
        self.assertEqual(result["verification_status"], "source_unavailable")
        self.assertEqual(updated["claims"]["company_graph_context"]["value"]["verification_status"], "source_unavailable")

    def test_explicit_human_decision_is_append_only_and_supersedable(self):
        portfolio = create_design_portfolio("Decision test", "decision-test")
        first = record_decision(portfolio, "decision-1", subject="Initial scope", scope="Pilot", resolution="Start with permits", rationale="Highest delay", actor="Business owner")
        changed = record_decision(first, "decision-2", subject="Revised scope", scope="Pilot", resolution="Start with appeals", rationale="New evidence", actor="Business owner", supersedes="decision-1")
        self.assertEqual([item["id"] for item in changed["decisions"]], ["decision-1", "decision-2"])
        self.assertTrue(validate_portfolio(changed)["valid"])
        state = build_engagement_state(changed, portfolio_path=Path("/tmp/portfolio.json"))
        self.assertEqual(state["decision_register"]["events"][0]["effective_status"], "superseded")

    def test_recommendations_do_not_become_decisions_and_candidates_are_advisory(self):
        portfolio = self._connected_portfolio()
        findings = readiness(portfolio)["findings"]
        candidate = next(item for item in findings if item["field"] == "possible_data_product_reuse")
        self.assertEqual(portfolio["decisions"], [])
        self.assertEqual(candidate["category"], "decision_dependency")
        self.assertIn("advisory", candidate["explanation"])

    def test_unverified_dependency_is_a_readiness_finding(self):
        source = ("workshop", "v1", "input")
        claim = lambda value: make_claim(value, "proposed", *source)
        portfolio = create_design_portfolio("Dependency", "dependency")
        portfolio = add_object(portfolio, "case", "use_case", {"name": claim("Review"), "purpose": claim("Review"), "owner": claim("Team"), "lifecycle_status": claim("discovery")})
        portfolio = add_object(portfolio, "data", "data_product", {"name": claim("Context"), "purpose": claim("Context"), "owner": claim("Team"), "lifecycle_status": claim("discovery")})
        portfolio = add_relationship(portfolio, "needs", "case", "data", "use-case-requires-data-product")
        finding = next(item for item in readiness(portfolio)["findings"] if item["field"] == "unverified_dependency")
        self.assertEqual(finding["category"], "design_gap")

    def test_incomplete_design_stays_editable_and_v2_portfolios_load(self):
        legacy = {"schema_version": 2, "model": "DesignPortfolio", "portfolio_id": "old", "title": "Old", "revision": "v1", "assessment_stage": "discovery", "design_alternatives": [], "claims": {}, "objects": [], "relationships": []}
        migrated = migrate_portfolio(legacy)
        self.assertEqual(migrated["decisions"], [])
        self.assertTrue(validate_portfolio(migrated)["valid"])
        state = build_engagement_state(migrated, portfolio_path=Path("/tmp/old.json"))
        self.assertFalse(state["structural_completion"]["complete"])
        self.assertEqual(state["design_stages"][0]["stage"], "establish_context")


if __name__ == "__main__":
    unittest.main()
