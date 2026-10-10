"""Local-only read-only dashboard for goals, projects and execution runs."""
from __future__ import annotations
import html,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .store import GEPStore
from .ledger import RunLedger
from .engine import WorkflowEngine
from .life import LifePortfolio
from .service import ObservationJournal

def dashboard_data(db: str)->dict:
    store=GEPStore(db);store.initialize()
    return {"overview":store.overview(),"runs":RunLedger(db).list(),"workflow":WorkflowEngine(db).snapshot(),"life":LifePortfolio(db).report(),"activity":ObservationJournal(db).latest()}

def render(data:dict)->str:
    goals=data["overview"]["goals"];projects=data["overview"]["projects"];runs=data["runs"]
    escape=lambda x:html.escape(str(x))
    cards="".join(
        '<article><strong>'+escape(p["name"])+'</strong><span>'+escape(p["state"])+
        '</span><small>'+escape(p["id"])+'</small></article>' for p in projects
    ) or '<p class="empty">No projects yet. Create one with the GEP CLI.</p>'
    work=data.get("workflow",{})
    observation=data.get("activity")
    activity_message=("Last local observation: "+str(observation["event_count"])+" events" if observation else "No ActivityWatch data imported")
    life=data.get("life",{})
    budget_msg="Planned: "+str(life.get("weekly_planned_hours",0))+" / "+str(life.get("weekly_available_hours",40))+" discretionary hours"
    stage_items="".join("<article><strong>"+escape(w["name"])+"</strong><span>"+escape(w["state"])+"</span></article>" for w in work.get("workflows",[]))
    stage_items+="".join("<article>"+escape(s["title"])+" · "+escape(s["state"])+"</article>" for s in work.get("steps",[]))
    goal_items="".join('<li>'+escape(g["name"])+' · '+escape(g["domain"])+'</li>' for g in goals)
    run_rows="".join('<tr><td>'+escape(r["provider"])+'</td><td>'+escape(r["status"])+
       '</td><td>'+escape(r["task_id"])+'</td><td>'+escape(r["updated_at"])+
       '</td></tr>' for r in runs)
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GEP Mission Control</title><style>
:root{color-scheme:dark;font-family:system-ui;background:#101622;color:#eff4ff}
body{max-width:1050px;margin:0 auto;padding:30px 22px}
header{border-bottom:1px solid #334257;padding-bottom:20px}
h1{font-size:32px}h2{font-size:20px;margin:28px 0 12px}
p{color:#aebbd0}.pill,article span{background:#2b415b;border-radius:12px;padding:5px 10px;font-size:12px}
section{background:#192335;border-radius:15px;padding:18px;margin-top:18px}
article{background:#233148;padding:15px;border-radius:10px;margin:9px 0;display:flex;gap:15px;flex-wrap:wrap}
small{color:#aebbd0}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;border-bottom:1px solid #344158;padding:12px 6px}
footer{margin-top:30px;color:#90a2ba;font-size:12px}</style></head>
<body><header><span class="pill">LOCAL / READ ONLY</span><h1>GEP Mission Control</h1>
<p>Goals first. Agents execute. Evidence decides what is complete.</p></header>
<section><h2>Life & learning goals</h2><ul>"""+goal_items+"""</ul></section>
<section><h2>Personal time allocation</h2><p>"""+escape(budget_msg)+"""</p></section><section><h2>Observed activity</h2><p>"""+escape(activity_message)+"""</p></section><section><h2>Projects</h2>"""+cards+"""</section>
<section><h2>Workflow milestones</h2>"""+stage_items+"""</section><section><h2>Execution ledger</h2><table>
<thead><tr><th>Executor</th><th>Status</th><th>Task ID</th><th>Updated</th></tr></thead>
<tbody>"""+run_rows+"""</tbody></table></section>
<footer>Provider-reported completion is not verified delivery. External actions require explicit approval.
GEP dashboard is bound to loopback only.</footer></body></html>"""

def serve(db:str,port:int=8765):
    if not (1024<=port<=65535):raise ValueError("Port out of range")
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/","/api/status"):
                self.send_error(404);return
            try:
                data=dashboard_data(db)
                body=(json.dumps(data,ensure_ascii=False) if self.path=="/api/status"
                      else render(data)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type",
                    "application/json; charset=utf-8" if self.path=="/api/status"
                    else "text/html; charset=utf-8")
                self.send_header("Cache-Control","no-store")
                self.send_header("Content-Length",str(len(body)))
                self.end_headers();self.wfile.write(body)
            except Exception:
                self.send_error(500,"Local dashboard failed")
    server=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    print(f"GEP local dashboard: http://127.0.0.1:{port}",flush=True)
    try:server.serve_forever()
    finally:server.server_close()
