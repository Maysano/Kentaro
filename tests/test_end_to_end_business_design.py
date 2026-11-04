"""End-to-end contract for the reusable synthetic Business Owner journey."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from kentaro.design.company_context import (
    acknowledge_graph_reconsideration,
    initialize_company_context,
    revalidate_company_context,
)
from kentaro.design.engagement import build_engagement_state
from kentaro.design.handover import export_handover, handover_status, validate_handover
from kentaro.design.portfolio import make_claim, record_decision, set_claim, validate_portfolio
from kentaro.design.proposal import propose_design
from kentaro.design.reports import readiness
from kentaro.design.specifications import structural_completion


CASE_ROOT = Path(__file__).parent / "fixtures" / "business_design_validation"
CASE_PATH = CASE_ROOT / "customer-risk-assessment.json"
REFERENCE_PORTFOLIO = CASE_ROOT / "expected-design-portfolio.json"
REFERENCE_CANVAS = CASE_ROOT / "expected-design-portfolio.html"
REFERENCE_HANDOVER = CASE_ROOT / "expected-handover.zip"


def load_case() -> dict:
    return json.loads(CASE_PATH.read_text(encoding="utf-8"))


def _claim(value: object) -> dict:
    return make_claim(value, "user_confirmed", "business-owner:customer-risk-case", "v1", "customer-risk-e2e-v1", asserted_at="2026-11-04T10:00:00+00:00")


def _metric(name: str, target: int, unit: str) -> dict:
    return {"name": _claim(name), "target": _claim(target), "unit": _claim(unit), "measurement_period": _claim("quarterly"), "baseline": _claim(10)}


def complete_portfolio(portfolio: dict) -> dict:
    """Apply only the explicit information from the fixture's completion turn."""
    result = deepcopy(portfolio)
    for item in result["objects"]:
        if item["kind"] == "objective":
            result = set_claim(result, "outcome", _claim("Reduce median customer risk-assessment turnaround by 30 percent within one quarter"), object_id=item["id"])
            result = set_claim(result, "business_kpi", _metric("Median assessment turnaround reduction", 30, "percent"), object_id=item["id"])
        elif item["kind"] == "use_case":
            result = set_claim(result, "consumer", _claim("Risk assessors"), object_id=item["id"])
            result = set_claim(result, "expected_business_contribution", _claim("Reduce median assessment turnaround while risk assessors retain every case decision"), object_id=item["id"])
            result = set_claim(result, "data_capabilities", _claim("Traceable customer profile, due-diligence evidence, and risk-case context"), object_id=item["id"])
        elif item["kind"] == "data_product":
            result = set_claim(result, "consumer", _claim("Risk assessors"), object_id=item["id"])
            result = set_claim(result, "data_capabilities", _claim("Read-only, traceable information needed for customer risk assessment"), object_id=item["id"])
            result = set_claim(result, "data_quality", _claim("Completeness measured for the quarterly pilot"), object_id=item["id"])
            result = set_claim(result, "access_expectations", _claim("Authorised Risk Operations users"), object_id=item["id"])
            result = set_claim(result, "service_expectations", _claim("Available during the risk-assessment working day"), object_id=item["id"])
            result = set_claim(result, "product_kpi", _metric("Information completeness", 95, "percent"), object_id=item["id"])
    return result


