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
        self.assertEqual(sum(item["kind"] == "data_product" for item in result["portfolio"]["objects"]), 3)
        self.assertEqual(sum(item["kind"] == "ai_product" for item in result["portfolio"]["objects"]), 1)
        self.assertIn("Conventional workflow automation", render_canvas(result["portfolio"]))
        self.assertEqual(result["readiness"]["summary"]["by_category"]["implementation_blocker"], 0)

    def test_b_ambiguous_input_keeps_the_required_design_path_connected_without_inventing_a_domain(self):
        result = propose_design("We want to improve customer experience and use AI.")
        self.assertEqual(result["frame"], "needs_context")
        self.assertEqual(result["measurement"]["clarification_questions"], 1)
        self.assertTrue(result["measurement"]["valid_connected_portfolio"])
        self.assertEqual({item["kind"] for item in result["portfolio"]["objects"]}, {"objective", "use_case", "data_product"})
        self.assertIn("ai_product_opportunity", result["portfolio"]["claims"])
        self.assertEqual(result["measurement"]["unsupported_factual_claims"], 0)

    def test_customer_risk_input_proposes_three_domain_oriented_information_products_and_a_human_controlled_ai_option(self):
        result = propose_design("Our bank's customer risk assessments take too long. Help me improve this process.")
        objects = result["portfolio"]["objects"]
        by_id = {item["id"]: item for item in objects}
        ai_product = by_id["ai-risk-preparation-assistant"]

        self.assertEqual(result["frame"], "customer_risk_assessment")
        self.assertTrue(validate_portfolio(result["portfolio"])["valid"])
        self.assertEqual(sum(item["kind"] == "data_product" for item in objects), 3)
        self.assertEqual(sum(item["kind"] == "ai_product" for item in objects), 1)
        data_products = [item for item in objects if item["kind"] == "data_product"]
        self.assertTrue(all(item["claims"]["domain_scope"]["status"] == "proposed" for item in data_products))
        self.assertIn("Customer risk-assessment case context", [item["claims"]["name"]["value"] for item in data_products])
        self.assertNotIn("Risk-assessment case worklist", [item["claims"]["name"]["value"] for item in data_products])
        self.assertEqual(ai_product["claims"]["human_oversight"]["status"], "proposed")
        self.assertIn("No risk scoring", ai_product["claims"]["prohibited_actions"]["value"])
        self.assertIn("Human-in-the-loop AI preparation support", [item["name"] for item in result["portfolio"]["design_alternatives"]])

    def test_canvas_title_prefers_a_confirmed_business_target_over_generic_portfolio_title(self):
        result = propose_design("Our bank's customer risk assessments take too long. Help me improve this process.")
        objective = next(item for item in result["portfolio"]["objects"] if item["kind"] == "objective")
        objective["claims"]["outcome"]["value"] = "Reduce customer risk-assessment turnaround time to under 24 hours"
        objective["claims"]["outcome"]["status"] = "user_confirmed"

        canvas = render_canvas(result["portfolio"])

        self.assertIn("<title>Reduce customer risk-assessment turnaround time to under 24 hours · Kentaro</title>", canvas)
        self.assertIn('"title": "Reduce customer risk-assessment turnaround time to under 24 hours"', canvas)
        self.assertNotIn("<h1>Business improvement framing — provisional design</h1>", canvas)

    def test_canvas_leads_with_business_decisions_and_keeps_specs_secondary(self):
        canvas = render_canvas(propose_design("Our finance team spends too much time reconciling monthly reports from different systems.")["portfolio"])

        self.assertIn("Business design summary", canvas)
        self.assertIn("Business target", canvas)
        self.assertIn("Supporting specifications held separately", canvas)
        self.assertIn("Business evidence still needed", canvas)
        self.assertNotIn("Input hash", canvas)
        self.assertNotIn("Declared objects", canvas)

    def test_canvas_is_a_self_contained_business_review_workspace(self):
        canvas = render_canvas(propose_design("Our bank's customer risk assessments take too long. Help me improve this process.")["portfolio"])

        self.assertIn("https://cal.com/maysanoplatform/30min", canvas)
        self.assertIn('data:image/png;base64,', canvas)
        self.assertIn('class="brand-symbol"', canvas)
        self.assertIn('class="brand-wordmark"', canvas)
        self.assertNotIn('class="brand-mark"', canvas)
        self.assertNotIn('class="kentaro-word"', canvas)
        self.assertIn("Book a Demo", canvas)
        self.assertIn("Business design canvas", canvas)
        self.assertIn("Business objectives", canvas)
        self.assertIn("Business use cases", canvas)
        self.assertIn("Reusable products", canvas)
        self.assertIn("Expected outcomes", canvas)
        self.assertIn("View as list", canvas)
        self.assertIn("Fit diagram to view", canvas)
        self.assertIn("Reset diagram zoom and pan", canvas)
        self.assertIn("Focus view", canvas)
        self.assertIn("selected-detail", canvas)
        self.assertIn("Supporting specifications, including generated ODPS-family artifacts", canvas)
        self.assertIn("does not establish access, approval, compliance, or production readiness", canvas)
        self.assertNotIn("<link rel=\"stylesheet\"", canvas)
        self.assertNotIn('role="tablist"', canvas)

    def test_c_finance_input_proposes_smaller_information_products_and_a_human_controlled_ai_option(self):
        result = propose_design("Our finance team spends too much time reconciling monthly reports from different systems. We want faster reporting and fewer discrepancies.")
        kinds = [item["kind"] for item in result["portfolio"]["objects"]]
        self.assertEqual(result["frame"], "finance_reconciliation")
        self.assertIn("objective", kinds)
        self.assertGreaterEqual(kinds.count("use_case"), 2)
        self.assertEqual(kinds.count("data_product"), 2)
        self.assertEqual(kinds.count("ai_product"), 1)
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
                suggested_review = output / "proposal" / "suggested-review"
                self.assertTrue((suggested_review / "README.md").exists())
                self.assertIn("Suggested Design Review Package", (suggested_review / "README.md").read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
