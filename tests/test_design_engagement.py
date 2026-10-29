"""Persistent engagement-state coverage."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.design.engagement import load_engagement_state, update_engagement_state
from kentaro.design.portfolio import add_object, add_relationship, create_design_portfolio, make_claim


class DesignEngagementTests(unittest.TestCase):
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