class EndToEndBusinessDesignTests(unittest.TestCase):
    def _start(self) -> tuple[dict, dict]:
        case = load_case()
        start = case["turns"][0]
        context = initialize_company_context(case["graph_snapshots"]["initial"], source_kind="maysano", session_mode="graph_connected")
        proposal = propose_design(start["prompt"], company_context=context)
        return case, proposal

    def test_customer_risk_business_owner_journey(self):
        case, proposal = self._start()
        portfolio = proposal["portfolio"]

        self.assertEqual(proposal["company_graph"]["context"]["verification_status"], "verified")
        self.assertEqual({match["kind"] for match in proposal["company_graph"]["findings"]["matches"]}, {"objective", "use_case", "data_product"})
        self.assertGreaterEqual(len(portfolio["design_alternatives"]), 2)
        self.assertFalse(structural_completion(portfolio)["structurally_complete"])
        self.assertIn("possible_data_product_reuse", {item["field"] for item in readiness(portfolio)["findings"]})
        self.assertIn("unverified_dependency", {item["field"] for item in readiness(portfolio)["findings"]})

        with TemporaryDirectory() as directory:
            blocked = Path(directory) / "blocked.zip"
            with self.assertRaisesRegex(ValueError, "structural completion"):
                export_handover(portfolio, blocked, reviewer="Business Owner", confirmation="I confirm this handover.", acknowledge_all_open_decisions=True)

        portfolio = complete_portfolio(portfolio)
        portfolio = record_decision(
            portfolio, "decision-risk-ai-pilot", subject="Pilot approach", scope="Customer risk assessment", alternatives=[item["name"] for item in portfolio["design_alternatives"]],
            resolution="Use human-in-the-loop AI preparation support", rationale="Risk assessors retain every case decision", actor="Business Owner", related_object_ids=["ai-risk-preparation-assistant"],
        )
        portfolio = record_decision(
            portfolio, "decision-risk-information-first", subject="Pilot approach", scope="Customer risk assessment", alternatives=[item["name"] for item in portfolio["design_alternatives"]],
            resolution="Start with information products and workflow improvement", rationale="Defer AI until evidence coverage improves", actor="Business Owner", related_object_ids=["data-risk-assessment-case-context"], supersedes="decision-risk-ai-pilot",
        )
        self.assertTrue(validate_portfolio(portfolio)["valid"])
        self.assertTrue(structural_completion(portfolio)["structurally_complete"])
        state = build_engagement_state(portfolio, portfolio_path=Path("/tmp/customer-risk-e2e.json"))
        self.assertEqual([stage["stage"] for stage in state["design_stages"]], ["establish_context", "define_business_intent", "assess_existing_capabilities", "develop_alternatives", "formalize_design", "validate_and_decide", "prepare_handover"])
        self.assertEqual(state["decision_register"]["events"][0]["effective_status"], "superseded")

        revised = initialize_company_context(case["graph_snapshots"]["revised"], source_kind="maysano", session_mode="graph_connected")
        portfolio, revalidation = revalidate_company_context(portfolio, revised)
        self.assertTrue(revalidation["changed"])
        self.assertEqual(revalidation["verification_status"], "stale")
        self.assertTrue(revalidation["affected_object_ids"])
        portfolio = record_decision(
            portfolio, "decision-graph-reconsidered", subject="Changed company context", scope="Customer risk-assessment pilot", alternatives=["Proceed unchanged", "Revisit data-product reuse"],
            resolution="Proceed with the information-product pilot after reviewing updated case-context evidence", rationale="The updated graph relationship does not change the human decision boundary", actor="Business Owner", related_object_ids=["data-risk-assessment-case-context"], evidence_references=["maysano:/products/product-risk-case"],
        )
        self.assertTrue(acknowledge_graph_reconsideration(portfolio, portfolio["decisions"][-1]))

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "customer-risk-handover.zip"
            with self.assertRaisesRegex(ValueError, "confirmation"):
                export_handover(portfolio, destination, reviewer="Business Owner", confirmation="", acknowledge_all_open_decisions=True)
            exported = export_handover(portfolio, destination, reviewer="Business Owner", confirmation="I have reviewed this completed design and its unresolved issues.", acknowledge_all_open_decisions=True)
            self.assertEqual(exported["manifest"]["status"], "reviewed")
            self.assertTrue(validate_handover(destination)["valid"])
            self.assertEqual({item["kind"] for item in exported["manifest"]["specification_status"]}, {"ODPS", "ODPC", "ODPG"})

    def test_packaged_reference_result_is_inspectable_and_current(self):
        case = load_case()
        portfolio = json.loads(REFERENCE_PORTFOLIO.read_text(encoding="utf-8"))
        self.assertTrue(validate_portfolio(portfolio)["valid"])
        canvas = REFERENCE_CANVAS.read_text(encoding="utf-8")
        self.assertIn(
            "Reduce median customer risk-assessment turnaround by 30 percent within one quarter",
            canvas,
        )
        self.assertIn("Business design canvas", canvas)
        self.assertTrue(validate_handover(REFERENCE_HANDOVER)["valid"])
        self.assertFalse(handover_status(portfolio, REFERENCE_HANDOVER)["stale"])
        with zipfile.ZipFile(REFERENCE_HANDOVER) as archive:
            self.assertIn("portfolio/design-portfolio.json", archive.namelist())
            packaged = json.loads(archive.read("portfolio/design-portfolio.json"))
        self.assertEqual(packaged["portfolio_id"], "customer-risk-assessment-proposal")
        self.assertEqual(packaged["decisions"][-1]["id"], "decision-graph-reconsidered")
        self.assertEqual(case["id"], "customer-risk-assessment-v1")

    def test_fixture_prompts_remain_ordinary_business_owner_language(self):
        case = load_case()
        self.assertEqual(case["schema_version"], 1)
        self.assertEqual(len(case["turns"]), 10)
        self.assertTrue(all(turn["actor"] == "Business Owner" for turn in case["turns"]))
        self.assertTrue(all("kentaro " not in turn["prompt"].lower() for turn in case["turns"]))


if __name__ == "__main__":
    unittest.main()
