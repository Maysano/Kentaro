"""Acceptance coverage for bounded, minimal-input business-design proposals."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.cli import main
from kentaro.design.portfolio import validate_portfolio
from kentaro.design.proposal import propose_design
from kentaro.design.render import render_canvas


class MinimalInputProposalTests(unittest.TestCase):
    def test_a_permit_input_creates_a_connected_provisional_design(self):
        result = propose_design("We are a government organization. Our permit applications take too long because several departments are involved. We want to improve the service using data and AI where appropriate.")
        self.assertEqual(result["frame"], "permit_service")
        self.assertTrue(validate_portfolio(result["portfolio"])["valid"])
        self.assertTrue(result["measurement"]["valid_connected_portfolio"])
        self.assertLessEqual(result["measurement"]["clarification_questions"], 3)
        self.assertEqual(result["measurement"]["unsupported_factual_claims"], 0)
        self.assertGreaterEqual(result["measurement"]["substantive_business_concepts"], 6)
        self.assertGreaterEqual(result["measurement"]["meaningful_alternatives"], 2)
        self.assertIn("Conventional workflow automation", render_canvas(result["portfolio"]))
        self.assertEqual(result["readiness"]["summary"]["by_category"]["implementation_blocker"], 0)

    def test_b_ambiguous_input_keeps_the_required_design_path_connected_without_inventing_a_domain(self):
        result = propose_design("We want to improve customer experience and use AI.")
        self.assertEqual(result["frame"], "needs_context")
        self.assertEqual(result["measurement"]["clarification_questions"], 1)
        self.assertTrue(result["measurement"]["valid_connected_portfolio"])
        self.assertEqual({item["kind"] for item in result["portfolio"]["objects"]}, {"objective", "use_case", "data_product"})
        self.assertEqual(result["measurement"]["unsupported_factual_claims"], 0)

    def test_c_finance_input_prioritises_data_quality_and_automation_before_ai(self):
        result = propose_design("Our finance team spends too much time reconciling monthly reports from different systems. We want faster reporting and fewer discrepancies.")
        kinds = [item["kind"] for item in result["portfolio"]["objects"]]
        self.assertEqual(result["frame"], "finance_reconciliation")
        self.assertIn("objective", kinds)
        self.assertGreaterEqual(kinds.count("use_case"), 2)
        self.assertIn("data_product", kinds)
        self.assertNotIn("ai_product", kinds)
        self.assertEqual(result["measurement"]["unsupported_factual_claims"], 0)

    def test_cli_writes_one_portfolio_and_all_derived_outputs_from_minimal_input(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                result = main([
                    "design", "propose",
                    "--business-input", "Our finance team spends too much time reconciling monthly reports from different systems. We want faster reporting and fewer discrepancies.",
                    "--output", ".kentaro/workspace/proposal/portfolio.json",
                ])
                output = Path(".kentaro/workspace/proposal")
                self.assertEqual(result, 0)
                self.assertTrue((output / "portfolio.json").exists())
                self.assertTrue((output / "engagement-state.json").exists())
                self.assertTrue((output / "proposal" / "canvas.html").exists())
                self.assertTrue((output / "proposal" / "executive-summary.md").exists())
                self.assertTrue((output / "proposal" / "readiness-report.json").exists())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
