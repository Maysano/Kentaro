"""Company-graph initialization is shared by local design commands and agent hosts."""
from __future__ import annotations

import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from kentaro.cli import main
from kentaro.design.company_context import (
    attach_context_marker,
    initialize_company_context,
    match_business_intent,
    unavailable_context,
)
from kentaro.design.portfolio import create_design_portfolio, validate_portfolio
from kentaro.design.portfolio import save_portfolio
from kentaro.design.proposal import propose_design
from kentaro.design.render import render_canvas


class CompanyContextTests(unittest.TestCase):
    def test_configured_connection_initializes_context_automatically_for_proposal(self):
        snapshot = {
            "scope": "company-a", "retrieved_at": "2026-11-03T00:00:00+00:00",
            "source_label": "Live Maysano pilot API", "records": [], "relationships": [], "limitations": [],
        }
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                workspace = Path(directory) / ".kentaro" / "workspace"
                workspace.mkdir(parents=True)
                (workspace / "maysano.toml").write_text(
                    "profile = 'live'\nread_only = true\nscope = 'company-a'\n[model]\nmode = 'local'\ncache = false\n",
                    encoding="utf-8",
                )
                (workspace / "maysano.env").write_text("API_BASE_URL=https://example.test/api\nAPI_KEY=not-a-real-key\n", encoding="utf-8")
                output = io.StringIO()
                with patch("kentaro.cli._source_context", return_value=(snapshot, "local")) as read, redirect_stdout(output):
                    self.assertEqual(main(["design", "propose", "--business-input", "Improve customer risk assessment", "--output", ".kentaro/workspace/design/risk.json"]), 0)
                result = json.loads(output.getvalue())
                self.assertTrue(read.called)
                self.assertTrue(result["maysano_connection"])
                self.assertEqual(result["company_graph"]["context"]["source_kind"], "maysano")
            finally:
                os.chdir(previous)

    def test_successful_retrieval_exposes_existing_candidates_without_making_them_local_objects(self):
        context = initialize_company_context({
            "scope": "company-a",
            "retrieved_at": "2026-11-03T00:00:00+00:00",
            "source_label": "Live Maysano pilot API",
            "records": [
                {"id": "existing-risk", "kind": "data_product", "title": "Customer risk assessment context", "source_ref": "maysano:/products/existing-risk"},
            ],
            "relationships": [],
            "limitations": [],
        }, source_kind="maysano")
        findings = match_business_intent(context, "Improve customer risk assessment")
        portfolio = attach_context_marker(create_design_portfolio("Risk", "risk"), context, findings)

        self.assertEqual(findings["matches"][0]["id"], "existing-risk")
        self.assertIn("Evaluate the matched existing data product", findings["recommendation"])
        self.assertEqual(portfolio["objects"], [])
        self.assertEqual(portfolio["claims"]["company_graph_context"]["value"]["match_count"], 1)
        self.assertNotIn("existing-risk", str(portfolio["claims"]["company_graph_context"]["value"]))
        self.assertTrue(validate_portfolio(portfolio)["valid"])
        canvas = render_canvas(portfolio)
        self.assertIn("Company graph", canvas)
        self.assertIn("Read-only company-context provenance and coverage", canvas)
        self.assertIn("graph-kpis", canvas)
        self.assertIn("Objects retrieved", canvas)
        self.assertIn("Reuse candidates", canvas)
        self.assertIn("full company graph is not embedded", canvas)

    def test_empty_graph_is_available_context_not_an_error(self):
        context = initialize_company_context({"scope": "company-a", "retrieved_at": "now", "records": [], "relationships": [], "limitations": []}, source_kind="maysano")
        findings = match_business_intent(context, "Improve customer risk assessment")
        self.assertEqual(findings["status"], "available")
        self.assertEqual(findings["matches"], [])
        self.assertIn("does not prove", findings["recommendation"])

    def test_connection_failure_keeps_design_explicitly_unverified(self):
        findings = match_business_intent(unavailable_context("Maysano company graph is unavailable: timeout"), "Improve risk assessment")
        self.assertEqual(findings["status"], "unverified")
        self.assertIn("do not claim graph-verified", findings["recommendation"])

    def test_connected_marker_requires_a_fresh_read_before_final_handover(self):
        context = initialize_company_context({"scope": "company-a", "retrieved_at": "2026-11-03T00:00:00+00:00", "records": [], "relationships": [], "limitations": []}, source_kind="maysano")
        marker = attach_context_marker(create_design_portfolio("Risk", "risk"), context, match_business_intent(context, "risk"))["claims"]["company_graph_context"]["value"]
        self.assertEqual(marker["source_kind"], "maysano")
        self.assertIn("retrieved_at", marker)
        # The CLI always re-reads this source before final export instead of
        # treating this timestamp as fresh enough.

    def test_connected_final_handover_is_gated_when_a_fresh_read_is_unavailable(self):
        context = initialize_company_context({"scope": "company-a", "retrieved_at": "2026-11-03T00:00:00+00:00", "records": [], "relationships": [], "limitations": []}, source_kind="maysano")
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                portfolio_path = Path(".kentaro/workspace/design/risk.json")
                save_portfolio(propose_design("Improve risk assessment", company_context=context)["portfolio"], portfolio_path)
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    code = main([
                        "design", "handover", "generate", "--input", str(portfolio_path),
                        "--output", ".kentaro/workspace/design/risk.zip", "--reviewer", "Reviewer",
                        "--confirmation", "Reviewed", "--acknowledge-open-decisions",
                    ])
                self.assertEqual(code, 2)
                self.assertIn("fresh authoritative company-graph read", stderr.getvalue())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
