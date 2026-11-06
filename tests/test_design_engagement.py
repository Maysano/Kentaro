"""Persistent engagement-state coverage."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.design.engagement import build_engagement_state, load_engagement_state, update_engagement_state
from kentaro.design.portfolio import add_object, add_relationship, create_design_portfolio, make_claim
from kentaro.design.specifications import structural_completion


class DesignEngagementTests(unittest.TestCase):
    def _complete_portfolio_with_proposed_ai_product(self):
        source = ("workshop", "v1", "input")
        claim = lambda value: make_claim(value, "proposed", *source, asserted_at="2026-10-28T00:00:00+00:00")
        metric = lambda name, target, unit, period: {"name": claim(name), "target": claim(target), "unit": claim(unit), "measurement_period": claim(period)}
        portfolio = create_design_portfolio("Service design", "service-design")
        portfolio = add_object(portfolio, "objective", "objective", {"name": claim("Improve service"), "purpose": claim("Reduce delay"), "owner": claim("Service team"), "lifecycle_status": claim("discovery"), "outcome": claim("Faster service"), "business_kpi": metric("Cycle time", 2, "days", "monthly")})
        portfolio = add_object(portfolio, "use-case", "use_case", {"name": claim("Case review"), "purpose": claim("Review cases"), "owner": claim("Service team"), "lifecycle_status": claim("discovery"), "consumer": claim("Case worker"), "expected_business_contribution": claim("Reduce review delay"), "data_capabilities": claim("Case context")})
        portfolio = add_object(portfolio, "data-product", "data_product", {"name": claim("Case context"), "purpose": claim("Reusable case information"), "owner": claim("Data team"), "lifecycle_status": claim("discovery"), "consumer": claim("Case worker"), "product_boundary": claim("Case status"), "data_capabilities": claim("Case context"), "data_quality": claim("Completeness"), "access_expectations": claim("Case workers"), "service_expectations": claim("Business day"), "product_kpi": metric("Completeness", 95, "percent", "monthly")})
        portfolio = add_object(portfolio, "ai-review", "ai_product", {"name": claim("Review assistant"), "purpose": claim("Prepares evidence for a human reviewer"), "owner": claim("Service team"), "lifecycle_status": claim("discovery")})
        portfolio = add_relationship(portfolio, "supports", "use-case", "objective", "use-case-supports-objective")
        portfolio = add_relationship(portfolio, "uses", "use-case", "data-product", "use-case-requires-data-product")
        return add_relationship(portfolio, "delivered-by", "use-case", "ai-review", "use-case-delivered-by-ai-product")

    def test_engagement_requests_missing_odpc_ai_product_details_without_blocking_structure(self):
        portfolio = self._complete_portfolio_with_proposed_ai_product()

        state = build_engagement_state(portfolio, portfolio_path=Path("/tmp/portfolio.json"))

        topic = next(item for item in state["topics_to_resolve"] if item["topic"] == "ODPC AI-product definition")
        self.assertEqual(topic["items"][0]["code"], "missing_ai_product_odpc_identity")
        self.assertIn("product ID", state["next_unresolved_requirement"])
        self.assertTrue(structural_completion(portfolio)["structurally_complete"])

    def test_state_is_derived_from_portfolio_and_exposes_next_requirement(self):
        source = ("workshop", "v1", "input")
        claim = lambda value: make_claim(value, "proposed", *source, asserted_at="2026-10-28T00:00:00+00:00")
        portfolio = create_design_portfolio("Service design", "service-design")
        portfolio = add_object(portfolio, "objective", "objective", {"name": claim("Improve service"), "purpose": claim("Reduce delay"), "owner": claim("Service team"), "lifecycle_status": claim("discovery")})
        portfolio = add_object(portfolio, "use-case", "use_case", {"name": claim("Case review"), "purpose": claim("Review cases"), "owner": claim("Service team"), "lifecycle_status": claim("discovery")})
        portfolio = add_object(portfolio, "data-product", "data_product", {"name": claim("Case context"), "purpose": claim("Provide case information"), "owner": claim("Data team"), "lifecycle_status": claim("discovery")})
        portfolio = add_relationship(portfolio, "supports", "use-case", "objective", "use-case-supports-objective")
        portfolio = add_relationship(portfolio, "uses", "use-case", "data-product", "use-case-requires-data-product")
        with TemporaryDirectory() as directory:
            source_path = Path(directory) / "portfolio.json"
            state_path, state = update_engagement_state(portfolio, source_path)
            self.assertTrue(state_path.is_file())
            self.assertFalse(state["structural_completion"]["complete"])
            self.assertEqual(state["required_deliverables"]["final_handover_package"]["status"], "blocked_by_missing_requirements")
            self.assertTrue(state["next_unresolved_requirement"].startswith("What KPI"))
            self.assertGreater(state["claim_summary"]["proposed"], 0)
            self.assertEqual(load_engagement_state(state_path)["authoritative_source"]["portfolio_id"], "service-design")
            _, reevaluated = update_engagement_state(portfolio, source_path)
            self.assertFalse(reevaluated["evaluation"]["affected_elements"]["portfolio_changed"])
            self.assertEqual(reevaluated["evaluation"]["affected_elements"]["object_ids"], [])
            self.assertIn("Business KPI targets", [item["topic"] for item in reevaluated["topics_to_resolve"]])


if __name__ == "__main__":
    unittest.main()
