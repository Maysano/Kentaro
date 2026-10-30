import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.cli import main
from kentaro.design.portfolio import load_portfolio, make_claim, save_portfolio, validate_portfolio
from kentaro.design.render import render_canvas
from kentaro.design.reports import analysis, readiness, stale_outputs


class DesignPortfolioTests(unittest.TestCase):
    def _run(self, args):
        self.assertEqual(main(args), 0)

    def test_generic_cli_creates_a_non_banking_many_to_many_design(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd(); os.chdir(root)
            try:
                portfolio = root / ".kentaro/workspace/design/government-service.json"
                self._run(["design", "init", "--title", "Permit Service Transformation", "--portfolio-id", "permit-service", "--output", str(portfolio)])
                base = ["--status", "proposed", "--source-id", "workshop", "--source-revision", "v1", "--derivation-input-hash", "government-case"]
                self._run(["design", "add-object", "--input", str(portfolio), "--id", "objective-speed", "--kind", "objective", "--name", "Faster permit decisions", "--purpose", "Reduce preventable permit delays", "--owner", "Service director", "--lifecycle-status", "proposed", *base])
                self._run(["design", "add-object", "--input", str(portfolio), "--id", "objective-access", "--kind", "objective", "--name", "More accessible service", "--purpose", "Improve applicant experience", "--owner", "Service director", "--lifecycle-status", "proposed", *base])
                self._run(["design", "add-object", "--input", str(portfolio), "--id", "usecase-submit", "--kind", "use_case", "--name", "Digital permit submission", "--purpose", "Let applicants submit complete requests", "--owner", "Permit operations", "--lifecycle-status", "proposed", "--ai-involvement", "none", *base])
                self._run(["design", "add-object", "--input", str(portfolio), "--id", "usecase-review", "--kind", "use_case", "--name", "Application completeness review", "--purpose", "Prioritise complete applications for review", "--owner", "Permit operations", "--lifecycle-status", "proposed", "--ai-involvement", "proposed", *base])
                self._run(["design", "add-object", "--input", str(portfolio), "--id", "ai-review", "--kind", "ai_product", "--name", "Application Review Assistant", "--purpose", "Suggest missing evidence", "--owner", "Digital services", "--lifecycle-status", "proposed", *base])
                self._run(["design", "add-object", "--input", str(portfolio), "--id", "data-permit", "--kind", "data_product", "--name", "Permit Application Record", "--purpose", "Reusable permit application context", "--owner", "Records service", "--lifecycle-status", "proposed", *base])
                relationships = [
                    ("speed-submit", "usecase-submit", "objective-speed", "use-case-supports-objective"),
                    ("access-submit", "usecase-submit", "objective-access", "use-case-supports-objective"),
                    ("speed-review", "usecase-review", "objective-speed", "use-case-supports-objective"),
                    ("review-ai", "usecase-review", "ai-review", "use-case-delivered-by-ai-product"),
                    ("submit-data", "usecase-submit", "data-permit", "use-case-requires-data-product"),
                    ("review-data", "usecase-review", "data-permit", "use-case-requires-data-product"),
                ]
                for relationship_id, from_id, to_id, kind in relationships:
                    self._run(["design", "add-relationship", "--input", str(portfolio), "--id", relationship_id, "--from-id", from_id, "--to-id", to_id, "--kind", kind])
                design = load_portfolio(portfolio)
                design["objects"][0]["claims"]["outcome"] = {"baseline": make_claim("unknown", "unknown", "workshop", "v1", "government-case", asserted_at="2026-10-25T00:00:00+00:00"), "target": make_claim("faster decisions", "proposed", "workshop", "v1", "government-case", asserted_at="2026-10-25T00:00:00+00:00")}
                design["design_alternatives"] = [
                    {"id": "conventional", "name": "Conventional automation", "object_ids": ["usecase-submit"], "shared_object_ids": ["data-permit"]},
                    {"id": "ai-assisted", "name": "AI-assisted case review", "object_ids": ["usecase-review", "ai-review"], "shared_object_ids": ["data-permit"]},
                ]
                save_portfolio(design, portfolio)
                self.assertTrue(validate_portfolio(load_portfolio(portfolio))["valid"])
                self.assertEqual(load_portfolio(portfolio)["objects"][2]["claims"]["ai_involvement"]["value"], "none")
                result = analysis(load_portfolio(portfolio))
                self.assertEqual(result["object_counts"]["objective"], 2)
                self.assertEqual(result["reuse_opportunities"][0]["object_id"], "data-permit")
                canvas = render_canvas(load_portfolio(portfolio))
                self.assertIn("<title>Faster permit decisions · Kentaro</title>", canvas)
                self.assertIn("Digital permit submission", canvas)
                self.assertIn("Business summary", canvas)
                self.assertIn("Needs information", canvas)
                self.assertIn("Supporting specifications and evidence", canvas)
                self.assertIn("Conventional automation", canvas)
                self.assertNotIn("Customer Risk", canvas)
                outputs = root / ".kentaro/workspace/design/outputs"
                self._run(["design", "report", "--input", str(portfolio), "--output-dir", str(outputs)])
                self.assertIn("Permit Service Transformation", (outputs / "executive-summary.md").read_text(encoding="utf-8"))
                manifest = json.loads((outputs / "manifest.json").read_text(encoding="utf-8"))
                changed = load_portfolio(portfolio); changed["revision"] = "draft-v2"; save_portfolio(changed, portfolio)
                self.assertTrue(all(item["stale"] for item in stale_outputs(changed, manifest)))
                self._run(["design", "report", "--input", str(portfolio), "--output-dir", str(outputs)])
                regenerated = json.loads((outputs / "manifest.json").read_text(encoding="utf-8"))
                self.assertFalse(any(item["stale"] for item in stale_outputs(changed, regenerated)))
                summary = (outputs / "executive-summary.md").read_text(encoding="utf-8")
                self.assertNotIn("Customer Risk", summary)
                self.assertNotIn("40%", summary)
            finally:
                os.chdir(previous)

    def test_blank_design_never_defaults_to_the_course_scenario(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd(); os.chdir(root)
            try:
                output = root / ".kentaro/workspace/design/blank.json"
                self.assertEqual(main(["design", "init", "--output", str(output)]), 2)
                self.assertFalse(output.exists())
                self._run(["design", "init", "--title", "Blank Design", "--portfolio-id", "blank", "--output", str(output)])
                self.assertEqual(load_portfolio(output)["objects"], [])
            finally:
                os.chdir(previous)

    def test_generic_migration_persists_legacy_masterclass_portfolio(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd(); os.chdir(root)
            try:
                legacy = json.loads((Path(__file__).parents[1] / "kentaro/scenarios/udemy_masterclass/customer-risk-intelligence.json").read_text(encoding="utf-8"))
                legacy_path = root / ".kentaro/workspace/design/legacy.json"
                legacy_path.parent.mkdir(parents=True); legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
                migrated = root / ".kentaro/workspace/design/migrated.json"
                self._run(["design", "migrate", "--input", str(legacy_path), "--output", str(migrated)])
                stored = load_portfolio(migrated)
                self.assertEqual(stored["model"], "DesignPortfolio")
                self.assertEqual(stored["scenario_id"], "customer-risk-intelligence")
            finally:
                os.chdir(previous)

    def test_invalid_nested_claim_is_rejected(self):
        portfolio = {"schema_version": 2, "model": "DesignPortfolio", "portfolio_id": "invalid", "title": "Invalid", "revision": "v1", "claims": {"outcome": {"baseline": "not-a-claim"}}, "objects": [], "relationships": []}
        self.assertFalse(validate_portfolio(portfolio)["valid"])

    def test_readiness_labels_unknowns_without_granting_authority(self):
        portfolio = {"schema_version": 2, "model": "DesignPortfolio", "portfolio_id": "sample", "title": "Sample", "revision": "v1", "claims": {}, "objects": [], "relationships": []}
        self.assertTrue(readiness(portfolio)["valid"])


if __name__ == "__main__":
    unittest.main()
