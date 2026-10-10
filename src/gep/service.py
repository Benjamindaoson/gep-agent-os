"""Bounded local scheduler service and read-only observation journal."""
from __future__ import annotations
import json,sqlite3,time
from datetime import datetime,timezone
from .activitywatch import ActivityWatchReader
from .runner import WorkflowWorker
from .store import GEPStore

class ObservationJournal:
    def __init__(self,path):
        self.path=str(path);GEPStore(path).initialize()
        with self.db() as d:
            d.executescript("""CREATE TABLE IF NOT EXISTS activity_imports(
                id INTEGER PRIMARY KEY AUTOINCREMENT, observed_at TEXT NOT NULL,
                window_hours INTEGER NOT NULL, app_seconds_json TEXT NOT NULL,
                event_count INTEGER NOT NULL);
            """)
    def db(self):
        d=sqlite3.connect(self.path);d.row_factory=sqlite3.Row
        return d
    def import_local(self,hours=24):
        summary=ActivityWatchReader().summary(hours)
        with self.db() as d:
            d.execute("""INSERT INTO activity_imports
              (observed_at,window_hours,app_seconds_json,event_count)
              VALUES (?,?,?,?)""",(datetime.now(timezone.utc).isoformat(),hours,
                        json.dumps(summary["app_seconds"]),summary["events"]))
        return summary
    def latest(self):
        with self.db() as d:
            row=d.execute("SELECT * FROM activity_imports ORDER BY id DESC LIMIT 1").fetchone()
        if not row:return None
        data=dict(row);data["app_seconds"]=json.loads(data.pop("app_seconds_json"))
        return data

def worker_loop(db_path,interval_seconds=15,once=False):
    if not 1<=interval_seconds<=3600:raise ValueError("Invalid poll interval")
    worker=WorkflowWorker(db_path)
    while True:
        result={"processed":worker.run_once(),"polled":worker.poll_submitted()}
        if once:return result
        try:time.sleep(interval_seconds)
        except KeyboardInterrupt:return {"stopped":"user_requested","last":result}
