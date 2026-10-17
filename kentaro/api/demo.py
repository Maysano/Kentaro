"""Local fixture contract. This module contains no network transport."""
import json
from datetime import datetime, timezone
from importlib.resources import as_file, files


DEMO_SCOPE = "portfolio-demo"


def read_packaged_demo() -> dict:
    """Read the synthetic demo packaged with Kentaro; no configuration or network is used."""
    resource = files("kentaro.resources").joinpath("demo-portfolio.json")
    with as_file(resource) as fixture:
        return DemoClient(fixture, DEMO_SCOPE).read_portfolio()


class DemoClient:
    def __init__(self, fixture, scope):
        self._fixture = fixture
        self._scope = scope

    def request(self, method):
        if method != "GET":
            raise ValueError("Only GET is permitted in Kentaro v0.1")
        return self.read_portfolio()

    def read_portfolio(self):
        with open(self._fixture, encoding="utf-8") as stream:
            data = json.load(stream)
        if data.get("schema_version") != 1 or data.get("synthetic") is not True:
            raise ValueError("Expected a version 1 synthetic fixture")
        records = [r for r in data["records"] if r["scope"] == self._scope]
        if not records:
            raise ValueError("No demo records available in the selected scope")
        ids = {r["id"] for r in records}
        if len(ids) != len(records):
            raise ValueError("Duplicate source IDs")
        for record in records:
            for key in ("id", "kind", "title", "owner", "state", "version", "updated_at", "source_ref"):
                if key not in record:
                    raise ValueError("Incomplete source metadata: " + key)
        relationships = [r for r in data["relationships"] if r["scope"] == self._scope
                         and r["source"] in ids and r["target"] in ids]
        return {"scope": self._scope, "records": records, "relationships": relationships,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "limitations": ["Synthetic fixture; live Maysano API capabilities unverified.",
                                "Fixture load time is not platform freshness; use record timestamps.",
                                "Acceptance criteria, delivery milestones and approval history unavailable."]}
