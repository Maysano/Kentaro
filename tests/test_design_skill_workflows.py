"""Independent deterministic operation coverage for the six reusable design skills."""
import unittest

from kentaro.design.portfolio import add_object, add_relationship, create_design_portfolio, make_claim, set_claim, validate_portfolio
from kentaro.design.reports import analysis, readiness


class DesignSkillWorkflowTests(unittest.TestCase):
    def _claims(self, name, purpose, *, owner="Unknown", status="unknown"):
        values = {"name": name, "purpose": purpose, "owner": owner, "lifecycle_status": "draft"}
        return {field: make_claim(value, status, "workshop", "v1", "incomplete-input", asserted_at="2026-10-25T00:00:00+00:00") for field, value in values.items()}

    def _portfolio(self):
        return create_design_portfolio("Independent design workflow", "independent")

    def test_objective_design_preserves_unknown_outcome_information(self):
        portfolio = add_object(self._portfolio(), "objective", "objective", self._claims("Faster service", "Reduce waiting"))
        portfolio = set_claim(portfolio, "kpi", {"baseline": make_claim("unknown", "unknown", "workshop", "v1", "incomplete-input", asserted_at="2026-10-25T00:00:00+00:00")}, object_id="objective")
        self.assertTrue(validate_portfolio(portfolio)["valid"])
        result = readiness(portfolio)
        self.assertEqual(result["assessment_stage"], "discovery")
        self.assertEqual(result["summary"]["by_category"]["implementation_blocker"], 0)
        self.assertGreater(result["summary"]["by_category"]["design_gap"], 0)
        self.assertTrue(all(item["finding_id"].startswith("finding:") for item in result["findings"]))

    def test_use_case_design_supports_non_ai_work(self):
        portfolio = add_object(self._portfolio(), "objective", "objective", self._claims("Accessible service", "Improve access"))
        use_case_claims = self._claims("Digital submission", "Let residents submit requests")
        use_case_claims["ai_involvement"] = make_claim("none", "user_confirmed", "workshop", "v1", "incomplete-input", asserted_at="2026-10-25T00:00:00+00:00")
        portfolio = add_object(portfolio, "submit", "use_case", use_case_claims)
        portfolio = add_relationship(portfolio, "submit-supports", "submit", "objective", "use-case-supports-objective")
        self.assertTrue(validate_portfolio(portfolio)["valid"])

    def test_ai_product_design_is_not_a_data_product(self):
        portfolio = add_object(self._portfolio(), "assistant", "ai_product", self._claims("Review Assistant", "Suggest missing evidence"))
        self.assertEqual(validate_portfolio(portfolio)["portfolio"]["objects"][0]["kind"], "ai_product")

    def test_data_product_design_is_independent_of_ai_product(self):
        portfolio = add_object(self._portfolio(), "applications", "data_product", self._claims("Application Status", "Reusable application context"))
        self.assertEqual(validate_portfolio(portfolio)["portfolio"]["objects"][0]["kind"], "data_product")

    def test_one_confirmed_consumer_can_qualify_a_candidate_data_product_without_reuse(self):
        portfolio = self._portfolio()
        confirmed = lambda value: make_claim(value, "user_confirmed", "workshop", "v1", "confirmed-input", asserted_at="2026-10-25T00:00:00+00:00")
        portfolio = add_object(portfolio, "case", "use_case", {"name": confirmed("Permit assessment"), "purpose": confirmed("Assess applications"), "owner": confirmed("Permit team"), "lifecycle_status": confirmed("proposed")})
        product = {"name": confirmed("Permit decision context"), "purpose": confirmed("Provide governed decision context"), "owner": make_claim("Unknown", "unknown", "workshop", "v1", "incomplete-input", asserted_at="2026-10-25T00:00:00+00:00"), "lifecycle_status": confirmed("proposed"), "product_boundary": confirmed("Permit eligibility and decision context"), "consumption_capability": confirmed("Decision-context retrieval"), "interface": confirmed("Read-only API")}
        portfolio = add_object(portfolio, "context", "data_product", product)
        portfolio = add_relationship(portfolio, "case-context", "case", "context", "use-case-requires-data-product")
        qualification = analysis(portfolio)["data_product_qualification"][0]
        self.assertTrue(qualification["candidate_data_product"])
        self.assertEqual(qualification["consumer_count"], 1)
        self.assertEqual(qualification["criteria"]["identified_consumer_demand"], "established")
        self.assertEqual(qualification["criteria"]["ownership_and_lifecycle_responsibility"], "unknown")

    def test_lifecycle_changes_unverified_rules_from_design_gap_to_blocker(self):
        portfolio = add_object(self._portfolio(), "review", "use_case", self._claims("Eligibility review", "Assess eligibility"))
        portfolio = set_claim(portfolio, "eligibility_rules", make_claim("draft rules", "proposed", "workshop", "v1", "incomplete-input", asserted_at="2026-10-25T00:00:00+00:00"), object_id="review")
        discovery = readiness(portfolio, assessment_stage="discovery")
        implementation = readiness(portfolio, assessment_stage="implementation")
        self.assertIn("design_gap", {item["category"] for item in discovery["findings"] if item["field"] == "eligibility_rules"})
        self.assertIn("implementation_blocker", {item["category"] for item in implementation["findings"] if item["field"] == "eligibility_rules"})

    def test_portfolio_analysis_finds_reused_data_product(self):
        portfolio = self._portfolio()
        for object_id, kind, name in (("objective", "objective", "Faster service"), ("first", "use_case", "Completeness check"), ("second", "use_case", "Demand analysis"), ("data", "data_product", "Service demand indicators")):
            portfolio = add_object(portfolio, object_id, kind, self._claims(name, "Local design"))
        portfolio = add_relationship(portfolio, "first-data", "first", "data", "use-case-requires-data-product")
        portfolio = add_relationship(portfolio, "second-data", "second", "data", "use-case-requires-data-product")
        self.assertEqual(analysis(portfolio)["reuse_opportunities"][0]["object_id"], "data")

    def test_readiness_reports_missing_evidence_without_approval(self):
        portfolio = add_object(self._portfolio(), "objective", "objective", self._claims("Faster service", "Reduce waiting"))
        result = readiness(portfolio)
        self.assertTrue(result["valid"])
        self.assertGreater(result["summary"]["by_category"]["design_gap"], 0)
        self.assertEqual(result["summary"]["by_category"]["implementation_blocker"], 0)
        self.assertNotIn("approved", str(result).lower())


if __name__ == "__main__":
    unittest.main()
