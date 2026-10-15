"""Read-only dashboard from the same scoped context as the briefing."""
from collections import Counter
from html import escape


def render_dashboard(context, *, inline=False):
    def esc(value):
        return escape(str(value), quote=True)

    records = context["records"]
    counts = Counter(r["kind"] for r in records)
    missing = [r for r in records if not r["owner"]]
    metrics = [("Objectives", counts["objective"]), ("Use cases", counts["use_case"]),
               ("Data products", counts["data_product"]), ("Missing owners", len(missing))]
    cards = "".join(f'<div class="metric"><span>{label}</span><strong>{value}</strong></div>'
                    for label, value in metrics)
    groups = []
    for kind, title in [("objective", "Business objectives"), ("use_case", "Use cases"),
                        ("data_product", "Data products"), ("decision", "Decisions"),
                        ("risk", "Risks"), ("evidence", "Evidence")]:
        rows = []
        for record in records:
            if record["kind"] != kind:
                continue
            edges = [r for r in context["relationships"]
                     if record["id"] in (r["source"], r["target"])]
            links = "".join(f'<li>{esc(e["source"])} → {esc(e["type"])} → {esc(e["target"])} '
                            f'({esc(e["id"])}, v{esc(e["version"])}, '
                            f'{esc(e["updated_at"])}, {esc(e["source_ref"])})</li>' for e in edges)
            rows.append(f'<tr><td><details><summary>{esc(record["title"])} '
                        f'<code>{esc(record["id"])}</code></summary>'
                        f'<p>Version {esc(record["version"])} · Updated {esc(record["updated_at"])}</p>'
                        f'<p>Source: <code>{esc(record["source_ref"])}</code></p><ul>{links}</ul>'
                        f'</details></td><td>{esc(record["owner"] or "Unassigned")}</td>'
                        f'<td>{esc(record["state"])}</td></tr>')
        groups.append(f'<section><h2>{title}</h2><table><thead><tr><th>Record and sources</th>'
                      f'<th>Owner</th><th>Recorded state</th></tr></thead><tbody>'
                      + ("".join(rows) or '<tr><td colspan="3">No records retrieved</td></tr>')
                      + '</tbody></table></section>')
    gaps = ", ".join(esc(r["id"]) for r in missing) or "None in retrieved records"
    limitations = "".join(f'<li>{esc(item)}</li>' for item in context["limitations"])
    if inline:
        cards = "".join(f'<div class="card viz-stat"><span>{label}</span>'
                        f'<div class="viz-stat-value tabular-nums">{value}</div></div>'
                        for label, value in metrics)
        sections = ''.join(groups).replace('<table>', '<table class="table table-sm">')
        sections = sections.replace('<summary>', '<summary class="cursor-interaction">')
        return f"""<div id="kentaro-portfolio-dashboard">
<header><h2>Portfolio status</h2><p>Synthetic demo · <code>{esc(context['scope'])}</code></p>
<p class="text-small">Retrieved {esc(context['retrieved_at'])} · UTC</p></header>
<div class="viz-grid" aria-label="Calculated record counts">{cards}</div>
<p><strong>Ownership gap:</strong> {gaps}</p>
<p><strong>Delivery health:</strong> Unknown — readiness criteria and milestone data unavailable.</p>
{sections}
<footer><hr><p class="text-small">Snapshot · Cache disabled · Model execution disabled.
Expand records for versions, update timestamps and source references.
Retrieval time is fixture load time, not platform freshness.</p>
<details><summary class="cursor-interaction">Limitations</summary><ul>{limitations}</ul>
<p>Recorded states and evidence presence do not establish delivery readiness.</p></details></footer>
</div>"""
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kentaro portfolio status</title>
<style>
:root {{color-scheme:light dark;font-family:system-ui,sans-serif;background:light-dark(#f5f7fa,#14181f);color:light-dark(#182333,#e4eaf2)}}
body {{max-width:1100px;margin:auto;padding:32px 20px}} h1 {{margin-bottom:8px}} p {{line-height:1.5}}
.meta {{color:light-dark(#4a596c,#b4c0cf)}} .metrics {{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin:28px 0}}
.metric {{padding:20px;background:light-dark(#fff,#202834);border-radius:12px}} .metric span {{display:block}} .metric strong {{display:block;font-size:2rem;margin-top:8px}}
section {{margin:28px 0}} table {{width:100%;border-collapse:collapse;table-layout:fixed}} th,td {{text-align:left;padding:14px 8px;border-bottom:1px solid light-dark(#ccd5df,#394657);vertical-align:top;overflow-wrap:anywhere}}
th:first-child {{width:55%}} summary {{cursor:pointer;line-height:1.6}} code {{font-size:.9em}} details p,details li {{font-size:.9em;line-height:1.6}} ul {{padding-left:20px}} footer {{margin-top:32px}}
@media(max-width:500px) {{body {{padding:16px 12px}} th:first-child {{width:45%}} th,td {{padding:10px 4px}}}}
</style>
<header><p class="meta">KENTARO · READ-ONLY PORTFOLIO</p><h1>Portfolio status</h1>
<p>Synthetic demo · Scope <code>{esc(context['scope'])}</code></p>
<p class="meta">Retrieved {esc(context['retrieved_at'])} · Cache disabled · Model execution disabled</p></header>
<div class="metrics" aria-label="Calculated record counts">{cards}</div>
<p><strong>Ownership gap:</strong> {gaps}</p>
<p><strong>Delivery health:</strong> Unknown — readiness criteria and milestone data unavailable.</p>
{''.join(groups)}
<footer><h2>Freshness and limitations</h2><p>Times are UTC. Retrieval time is fixture load time;
record update times appear in source details. Counts describe the retrieved scope.
Recorded active states do not establish delivery health. Evidence presence does not prove readiness.</p>
<ul>{limitations}</ul></footer></html>"""
