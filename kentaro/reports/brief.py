"""Deterministic report generation; no inferred portfolio relationships."""
from collections import Counter


def render_brief(context, model_policy):
    records = context["records"]
    owner_fields_available = context.get("owner_fields_available", True)

    def source_version(record):
        return f"v{record['version']}" if record["version"] != "not supplied" else "version not supplied"

    lines = ["# Portfolio brief", "", f"Source: {context.get('source_label', 'synthetic demo fixture (not live Maysano)')}.",
             f"Scope: {context['scope']}", f"Retrieved: {context['retrieved_at']}",
             f"Model policy: {model_policy} (execution disabled)", context.get("cache_label", "Cache: disabled"), "", "## Facts", ""]
    for r in records:
        lines.append(f"- {r['kind']}: {r['title']} ; owner: {r['owner'] or 'unknown'}; "
                     f"state: {r['state']} [{r['id']}, {source_version(r)}, "
                     f"updated {r['updated_at']}, source {r['source_ref']}]")
    lines += ["", "## Relationships (facts)", ""]
    for r in context["relationships"]:
        lines.append(f"- {r['source']} -> {r['type']} -> {r['target']} "
                     f"[{r['id']}, {source_version(r)}, updated {r['updated_at']}, source {r['source_ref']}]")
    lines += ["", "## Calculations", ""]
    for kind, count in sorted(Counter(r["kind"] for r in records).items()):
        lines.append(f"- {kind}: {count} (count of listed records)")
    missing = [r["id"] for r in records if not r["owner"]]
    if owner_fields_available:
        lines.append(f"- Records missing ownership: {len(missing)} ({', '.join(missing) or 'none'}).")
    else:
        lines.append(f"- Owner information unavailable: {len(records)} retrieved records; the external API does not return owner fields.")
    lines += ["", "## Inferences", "", "None generated.", "", "## Recommendations", ""]
    if owner_fields_available:
        lines += [f"- Confirm ownership for {id}; the source does not identify an owner." for id in missing]
        if not missing:
            lines.append("None generated.")
    else:
        lines.append("None generated: the external API does not supply owner fields.")
    lines += ["", "## Limitations and unknowns", ""]
    lines += ["- " + item for item in context["limitations"]]
    return "\n".join(lines) + "\n"
