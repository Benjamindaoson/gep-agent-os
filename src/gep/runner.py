"""Worker consuming GEP workflow steps through installed upstream executors.

A reported upstream result is never a verified milestone. This process can be
restarted safely: expired in-flight work is marked for reconciliation, not retried.
"""
from __future__ import annotations
from .engine import WorkflowEngine
from .integrations import OpenClaw,OpenHands,IntegrationError

class WorkflowWorker:
    def __init__(self,db_path):
        self.engine=WorkflowEngine(db_path)
    def run_once(self):
        step=self.engine.claim()
        if step is None:return {"claimed":False}
        try:
            provider=OpenClaw() if step["provider"]=="openclaw" else OpenHands()
            result=provider.launch(step["instruction"],step["workspace"])
            self.engine.complete_execution(step["id"],step["lease_token"],
                    result["status"],run_id=result.get("session_id"),output=result.get("result",""))
        except Exception as e:
            self.engine.complete_execution(step["id"],step["lease_token"],
                 "needs_reconciliation",output=str(e)[:1000])
        return {"claimed":True,"step_id":step["id"],"state":self.step_state(step["id"])}
    def step_state(self,sid):
        with self.engine.db() as d:
            row=d.execute("SELECT state FROM steps WHERE id=?",(sid,)).fetchone()
            return row["state"] if row else "missing"
    def poll_submitted(self):
        outcomes=[]
        with self.engine.db() as d:
            active=[dict(row) for row in d.execute(
                "SELECT id,workflow_id,run_id FROM steps WHERE provider='openhands' AND state='submitted'")]
        for step in active:
            try:
                result=OpenHands().poll(step["run_id"])
                if result["status"]=="running":continue
                state="awaiting_verification" if result["status"]=="reported_complete" else "failed"
                with self.engine.db() as d:
                    d.execute("UPDATE steps SET state=?,output=?,updated_at=? WHERE id=? AND state='submitted'",
                              (state,result.get("result",""),__import__("gep.engine",fromlist=["timestamp"]).timestamp(),step["id"]))
                    self.engine.event(d,step["workflow_id"],step["id"],"polled",{"status":state})
                outcomes.append({"step_id":step["id"],"state":state})
            except Exception:
                outcomes.append({"step_id":step["id"],"state":"poll_unavailable"})
        return outcomes
