"""Read-only dashboard from the same scoped context as the briefing."""
from collections import Counter
from html import escape


def render_dashboard(context, *, inline=False):
    def esc(value):
        return escape(str(value), quote=True)

    records = context["records"]
    source_label = context.get("source_label", "Synthetic demo")
    cache_label = context.get("cache_label", "Cache disabled")
    owner_fields_available = context.get("owner_fields_available", True)

    def source_version(item):
        return f"v{item['version']}" if item["version"] != "not supplied" else "version not supplied"

    def source_updated(item):
        return f"updated {item['updated_at']}" if item["updated_at"] != "not supplied" else "updated not supplied"

    def record_version(item):
        return f"Version {item['version']}" if item["version"] != "not supplied" else "Version not supplied"

    def record_updated(item):
        return f"Updated {item['updated_at']}" if item["updated_at"] != "not supplied" else "Updated not supplied"

    counts = Counter(r["kind"] for r in records)
    missing = [r for r in records if not r["owner"]]
    metrics = [("Objectives", counts["objective"]), ("Use cases", counts["use_case"]),
               ("Data products", counts["data_product"]),
               ("Missing owners" if owner_fields_available else "Owners unavailable", len(missing))]
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
                            f'({esc(e["id"])}, {esc(source_version(e))}, '
                            f'{esc(source_updated(e))}, {esc(e["source_ref"])})</li>' for e in edges)
            owner = record["owner"] or ("Unassigned" if owner_fields_available else "Unavailable from source")
            rows.append(f'<tr><td><details><summary>{esc(record["title"])} '
                        f'<code>{esc(record["id"])}</code></summary>'
                        f'<p>{esc(record_version(record))} · {esc(record_updated(record))}</p>'
                        f'<p>Source: <code>{esc(record["source_ref"])}</code></p><ul>{links}</ul>'
                        f'</details></td><td>{esc(owner)}</td>'
                        f'<td>{esc(record["state"])}</td></tr>')
        empty = "Not available from source API" if not owner_fields_available and kind in {"decision", "risk", "evidence"} else "No records retrieved"
        groups.append(f'<section><h2>{title}</h2><table><thead><tr><th>Record and sources</th>'
                      f'<th>Owner</th><th>Recorded state</th></tr></thead><tbody>'
                      + ("".join(rows) or f'<tr><td colspan="3">{empty}</td></tr>')
                      + '</tbody></table></section>')
    gaps = (", ".join(esc(r["id"]) for r in missing) or "None in retrieved records") if owner_fields_available else "Owner field unavailable from external API"
    ownership_heading = "Ownership gap" if owner_fields_available else "Ownership availability"
    limitations = "".join(f'<li>{esc(item)}</li>' for item in context["limitations"])
    if inline:
        cards = "".join(f'<div class="card viz-stat"><span>{label}</span>'
                        f'<div class="viz-stat-value tabular-nums">{value}</div></div>'
                        for label, value in metrics)
        sections = ''.join(groups).replace('<section>', '<section class="kd-section">')
        sections = sections.replace('<h2>', '<h3>').replace('</h2>', '</h3>')
        sections = sections.replace('<table>', '<div class="table-responsive"><table class="table table-sm">')
        sections = sections.replace('</table>', '</table></div>')
        sections = sections.replace('<summary>', '<summary class="cursor-interaction">')
        return f"""<div id="kentaro-portfolio-dashboard" aria-labelledby="kd-title">
<style>
#kentaro-portfolio-dashboard {{ color: var(--foreground); }}
#kentaro-portfolio-dashboard .kd-header {{ display: flex; align-items: start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }}
#kentaro-portfolio-dashboard .kd-kicker {{ margin: 0 0 6px; color: var(--muted-foreground); font-size: var(--font-size-base); }}
#kentaro-portfolio-dashboard h2 {{ margin: 0; }}
#kentaro-portfolio-dashboard .kd-meta {{ margin: 8px 0 0; color: var(--muted-foreground); }}
#kentaro-portfolio-dashboard .kd-scope {{ margin: 0; padding-top: 4px; white-space: nowrap; color: var(--muted-foreground); }}
#kentaro-portfolio-dashboard .kd-metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
#kentaro-portfolio-dashboard .kd-findings {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 16px 0 24px; }}
#kentaro-portfolio-dashboard .kd-finding {{ padding: 14px; }}
#kentaro-portfolio-dashboard .kd-finding p {{ margin: 0; }}
#kentaro-portfolio-dashboard .kd-finding p + p {{ margin-top: 6px; }}
#kentaro-portfolio-dashboard .kd-label {{ color: var(--muted-foreground); }}
#kentaro-portfolio-dashboard .kd-section {{ margin-top: 28px; }}
#kentaro-portfolio-dashboard .kd-section h3 {{ margin: 0 0 10px; }}
#kentaro-portfolio-dashboard details p {{ margin: 8px 0; }}
#kentaro-portfolio-dashboard details ul {{ margin: 8px 0 0; padding-left: 20px; }}
#kentaro-portfolio-dashboard footer {{ margin-top: 28px; }}
#kentaro-portfolio-dashboard footer p {{ margin: 10px 0; }}
@media (max-width: 620px) {{
  #kentaro-portfolio-dashboard .kd-header {{ display: block; }}
  #kentaro-portfolio-dashboard .kd-scope {{ margin-top: 10px; }}
  #kentaro-portfolio-dashboard .kd-metrics, #kentaro-portfolio-dashboard .kd-findings {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
</style>
<header class="kd-header"><div><p class="kd-kicker">KENTARO · READ-ONLY PORTFOLIO</p><h2 id="kd-title">Portfolio status</h2>
<p class="kd-meta">{esc(source_label)} · Retrieved {esc(context['retrieved_at'])} UTC</p></div>
<p class="kd-scope">Scope <code>{esc(context['scope'])}</code></p></header>
<div class="kd-metrics" aria-label="Calculated record counts">{cards}</div>
<aside class="kd-findings" aria-label="Portfolio attention items"><div class="card kd-finding"><p class="kd-label">{ownership_heading}</p><p><strong>{gaps}</strong></p></div>
<div class="card kd-finding"><p class="kd-label">Delivery health</p><p><strong>Unknown</strong> — readiness criteria and milestone data unavailable.</p></div></aside>
{sections}
<footer><hr><p class="text-small">Snapshot · {esc(cache_label)} · Model execution disabled. Retrieval time is not platform freshness.</p>
<details><summary class="cursor-interaction">Limitations and evidence boundary</summary><ul>{limitations}</ul>
<p>Recorded states and evidence presence do not establish delivery readiness.</p></details></footer>
</div>"""
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kentaro portfolio status</title>
<style>
/* Maysano visual tokens, retrieved from https://maysano.com/assets/index-5gJK1Z9N-vbd0c3f9.css. */
:root {{
  --background:80 30% 96%; --foreground:208 42% 25%; --heading:208 42% 19%;
  --border:80 20% 85%; --card:80 25% 98%; --card-foreground:208 42% 15%;
  --card-border:80 20% 88%; --primary:99 30% 34%; --primary-foreground:0 0% 100%;
  --secondary:80 20% 90%; --muted:80 15% 88%; --muted-foreground:145 11% 38%;
  --accent:80 35% 88%; --navy:208 42% 19%; --navy-foreground:80 30% 95%; --lime:80 45% 72%;
  --font-sans:"Avenir Next",Avenir,"Segoe UI",Helvetica,Arial,sans-serif;
  --font-mono:ui-monospace,"SFMono-Regular",Menlo,Monaco,Consolas,monospace;
  --radius:.5rem; --shadow-sm:0 2px 0 0 hsl(208 42% 19% / .03),0 1px 2px -1px hsl(208 42% 19% / .05);
  color:hsl(var(--foreground)); background:hsl(var(--background)); font-family:var(--font-sans);
  font-synthesis:none; text-rendering:optimizeLegibility; -webkit-font-smoothing:antialiased;
}}
* {{box-sizing:border-box}} body {{min-width:320px;margin:0;background:hsl(var(--background));color:hsl(var(--foreground));line-height:1.5}}
body > header {{padding:clamp(42px,7vw,78px) max(20px,calc((100vw - 1100px) / 2));background:radial-gradient(circle at 88% 32%,hsl(197 66% 34% / .22),transparent 34%),radial-gradient(circle at 52% 118%,hsl(160 44% 29% / .17),transparent 42%),hsl(var(--navy));color:hsl(var(--navy-foreground));border-bottom:1px solid hsl(var(--navy) / .25)}}
h1,h2 {{color:hsl(var(--heading))}} body > header h1 {{max-width:720px;margin:0;color:hsl(var(--navy-foreground));font-size:clamp(2.45rem,5vw,4.6rem);font-weight:700;letter-spacing:-.045em;line-height:.96}}
p {{line-height:1.58}} .meta {{margin:10px 0 0;color:hsl(var(--navy-foreground) / .7);font-size:.92rem}} body > header > p:first-child {{margin:0 0 14px;color:hsl(var(--lime));font-size:.74rem;font-weight:700;letter-spacing:.14em}}
code {{font-family:var(--font-mono);font-size:.84em;overflow-wrap:anywhere}} body > header code {{color:hsl(var(--lime))}}
.metrics,.findings,section,footer {{width:min(1100px,calc(100% - 40px));margin-left:auto;margin-right:auto}} .metrics {{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:28px}}
.metric {{min-height:132px;padding:18px 20px;background:hsl(var(--card));border:1px solid hsl(var(--card-border));border-radius:var(--radius);box-shadow:var(--shadow-sm)}} .metric span {{display:block;color:hsl(var(--muted-foreground));font-size:.78rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase}} .metric strong {{display:block;margin-top:15px;color:hsl(var(--heading));font-size:2.35rem;font-weight:600;letter-spacing:-.045em;line-height:1}}
.findings {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}} .findings p {{min-height:88px;margin:0;padding:16px 18px;background:hsl(var(--secondary));border-left:3px solid hsl(var(--primary));color:hsl(var(--foreground));font-size:.93rem}} .findings strong {{display:block;margin-bottom:5px;color:hsl(var(--heading));font-size:.78rem;letter-spacing:.07em;text-transform:uppercase}}
section {{margin-top:42px}} section h2 {{margin:0 0 12px;font-size:clamp(1.35rem,2vw,1.75rem);font-weight:600;letter-spacing:-.025em}} table {{width:100%;border:1px solid hsl(var(--card-border));border-collapse:separate;border-spacing:0;table-layout:fixed;background:hsl(var(--card));box-shadow:var(--shadow-sm)}} th,td {{padding:14px 16px;border-bottom:1px solid hsl(var(--border));text-align:left;vertical-align:top;overflow-wrap:anywhere}} th {{background:hsl(var(--secondary));color:hsl(var(--muted-foreground));font-size:.73rem;font-weight:700;letter-spacing:.075em;text-transform:uppercase}} th:first-child {{width:55%}} tr:last-child td {{border-bottom:0}} summary {{cursor:pointer;color:hsl(var(--heading));font-weight:600;line-height:1.55}} summary::marker {{color:hsl(var(--primary))}} details p,details li {{font-size:.88rem;line-height:1.6}} details p {{color:hsl(var(--muted-foreground))}} details ul {{padding-left:20px}} details ul:empty {{display:none}}
footer {{margin-top:44px;margin-bottom:48px;padding-top:26px;border-top:1px solid hsl(var(--border))}} footer h2 {{font-size:1.35rem}} footer ul {{padding-left:20px}} footer li {{margin:8px 0;color:hsl(var(--muted-foreground));font-size:.92rem}} @media(max-width:680px) {{.metrics {{grid-template-columns:repeat(2,minmax(0,1fr))}} .findings {{grid-template-columns:1fr}} th,td {{padding:12px 10px}} th:first-child {{width:50%}}}} @media(max-width:420px) {{.metrics,section,footer,.findings {{width:calc(100% - 24px)}} body > header {{padding-left:12px;padding-right:12px}} .metric {{padding:15px 14px}} th,td {{padding:10px 7px;font-size:.86rem}}}}
</style>
<header><p class="meta">KENTARO · READ-ONLY PORTFOLIO</p><h1>Portfolio status</h1>
<p>{esc(source_label)} · Scope <code>{esc(context['scope'])}</code></p>
<p class="meta">Retrieved {esc(context['retrieved_at'])} · {esc(cache_label)} · Model execution disabled</p></header>
<div class="metrics" aria-label="Calculated record counts">{cards}</div>
<div class="findings" aria-label="Portfolio attention items"><p><strong>{esc(ownership_heading)}:</strong>{gaps}</p>
<p><strong>Delivery health:</strong>Unknown — readiness criteria and milestone data unavailable.</p></div>
{''.join(groups)}
<footer><h2>Freshness and limitations</h2><p>Times are UTC. Retrieval time is not platform freshness;
record update times appear in source details. Counts describe the retrieved scope.
Recorded active states do not establish delivery health. Evidence presence does not prove readiness.</p>
<ul>{limitations}</ul></footer></html>"""
