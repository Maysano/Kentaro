import json
from pathlib import Path
from unittest.mock import mock_open, patch
import unittest
from kentaro.api.demo import DemoClient
from kentaro.config.loader import load_config
from kentaro.reports.brief import render_brief

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "examples/configs/demo.toml"


class VerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG)
        self.client = DemoClient(self.config["fixture"], self.config["scope"])

    def test_mutations_rejected(self):
        for method in ("POST", "PUT", "PATCH", "DELETE", "post", "HEAD"):
            with self.subTest(method=method), self.assertRaises(ValueError):
                self.client.request(method)
        for name in ("create", "update", "delete", "approve", "archive"):
            self.assertFalse(hasattr(self.client, name))

    def test_scope_and_cross_scope_edges(self):
        data = json.loads(self.config["fixture"].read_text())
        other = dict(data["records"][0], id="secret", scope="other")
        data["records"].append(other)
        data["relationships"].append(dict(data["relationships"][0], target="secret"))
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            context = self.client.read_portfolio()
        self.assertNotIn("secret", [r["id"] for r in context["records"]])
        self.assertTrue(all(r["target"] != "secret" for r in context["relationships"]))
        with self.assertRaises(ValueError):
            DemoClient(self.config["fixture"], "unknown").read_portfolio()

    def test_report_provenance_and_unknowns(self):
        context = self.client.request("GET")
        report = render_brief(context, "local")
        for record in context["records"] + context["relationships"]:
            self.assertIn(record["id"], report)
            self.assertIn(record["updated_at"], report)
            self.assertIn(record["source_ref"], report)
        for text in (context["retrieved_at"], "## Facts", "## Calculations", "## Inferences",
                     "## Recommendations", "uc-2", "owner: unknown", "not live Maysano"):
            self.assertIn(text, report)

    def test_dashboard_preserves_sources_and_escapes_content(self):
        from kentaro.dashboard.render import render_dashboard
        context = self.client.read_portfolio()
        context["records"][0]["title"] = '<script>alert("bad")</script>'
        dashboard = render_dashboard(context)
        self.assertNotIn('<script>', dashboard)
        self.assertIn('&lt;script&gt;', dashboard)
        self.assertIn('Delivery health:', dashboard)
        for record in context["records"] + context["relationships"]:
            self.assertIn(record["id"], dashboard)
            self.assertIn(record["source_ref"], dashboard)
            self.assertIn(record["updated_at"], dashboard)

    def test_inline_dashboard_is_fragment_with_sources(self):
        from kentaro.dashboard.render import render_dashboard
        context = self.client.read_portfolio()
        fragment = render_dashboard(context, inline=True)
        self.assertNotIn("<!doctype", fragment.lower())
        self.assertNotIn("<html", fragment.lower())
        self.assertIn('<style>', fragment)
        self.assertIn('kd-metrics', fragment)
        for record in context["records"]:
            self.assertIn(record["source_ref"], fragment)
        self.assertIn(context["retrieved_at"], fragment)

    def test_unsafe_config_rejected(self):
        text = CONFIG.read_text()
        for before, after in [('read_only = true', 'read_only = false'),
                              ('mode = "local"', 'mode = "invalid"'),
                              ('enabled = false', 'enabled = true'),
                              ('ttl_seconds = 300', 'ttl_seconds = 0')]:
            content = text.replace(before, after).encode("utf-8")
            with patch("pathlib.Path.open", mock_open(read_data=content)):
                with self.subTest(after=after), self.assertRaises(ValueError):
                    load_config(CONFIG)



if __name__ == "__main__":
    unittest.main()
