import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from kentaro.cli import main
from kentaro.design.handover import decision_context, export_handover, generate_handover, handover_status, inspect_handover, prepare_handover_review, validate_handover
from kentaro.design.portfolio import add_object, add_relationship, create_design_portfolio, make_claim, save_portfolio
from kentaro.design.specifications import structural_completion
from kentaro.scenarios.udemy_masterclass import starting_portfolio


class DesignHandoverTests(unittest.TestCase):
    def _complete_portfolio(self):
        claim = lambda value: make_claim(value, "proposed", "workshop", "v1", "complete-design", asserted_at="2026-10-25T00:00:00+00:00")
        metric = lambda name, target, unit, period: {"name": claim(name), "target": claim(target), "unit": claim(unit), "measurement_period": claim(period), "baseline": claim(0)}
        portfolio = create_design_portfolio("Complete service design", "complete-service")
        portfolio = add_object(portfolio, "objective", "objective", {"name": claim("Improve service"), "purpose": claim("Reduce avoidable delay"), "owner": claim("Service team"), "lifecycle_status": claim("discovery"), "outcome": claim("Faster service"), "business_kpi": metric("Cycle time", 2, "days", "monthly")})
        portfolio = add_object(portfolio, "use-case", "use_case", {"name": claim("Case review"), "purpose": claim("Review service cases"), "owner": claim("Service team"), "lifecycle_status": claim("discovery"), "consumer": claim("Case worker"), "expected_business_contribution": claim("Reduce review delay"), "data_capabilities": claim("Case status and evidence context")})
        portfolio = add_object(portfolio, "data-product", "data_product", {"name": claim("Case context"), "purpose": claim("Reusable case information"), "owner": claim("Data team"), "lifecycle_status": claim("discovery"), "consumer": claim("Case worker"), "product_boundary": claim("Case status and evidence only"), "data_capabilities": claim("Case status and evidence context"), "data_quality": claim("Completeness measured monthly"), "access_expectations": claim("Approved case workers"), "service_expectations": claim("Available in the working day"), "product_kpi": metric("Context completeness", 95, "percent", "monthly")})
        portfolio = add_relationship(portfolio, "supports", "use-case", "objective", "use-case-supports-objective")
        return add_relationship(portfolio, "needs-data", "use-case", "data-product", "use-case-requires-data-product")

    def test_banking_handover_preserves_claim_state_and_marks_contracts_unsupported(self):
        portfolio = starting_portfolio()
        with TemporaryDirectory() as directory:
            package = Path(directory) / "handover"
            generated = prepare_handover_review(portfolio, package)
            self.assertEqual(generated["manifest"]["status"], "draft")
            self.assertTrue(validate_handover(package)["valid"])
            self.assertIn("Suggested Design Review Package", (package / "README.md").read_text(encoding="utf-8"))
            self.assertIn("does not request or require approval", (package / "delivery-brief.md").read_text(encoding="utf-8"))
            context = json.loads((package / "decision-context.yaml").read_text(encoding="utf-8"))
            self.assertEqual(context["model"], "DecisionContext")
            self.assertEqual(context["business_context"]["use_cases"][0]["owner"]["status"], "assumed")
            self.assertTrue((package / "specifications" / "ai-products" / "ai-risk-assistant.json").is_file())
            self.assertFalse((package / "specifications" / "data-products").exists())
            self.assertEqual({item["status"] for item in generated["manifest"]["specification_status"]}, {"unsupported"})
            self.assertEqual(inspect_handover(package)["decision_context"]["ai_product_count"], 1)

    def test_generic_government_handover_is_not_a_course_specific_export_and_detects_staleness(self):
        claim = lambda value: make_claim(value, "proposed", "workshop", "v1", "government-case", asserted_at="2026-10-25T00:00:00+00:00")
        portfolio = create_design_portfolio("Permit Service Transformation", "permit-service")
        portfolio = add_object(portfolio, "objective", "objective", {"name": claim("Faster permit decisions"), "purpose": claim("Reduce preventable permit delays"), "owner": claim("Service director"), "lifecycle_status": claim("proposed")})
        portfolio = add_object(portfolio, "use-case", "use_case", {"name": claim("Permit completeness review"), "purpose": claim("Review application completeness"), "owner": claim("Permit operations"), "lifecycle_status": claim("proposed"), "ai_involvement": claim("none")})
        portfolio = add_relationship(portfolio, "supports", "use-case", "objective", "use-case-supports-objective")
        self.assertEqual(decision_context(portfolio)["source"]["portfolio_id"], "permit-service")
        with TemporaryDirectory() as directory:
            package = Path(directory) / "handover"
            generate_handover(portfolio, package)
            brief = (package / "delivery-brief.md").read_text(encoding="utf-8")
            self.assertIn("Permit Service Transformation", brief)
            self.assertNotIn("Customer Risk", brief)
            portfolio["revision"] = "draft-v2"
            status = handover_status(portfolio, package)
            self.assertTrue(status["stale"])
            self.assertTrue(status["valid"])

    def test_integrity_validation_detects_tampering(self):
        with TemporaryDirectory() as directory:
            package = Path(directory) / "handover"
            generate_handover(starting_portfolio(), package)
            summary = package / "executive-summary.md"
            summary.write_text(summary.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")
            validation = validate_handover(package)
            self.assertFalse(validation["valid"])
            self.assertEqual(validation["findings"][0]["code"], "artifact_digest_mismatch")

    def test_final_zip_requires_confirmation_and_is_inspectable(self):
        with TemporaryDirectory() as directory:
            package = Path(directory) / "handover.zip"
            with self.assertRaisesRegex(ValueError, "confirmation"):
                export_handover(starting_portfolio(), package, reviewer="Jarkko", confirmation="", acknowledge_all_open_decisions=True)
            with self.assertRaisesRegex(ValueError, "structural completion"):
                export_handover(starting_portfolio(), package, reviewer="Jarkko", confirmation="I confirm this reviewed handover is ready for its intended builder.", acknowledge_all_open_decisions=True)
            complete = self._complete_portfolio()
            self.assertTrue(structural_completion(complete)["structurally_complete"])
            exported = export_handover(complete, package, reviewer="Jarkko", confirmation="I confirm this reviewed handover is ready for its intended builder.", acknowledge_all_open_decisions=True)
            self.assertEqual(exported["manifest"]["status"], "reviewed")
            self.assertTrue(package.is_file())
            self.assertTrue(validate_handover(package)["valid"])
            self.assertEqual(inspect_handover(package)["package_status"], "reviewed")
            self.assertEqual({item["kind"] for item in exported["manifest"]["specification_status"]}, {"ODPS", "ODPC", "ODPG"})
            with zipfile.ZipFile(package) as archive:
                self.assertIn("specifications/odpc.yaml", archive.namelist())
                self.assertIn("specifications/odpg.yaml", archive.namelist())

    def test_cli_prepares_review_then_generates_confirmed_workspace_zip(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd()
            os.chdir(root)
            try:
                input_path = root / ".kentaro/workspace/design/portfolio.json"
                save_portfolio(self._complete_portfolio(), input_path)
                review_path = root / ".kentaro/workspace/design/review-v1"
                output_path = root / ".kentaro/workspace/design/handover-v1.zip"
                self.assertEqual(main(["design", "handover", "prepare-review", "--input", str(input_path), "--output", str(review_path)]), 0)
                self.assertEqual(main(["design", "handover", "generate", "--input", str(input_path), "--output", str(output_path), "--reviewer", "Jarkko", "--confirmation", "I confirm this handover.", "--acknowledge-open-decisions"]), 0)
                self.assertEqual(main(["design", "handover", "inspect", "--package", str(output_path)]), 0)
                self.assertEqual(main(["design", "handover", "status", "--input", str(input_path), "--package", str(output_path)]), 0)
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
