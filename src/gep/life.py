"""Personal goal portfolio with explicit protected commitments and WIP tradeoffs.

No surveillance or optimization based on unverified inferences.
"""
from __future__ import annotations
from .store import GEPStore
from datetime import datetime,timezone
import sqlite3

class LifePortfolio:
    def __init__(self,path="gep.db"):
        self.path=str(path);GEPStore(path).initialize()
        with self.db() as d:
            d.executescript("""
             CREATE TABLE IF NOT EXISTS goal_plans(
               goal_id TEXT PRIMARY KEY REFERENCES goals(id),
               horizon TEXT NOT NULL DEFAULT 'quarter',
               priority INTEGER NOT NULL DEFAULT 3,
               protected INTEGER NOT NULL DEFAULT 0,
               target TEXT NOT NULL DEFAULT '',weekly_hours REAL NOT NULL DEFAULT 0
             );
             CREATE TABLE IF NOT EXISTS goal_links(
               source_goal TEXT NOT NULL REFERENCES goals(id),
               target_goal TEXT NOT NULL REFERENCES goals(id),
               relation TEXT NOT NULL,
               PRIMARY KEY(source_goal,target_goal)
             );
             CREATE TABLE IF NOT EXISTS planned_allocations(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               goal_id TEXT NOT NULL REFERENCES goals(id),
               week TEXT NOT NULL,hours REAL NOT NULL CHECK(hours>=0)
             );
             """)
    def db(self):
        c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c
    def plan(self,goal_id,priority=3,protected=False,target="",weekly_hours=0,horizon="quarter"):
        if not 1<=priority<=5:raise ValueError("Priority must be 1..5")
        if weekly_hours<0 or weekly_hours>168:raise ValueError("Invalid hours")
        with self.db() as d:
            d.execute("""INSERT INTO goal_plans(goal_id,horizon,priority,protected,target,weekly_hours)
                        VALUES (?,?,?,?,?,?) ON CONFLICT(goal_id) DO UPDATE SET
                        horizon=excluded.horizon,priority=excluded.priority,
                        protected=excluded.protected,target=excluded.target,
                        weekly_hours=excluded.weekly_hours""",
                        (goal_id,horizon,priority,int(protected),target,weekly_hours))
    def link(self,source,target,relation):
        if source==target:raise ValueError("Self links are not allowed")
        if relation not in ("supports","competes","depends_on"):raise ValueError("Invalid relation")
        with self.db() as d:
            d.execute("INSERT OR REPLACE INTO goal_links VALUES(?,?,?)",(source,target,relation))
    def report(self,available_hours=40):
        if not 0<=available_hours<=168:raise ValueError("Invalid time budget")
        with self.db() as d:
            goals=[dict(g) for g in d.execute("""SELECT g.id,g.name,g.domain,p.horizon,p.priority,
                  p.protected,p.target,p.weekly_hours FROM goals g
                  LEFT JOIN goal_plans p ON g.id=p.goal_id ORDER BY COALESCE(p.priority,3) ASC""")]
            links=[dict(g) for g in d.execute("SELECT * FROM goal_links")]
            projects=[dict(x) for x in d.execute("SELECT * FROM projects WHERE state='active'")]
        budget=sum(g["weekly_hours"] or 0 for g in goals)
        protected=[g["name"] for g in goals if g["protected"]]
        return {"goals":goals,"links":links,"active_projects":projects,
          "weekly_available_hours":available_hours,"weekly_planned_hours":budget,
          "overcommitted":budget>available_hours,"protected_goals":protected,
          "warnings":(["Weekly plan exceeds discretionary time budget"] if budget>available_hours else []),
          "note":"Time budgets are user-declared. GEP does not infer effort or judge personal worth."}
