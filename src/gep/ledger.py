"""SQLite durable run ledger. Remote execution requires explicit operator approval."""
import os,sqlite3
from uuid import uuid4
from datetime import datetime,timezone
from .integrations import PROVIDERS

def utc():return datetime.now(timezone.utc).isoformat()
class RunLedger:
    def __init__(self,path):
        self.path=path
        with self.db() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS agent_runs (
              id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
              provider TEXT NOT NULL,status TEXT NOT NULL,session_id TEXT,
              result TEXT NOT NULL DEFAULT '',error TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL,updated_at TEXT NOT NULL)""")
    def db(self):
        con=sqlite3.connect(self.path);con.row_factory=sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con
    def get(self,rid):
        with self.db() as db:
            row=db.execute("SELECT * FROM agent_runs WHERE id=?",(rid,)).fetchone()
        if not row:raise ValueError("Unknown run")
        return dict(row)
    def change(self,rid,status,session=None,result="",error=""):
        with self.db() as db:
            db.execute("""UPDATE agent_runs SET status=?,session_id=COALESCE(?,session_id),
                result=?,error=?,updated_at=? WHERE id=?""",
                (status,session,result,error,utc(),rid))
    def launch(self,task_id,provider,prompt,workspace,approved=False):
        if not approved:raise ValueError("Explicit --approve required for external execution")
        if provider not in PROVIDERS:raise ValueError("Unknown provider")
        if not os.path.isdir(workspace):raise ValueError("Workspace does not exist")
        with self.db() as db:
            task=db.execute("""SELECT p.state FROM tasks t
             JOIN projects p ON p.id=t.project_id WHERE t.id=?""",(task_id,)).fetchone()
            if task is None or task["state"]!="active":raise ValueError("Task needs active project")
            ongoing=db.execute("""SELECT id FROM agent_runs WHERE task_id=?
             AND status IN ('dispatched','submitted','running')""",(task_id,)).fetchone()
            if ongoing:raise ValueError("Task has an unfinished run")
            rid="run_"+uuid4().hex
            db.execute("""INSERT INTO agent_runs
             (id,task_id,provider,status,created_at,updated_at)
             VALUES (?,?,?,?,?,?)""",(rid,task_id,provider,"dispatched",utc(),utc()))
        try:
            outcome=PROVIDERS[provider]().launch(prompt,workspace)
        except Exception as e:
            self.change(rid,"needs_reconciliation",error=str(e)[:1000]);raise
        self.change(rid,outcome["status"],outcome.get("session_id"),outcome.get("result",""))
        return self.get(rid)
    def poll(self,rid):
        run=self.get(rid)
        if run["provider"]=="openhands" and run["status"] in ("submitted","running"):
            result=PROVIDERS["openhands"]().poll(run["session_id"])
            self.change(rid,result["status"],result=result["result"])
        return self.get(rid)
    def list(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT 100")]
