"""Durable multi-workflow controller with safe leasing, attempts, approvals and audit."""
from __future__ import annotations
import json,sqlite3
from datetime import datetime,timezone,timedelta
from uuid import uuid4
from .store import GEPStore

def timestamp():
    return datetime.now(timezone.utc).isoformat()

class WorkflowEngine:
    def __init__(self,path="gep.db"):
        self.path=str(path)
        GEPStore(path).initialize()
        with self.db() as d:
            d.executescript("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
                name TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'planned',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS steps (
                id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL REFERENCES workflows(id),
                title TEXT NOT NULL, provider TEXT NOT NULL, instruction TEXT NOT NULL,
                workspace TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
                requires_approval INTEGER NOT NULL DEFAULT 1,
                attempt INTEGER NOT NULL DEFAULT 0, max_attempt INTEGER NOT NULL DEFAULT 2,
                lease_token TEXT, lease_until TEXT, run_id TEXT,
                output TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS step_dependencies (
                step_id TEXT NOT NULL REFERENCES steps(id),
                depends_on TEXT NOT NULL REFERENCES steps(id),
                PRIMARY KEY(step_id,depends_on)
            );
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT NOT NULL,
                step_id TEXT, event TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '{}',
                occurred_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stage_artifacts (
                id TEXT PRIMARY KEY, step_id TEXT NOT NULL REFERENCES steps(id),
                kind TEXT NOT NULL, uri TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unverified',
                note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
            );
            """)
    def db(self):
        d=sqlite3.connect(self.path,timeout=20)
        d.row_factory=sqlite3.Row
        d.execute("PRAGMA foreign_keys=ON")
        d.execute("PRAGMA busy_timeout=20000")
        return d
    def event(self,d,wid,sid,event,detail=None):
        d.execute("INSERT INTO workflow_events(workflow_id,step_id,event,detail,occurred_at) VALUES(?,?,?,?,?)",
                  (wid,sid,event,json.dumps(detail or {}),timestamp()))
    def create(self,project_id,name):
        if not name.strip():raise ValueError("Workflow name required")
        wid="wf_"+uuid4().hex[:16]
        with self.db() as d:
            p=d.execute("SELECT id FROM projects WHERE id=?",(project_id,)).fetchone()
            if not p:raise ValueError("Unknown project")
            d.execute("INSERT INTO workflows VALUES(?,?,?,?,?,?)",(wid,project_id,name,"planned",timestamp(),timestamp()))
            self.event(d,wid,None,"created")
        return wid
    def step(self,wid,title,provider,instruction,workspace,depends_on=(),requires_approval=True,max_attempt=2):
        if provider not in ("openclaw","openhands"):raise ValueError("Unsupported provider")
        if not (1<=max_attempt<=10):raise ValueError("Invalid retry bound")
        sid="step_"+uuid4().hex[:16]
        with self.db() as d:
            w=d.execute("SELECT id FROM workflows WHERE id=?",(wid,)).fetchone()
            if not w:raise ValueError("Unknown workflow")
            for dep in depends_on:
                if not d.execute("SELECT id FROM steps WHERE id=? AND workflow_id=?",(dep,wid)).fetchone():
                    raise ValueError("Dependency is not a step of this workflow")
            d.execute("""INSERT INTO steps
            (id,workflow_id,title,provider,instruction,workspace,requires_approval,max_attempt,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (sid,wid,title,provider,instruction,workspace,int(requires_approval),max_attempt,timestamp(),timestamp()))
            for dep in set(depends_on):
                d.execute("INSERT INTO step_dependencies VALUES(?,?)",(sid,dep))
            self.event(d,wid,sid,"step_added")
        return sid
    def start(self,wid):
        with self.db() as d:
            w=d.execute("""SELECT w.state,p.state project_state FROM workflows w
              JOIN projects p ON p.id=w.project_id WHERE w.id=?""",(wid,)).fetchone()
            if not w:raise ValueError("Unknown workflow")
            if w["project_state"]!="active":raise ValueError("Project must be active")
            if w["state"] not in ("planned","paused"):raise ValueError("Workflow cannot start from this state")
            d.execute("UPDATE workflows SET state='running',updated_at=? WHERE id=?",(timestamp(),wid))
            self.event(d,wid,None,"started")
    def pause(self,wid):
        with self.db() as d:
            d.execute("UPDATE workflows SET state='paused',updated_at=? WHERE id=?",(timestamp(),wid))
            self.event(d,wid,None,"paused")
    def approve(self,sid):
        with self.db() as d:
            row=d.execute("SELECT workflow_id,state FROM steps WHERE id=?",(sid,)).fetchone()
            if not row:raise ValueError("Unknown step")
            d.execute("UPDATE steps SET requires_approval=0,updated_at=? WHERE id=?",(timestamp(),sid))
            self.event(d,row["workflow_id"],sid,"approved")
    def recover_stale(self):
        """Expire abandoned leases. Never rerun automatically after uncertain external effects."""
        with self.db() as d:
            rows=d.execute("""SELECT s.id,s.workflow_id FROM steps s JOIN workflows w
                ON w.id=s.workflow_id WHERE s.state='leased' AND s.lease_until<?""",(timestamp(),)).fetchall()
            for row in rows:
                d.execute("""UPDATE steps SET state='needs_reconciliation',lease_token=NULL,
                            lease_until=NULL,updated_at=? WHERE id=?""",(timestamp(),row["id"]))
                self.event(d,row["workflow_id"],row["id"],"lease_expired")
            return len(rows)
    def claim(self,ttl_seconds=300):
        if ttl_seconds<10 or ttl_seconds>3600:raise ValueError("Invalid lease TTL")
        self.recover_stale()
        with self.db() as d:
            d.execute("BEGIN IMMEDIATE")
            row=d.execute("""SELECT s.* FROM steps s JOIN workflows w ON w.id=s.workflow_id
               WHERE w.state='running' AND s.state='pending' AND s.requires_approval=0
                 AND NOT EXISTS (SELECT 1 FROM step_dependencies dep
                   JOIN steps parent ON parent.id=dep.depends_on
                   WHERE dep.step_id=s.id AND parent.state!='verified')
               ORDER BY s.created_at,s.id LIMIT 1""").fetchone()
            if not row:return None
            token=uuid4().hex
            deadline=(datetime.now(timezone.utc)+timedelta(seconds=ttl_seconds)).isoformat()
            d.execute("""UPDATE steps SET state='leased',lease_token=?,lease_until=?,
                attempt=attempt+1,updated_at=? WHERE id=? AND state='pending'""",
                (token,deadline,timestamp(),row["id"]))
            self.event(d,row["workflow_id"],row["id"],"claimed",{"attempt":row["attempt"]+1})
            return {**dict(row),"lease_token":token,"attempt":row["attempt"]+1}
    def complete_execution(self,sid,token,status,run_id=None,output=""):
        if status not in ("reported_complete","submitted","failed","needs_reconciliation"):
            raise ValueError("Invalid execution result")
        with self.db() as d:
            row=d.execute("SELECT workflow_id,lease_token,state FROM steps WHERE id=?",(sid,)).fetchone()
            if not row or row["state"]!="leased" or row["lease_token"]!=token:
                raise ValueError("Lease mismatch or expired")
            state="awaiting_verification" if status=="reported_complete" else status
            d.execute("""UPDATE steps SET state=?,lease_token=NULL,lease_until=NULL,
                run_id=?,output=?,updated_at=? WHERE id=?""",(state,run_id,output[:16000],timestamp(),sid))
            self.event(d,row["workflow_id"],sid,"execution_"+status,{"run_id":run_id})
    def reconcile(self,sid,next_state):
        if next_state not in ("pending","awaiting_verification","failed"):
            raise ValueError("Invalid reconciliation state")
        with self.db() as d:
            row=d.execute("SELECT * FROM steps WHERE id=?",(sid,)).fetchone()
            if not row or row["state"] not in ("needs_reconciliation","failed","submitted"):
                raise ValueError("Step is not eligible for reconciliation")
            if next_state=="pending" and row["attempt"]>=row["max_attempt"]:
                raise ValueError("Retry budget exhausted")
            d.execute("UPDATE steps SET state=?,updated_at=? WHERE id=?",(next_state,timestamp(),sid))
            self.event(d,row["workflow_id"],sid,"reconciled",{"next":next_state})
    def artifact(self,sid,kind,uri,note=""):
        if not uri.strip() or not kind.strip():raise ValueError("Artifact kind and location required")
        aid="art_"+uuid4().hex[:16]
        with self.db() as d:
            row=d.execute("SELECT workflow_id FROM steps WHERE id=?",(sid,)).fetchone()
            if not row:raise ValueError("Unknown step")
            d.execute("INSERT INTO stage_artifacts VALUES(?,?,?,?,?,?,?)",
                      (aid,sid,kind,uri,"unverified",note,timestamp()))
            self.event(d,row["workflow_id"],sid,"artifact_added",{"id":aid})
        return aid
    def verify(self,sid,artifact_id,accepted=False):
        if not accepted:raise ValueError("Explicit artifact acceptance required")
        with self.db() as d:
            step=d.execute("SELECT * FROM steps WHERE id=?",(sid,)).fetchone()
            if not step or step["state"]!="awaiting_verification":
                raise ValueError("Execution not ready for evidence acceptance")
            art=d.execute("SELECT id FROM stage_artifacts WHERE id=? AND step_id=?",(artifact_id,sid)).fetchone()
            if not art:raise ValueError("Artifact not part of this step")
            d.execute("UPDATE stage_artifacts SET status='accepted' WHERE id=?",(artifact_id,))
            d.execute("UPDATE steps SET state='verified',updated_at=? WHERE id=?",(timestamp(),sid))
            self.event(d,step["workflow_id"],sid,"verified",{"artifact_id":artifact_id})
    def snapshot(self):
        with self.db() as d:
            workflows=[dict(x) for x in d.execute("SELECT * FROM workflows ORDER BY created_at")]
            steps=[dict(x) for x in d.execute("SELECT * FROM steps ORDER BY created_at")]
            artifacts=[dict(x) for x in d.execute("SELECT * FROM stage_artifacts ORDER BY created_at")]
        return {"workflows":workflows,"steps":steps,"artifacts":artifacts}
