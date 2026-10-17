"""Read-only client for the documented Maysano external pilot API."""
from __future__ import annotations

import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


RESOURCE_SPECS = (
    ("products", "data_product", "name"),
    ("business-objectives", "objective", "title"),
    ("business-use-cases", "use_case", "name"),
)
LINK_KINDS = {
    "products": "data_product",
    "objectives": "objective",
    "useCases": "use_case",
    "kpis": "kpi",
}


def _trusted_tls_context():
    """Keep TLS verification enabled, preferring certifi when the runtime supplies it."""
    try:
        import certifi
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


class RequestBudgetExhausted(Exception):
    """Raised before exceeding the documented per-key request allowance."""


def load_live_environment(path):
    """Read only the expected key/value pairs without executing a dotenv file."""
    values = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError("Unable to read live environment file") from error
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, marker, value = line.partition("=")
        if not marker or key not in {"API_BASE_URL", "API_KEY"}:
            raise ValueError("Live environment file contains an unsupported setting")
        if key in values:
            raise ValueError("Live environment file contains a duplicate setting")
        values[key] = value.strip()
    if not values.get("API_BASE_URL") or not values.get("API_KEY"):
        raise ValueError("Live environment requires API_BASE_URL and API_KEY")
    parsed = urlsplit(values["API_BASE_URL"])
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("API_BASE_URL must be an HTTPS URL without user credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("API_BASE_URL must not contain query or fragment components")
    values["API_BASE_URL"] = values["API_BASE_URL"].rstrip("/")
    return values


class LiveClient:
    """Retrieves read-only portfolio metadata without persisting API responses."""

    def __init__(self, environment_file, scope, *, timeout=30, request_budget=40):
        self._settings = load_live_environment(environment_file)
        self._scope = scope
        self._timeout = timeout
        self._request_budget = request_budget
        self._attempts = 0
        self._tls_context = _trusted_tls_context()

    def request(self, method):
        if method != "GET":
            raise ValueError("Only GET is permitted in Kentaro v0.1")
        return self.read_portfolio()

    def _get_json(self, path, parameters=None):
        if self._attempts >= self._request_budget:
            raise RequestBudgetExhausted
        query = urlencode(parameters or {})
        url = self._settings["API_BASE_URL"] + path + ("?" + query if query else "")
        request = Request(url, headers={"Authorization": "Bearer " + self._settings["API_KEY"]}, method="GET")
        self._attempts += 1
        try:
            with urlopen(request, timeout=self._timeout, context=self._tls_context) as response:
                return json.load(response)
        except HTTPError as error:
            raise ValueError(f"Maysano API request failed with HTTP status {error.code}") from error
        except URLError as error:
            raise ValueError("Maysano API connection failed") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Maysano API returned invalid JSON") from error

    def _list_resource(self, resource):
        rows = []
        offset = 0
        total = None
        complete = False
        while True:
            try:
                payload = self._get_json("/" + resource, {"limit": 100, "offset": offset})
            except RequestBudgetExhausted:
                return rows, False, total
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                raise ValueError(f"Maysano API returned an invalid {resource} list response")
            pagination = payload.get("pagination")
            if not isinstance(pagination, dict) or not isinstance(pagination.get("total"), int):
                raise ValueError(f"Maysano API returned invalid {resource} pagination")
            rows.extend(payload["data"])
            total = pagination["total"]
            if not payload["data"] or offset + 100 >= total:
                complete = True
                break
            offset += 100
        return rows, complete, total

    @staticmethod
    def _normalise_record(row, resource, kind, title_key):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError(f"Maysano API returned a {resource} record without an ID")
        record_id = row["id"]
        title = row.get(title_key)
        return {
            "id": record_id,
            "kind": kind,
            "title": title if isinstance(title, str) and title else "not supplied",
            "owner": None,
            "state": row.get("status") if isinstance(row.get("status"), str) else "not supplied",
            "version": str(row["version"]) if row.get("version") is not None else "not supplied",
            "updated_at": row.get("updatedAt") if isinstance(row.get("updatedAt"), str) else "not supplied",
            "source_ref": f"maysano:/{resource}/{quote(record_id, safe='')}",
            "resource": resource,
        }

    def _links_for_record(self, record, known_ids, limitations):
        try:
            detail = self._get_json("/" + record["resource"] + "/" + quote(record["id"], safe=""))
        except RequestBudgetExhausted:
            limitations.append("Relationship retrieval stopped before the documented request budget was exceeded.")
            return [], False
        if not isinstance(detail, dict) or detail.get("id") != record["id"]:
            raise ValueError(f"Maysano API returned an invalid detail response for {record['id']}")
        links = detail.get("links", {})
        truncated = detail.get("linksTruncated", {})
        if not isinstance(links, dict) or not isinstance(truncated, dict):
            raise ValueError(f"Maysano API returned invalid link metadata for {record['id']}")
        relationships = []
        for collection, target_kind in LINK_KINDS.items():
            values = links.get(collection)
            if values is None:
                continue
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ValueError(f"Maysano API returned invalid {collection} links for {record['id']}")
            if truncated.get(collection) is True:
                limitations.append(f"Links from {record['id']} to {collection} are truncated by the source API.")
            for target in values:
                if target not in known_ids:
                    limitations.append(f"A documented link from {record['id']} to {target} could not be represented in the retrieved record set.")
                    continue
                relationships.append({
                    "id": f"client-link:{record['id']}:{collection}:{target}",
                    "source": record["id"],
                    "target": target,
                    "type": "related_" + target_kind,
                    "version": "not supplied",
                    "updated_at": "not supplied",
                    "source_ref": record["source_ref"] + "#links." + collection,
                })
        return relationships, True

    def read_portfolio(self):
        records = []
        limitations = [
            "Live Maysano pilot API snapshot; the key is organization-bound and permissions are independent.",
            "The external API does not provide owner fields; ownership is unknown unless another approved source is added.",
            "The external API does not provide relationship IDs, versions, or timestamps; displayed link references are client-derived from detail responses.",
            "List pagination is not a consistent snapshot; records may change while pages are read.",
            "Responses are not cached because the API specifies Cache-Control: no-store.",
            "Decisions, risks, evidence, approval history, and delivery milestones are not available through the documented external endpoints.",
        ]
        for resource, kind, title_key in RESOURCE_SPECS:
            rows, complete, total = self._list_resource(resource)
            if not complete:
                limitations.append(f"{resource} retrieval is incomplete after {len(rows)} of {total if total is not None else 'unknown'} listed records.")
            records.extend(self._normalise_record(row, resource, kind, title_key) for row in rows)
        ids = {record["id"] for record in records}
        if len(ids) != len(records):
            raise ValueError("Maysano API returned duplicate record IDs across retrieved resources")
        relationships = []
        links_complete = True
        for record in records:
            record_links, complete = self._links_for_record(record, ids, limitations)
            relationships.extend(record_links)
            links_complete = links_complete and complete
            if not complete:
                break
        if not links_complete:
            limitations.append("Relationship coverage is incomplete because detail retrieval stopped at the client request budget.")
        return {
            "scope": self._scope,
            "records": records,
            "relationships": relationships,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source_label": "Live Maysano pilot API",
            "cache_label": "Cache disabled (API no-store)",
            "owner_fields_available": False,
            "limitations": list(dict.fromkeys(limitations)),
        }
