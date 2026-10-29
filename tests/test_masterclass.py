import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.cli import main
from kentaro.masterclass.portfolio import create_case_portfolio, validate_portfolio
from kentaro.masterclass.render import render_canvas
from kentaro.masterclass.reports import readiness, stale_outputs, unresolved_decisions, validate_odps


class MasterclassTests(unittest.TestCase):
    def test_synthetic_portfolio_is_valid_and_separates_ai_and_data_products(self):
        portfolio = create_case_portfolio()
        result = validate_portfolio(portfolio)
        self.assertTrue(result["valid"])
        kinds = {item["kind"] for item in portfolio["objects"]}
        self.assertIn("ai_product", kinds)
        self.assertIn("data_product", kinds)
        self.assertIn("use-case-supports-objective", {edge["kind"] for edge in portfolio["relationships"]})

    def test_invalid_relationship_and_claim_are_rejected(self):
        portfolio = create_case_portfolio()
        portfolio["objects"][0]["claims"]["owner"].pop("source_revision")
        portfolio["relationships"][0]["from_id"] = "objective-risk-time"
        codes = {item["code"] for item in validate_portfolio(portfolio)["findings"]}
        self.assertIn("invalid_claims", codes)
        self.assertIn("invalid_relationship_endpoints", codes)

    def test_canvas_escapes_claims_and_reports_unknowns(self):
        portfolio = create_case_portfolio()
        portfolio["objects"][0]["claims"]["name"]["value"] = "<script>alert(1)</script>"
        canvas = render_canvas(portfolio)
        self.assertIn("\\u003cscript\\u003e", canvas)
        self.assertNotIn("<script>alert", canvas)
        self.assertIn("data-node-id", canvas)
        self.assertIn("function select", canvas)
        report = readiness(portfolio)
        self.assertGreater(report["summary"]["by_category"]["design_gap"], 0)
        self.assertEqual(report["summary"]["by_category"]["implementation_blocker"], 0)
        self.assertIn("Unresolved Decisions", unresolved_decisions(portfolio, report))

    def test_cli_is_local_and_detects_stale_outputs(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd(); os.chdir(root)
            try:
                self.assertEqual(main(["masterclass", "init"]), 0)
                portfolio = root / ".kentaro/workspace/masterclass/customer-risk-intelligence/portfolio.json"
                self.assertTrue((portfolio.parent / "customer-profile.odps.yaml").is_file())
                self.assertTrue((portfolio.parent / "customer-profile-repair.odps.yaml").is_file())
                self.assertEqual(main(["masterclass", "validate", "--input", str(portfolio)]), 0)
                output = root / ".kentaro/workspace/masterclass/customer-risk-intelligence/outputs"
                self.assertEqual(main(["masterclass", "report", "--input", str(portfolio), "--output-dir", str(output)]), 0)
                manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["dependency_manifest"][0]["kind"], "design_portfolio")
                self.assertTrue((output / "unresolved-decisions.md").exists())
                changed = json.loads(portfolio.read_text(encoding="utf-8")); changed["revision"] = "changed"; portfolio.write_text(json.dumps(changed), encoding="utf-8")
                self.assertTrue(all(item["stale"] for item in stale_outputs(changed, manifest)))
            finally:
                os.chdir(previous)

    def test_pinned_sdk_validates_course_fixture(self):
        fixture = Path(__file__).parents[1] / "kentaro/scenarios/udemy_masterclass/customer-profile.odps.yaml"
        result = validate_odps(fixture)
        self.assertTrue(result["valid"])
        self.assertEqual(result["sdk_version"], "0.4.0")
        repair = Path(__file__).parents[1] / "kentaro/scenarios/udemy_masterclass/customer-profile-repair.odps.yaml"
        self.assertFalse(validate_odps(repair)["valid"])

    def test_masterclass_odps_default_uses_the_packaged_course_fixture(self):
        self.assertEqual(main(["masterclass", "validate-odps"]), 0)

    def test_cli_rejects_course_outputs_outside_ignored_workspace(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd(); os.chdir(root)
            try:
                outside = root / "portfolio.json"
                self.assertEqual(main(["masterclass", "init", "--output", str(outside)]), 2)
                self.assertFalse(outside.exists())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
