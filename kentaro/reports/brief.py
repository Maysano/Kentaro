"""Deterministic report generation; no inferred portfolio relationships."""
from collections import Counter


def render_brief(context, model_policy):
    records = context["records"]
    lines = ["# Portfolio brief", "", "Source: synthetic demo fixture (not live Maysano).",
             f"Scope: {context['scope']}", f"Retrieved: {context['retrieved_at']}",
             f"Model policy: {model_policy} (execution disabled)", "Cache: disabled", "", "## Facts", ""]
    for r in records:
        lines.append(f"- {r['kind']}: {r['title']} ; owner: {r['owner'] or 'unknown'}; "
                     f"state: {r['state']} [{r['id']}, v{r['version']}, "
                     f"updated {r['updated_at']}, source {r['source_ref']}]")
    lines += ["", "## Relationships (facts)", ""]
    for r in context["relationships"]:
        lines.append(f"- {r['source']} -> {r['type']} -> {r['target']} "
                     f"[{r['id']}, v{r['version']}, updated {r['updated_at']}, source {r['source_ref']}]")
    lines += ["", "## Calculations", ""]
    for kind, count in sorted(Counter(r["kind"] for r in records).items()):
        lines.append(f"- {kind}: {count} (count of listed records)")
    missing = [r["id"] for r in records if not r["owner"]]
    lines += [f"- Records missing ownership: {len(missing)} ({', '.join(missing) or 'none'}).",
              "", "## Inferences", "", "None generated.", "", "## Recommendations", ""]
    lines += [f"- Confirm ownership for {id}; the source does not identify an owner." for id in missing]
    if not missing:
        lines.append("None generated.")
    lines += ["", "## Limitations and unknowns", ""]
    lines += ["- " + item for item in context["limitations"]]
    return "\n".join(lines) + "\n"
