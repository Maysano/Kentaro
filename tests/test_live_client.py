import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from kentaro.api.live import LiveClient, load_live_environment
from kentaro.config.loader import load_config


ROOT = Path(__file__).resolve().parents[1]


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class LiveClientTests(unittest.TestCase):
    def setUp(self):
        self.environment = TemporaryDirectory()
        self.env_file = Path(self.environment.name) / ".env"
        self.env_file.write_text(
            "API_BASE_URL=https://pilot.example.test/api/external/v1\nAPI_KEY=not-a-real-key\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.environment.cleanup()

    def test_live_config_has_no_credentials(self):
        config = load_config(ROOT / "examples/configs/live.toml")
        self.assertEqual(config["profile"], "live")
        self.assertNotIn("API_KEY", config)

    def test_environment_rejects_executable_or_unknown_content(self):
        self.env_file.write_text("API_BASE_URL=https://pilot.example.test\nAPI_KEY=value\nEXTRA=value\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_live_environment(self.env_file)

    def test_live_read_normalises_records_and_links_without_network_side_effects(self):
        responses = {
            "/api/external/v1/products?limit=100&offset=0": {
                "data": [{"id": "product-1", "name": "Product", "status": "published", "version": "1", "updatedAt": "2026-10-15T10:00:00Z"}],
                "pagination": {"limit": 100, "offset": 0, "total": 1},
            },
            "/api/external/v1/business-objectives?limit=100&offset=0": {
                "data": [{"id": "objective-1", "title": "Objective", "status": "active", "updatedAt": "2026-10-15T10:00:00Z"}],
                "pagination": {"limit": 100, "offset": 0, "total": 1},
            },
            "/api/external/v1/business-use-cases?limit=100&offset=0": {
                "data": [{"id": "use-case-1", "name": "Use case", "status": "draft", "updatedAt": "2026-10-15T10:00:00Z"}],
                "pagination": {"limit": 100, "offset": 0, "total": 1},
            },
            "/api/external/v1/products/product-1": {"id": "product-1", "links": {"objectives": ["objective-1"]}, "linksTruncated": {"objectives": False}},
            "/api/external/v1/business-objectives/objective-1": {"id": "objective-1", "links": {"products": ["product-1"], "useCases": ["use-case-1"]}, "linksTruncated": {"products": False, "useCases": False}},
            "/api/external/v1/business-use-cases/use-case-1": {"id": "use-case-1", "links": {"products": ["product-1"]}, "linksTruncated": {"products": False}},
        }
        calls = []

        def fake_urlopen(request, timeout, context):
            calls.append((request, timeout))
            path = request.full_url.replace("https://pilot.example.test", "")
            return Response(json.dumps(responses[path]).encode("utf-8"))

        with patch("kentaro.api.live.urlopen", fake_urlopen):
            context = LiveClient(self.env_file, "organization-bound").read_portfolio()

        self.assertEqual({record["kind"] for record in context["records"]}, {"data_product", "objective", "use_case"})
        self.assertTrue(all(record["owner"] is None for record in context["records"]))
        self.assertTrue(any(link["type"] == "related_use_case" for link in context["relationships"]))
        self.assertTrue(all(request.get_method() == "GET" for request, _ in calls))
        self.assertTrue(all(request.get_header("Authorization") == "Bearer not-a-real-key" for request, _ in calls))
        self.assertIn("The external API does not provide owner fields; ownership is unknown unless another approved source is added.", context["limitations"])
        from kentaro.dashboard.render import render_dashboard
        from kentaro.reports.brief import render_brief
        self.assertIn("Owner information unavailable", render_brief(context, "local"))
        dashboard = render_dashboard(context)
        self.assertIn("Owners unavailable", dashboard)
        self.assertIn("Ownership availability", dashboard)
        self.assertIn("Unavailable from source", dashboard)
        self.assertIn("Not available from source API", dashboard)
        self.assertNotIn("vnot supplied", dashboard)
        self.assertNotIn("Version ersion", dashboard)
        self.assertNotIn("Ownership gap", dashboard)

    def test_live_client_rejects_mutation(self):
        client = LiveClient(self.env_file, "organization-bound")
        with self.assertRaises(ValueError):
            client.request("POST")


if __name__ == "__main__":
    unittest.main()
