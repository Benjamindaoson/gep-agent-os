"""Persistent, verifiable GEP goal/project/task state.

This deliberately does NOT execute external tools or infer life priorities.
All start decisions and evidence verification require explicit user action.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def _new_id(prefix: str) -> str:
    return prefix + "_" + uuid4().hex[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GEPStore:
    def __init__(self, path: str | Path = "gep.db"):
        self.path = str(path)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, domain TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'proposed',
                    decision_note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_goals (
                    project_id TEXT NOT NULL REFERENCES projects(id),
                    goal_id TEXT NOT NULL REFERENCES goals(id),
                    contribution TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(project_id, goal_id)
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
                    name TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                    uri TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0,
                    kind TEXT NOT NULL DEFAULT 'artifact', created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
                    role TEXT NOT NULL, provider TEXT NOT NULL, locator TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
                    payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    def add_goal(self, name: str, domain: str) -> str:
        if not name.strip() or not domain.strip():
            raise ValueError("Goal name and domain are required")
        identity = _new_id("goal")
        with self._connect() as db:
            db.execute("INSERT INTO goals VALUES(?,?,?,?)", (identity, name, domain, _now()))
        return identity

    def add_project(self, name: str, goal_ids: list[str] | None = None) -> str:
        if not name.strip():
            raise ValueError("Project name is required")
        identity = _new_id("project")
        with self._connect() as db:
            db.execute("INSERT INTO projects VALUES(?,?,?,?,?)", (identity, name, "proposed", "", _now()))
            for goal_id in dict.fromkeys(goal_ids or []):
                db.execute("INSERT INTO project_goals(project_id,goal_id) VALUES(?,?)", (identity, goal_id))
        return identity

    def decide_project(self, project_id: str, state: str, note: str = "", wip_limit: int = 2,
                       override: bool = False) -> None:
        if state not in {"active", "paused", "rejected", "shipped"}:
            raise ValueError("Invalid project state")
        if wip_limit < 1:
            raise ValueError("WIP limit must be positive")
        with self._connect() as db:
            project = db.execute("SELECT state FROM projects WHERE id=?", (project_id,)).fetchone()
            if project is None:
                raise ValueError("Unknown project")
            if state == "active" and project["state"] != "active" and not override:
                links = db.execute("SELECT count(*) FROM project_goals WHERE project_id=?", (project_id,)).fetchone()[0]
                if not links:
                    raise ValueError("A project needs a goal link before it becomes active (or explicit override)")
                active = db.execute("SELECT count(*) FROM projects WHERE state='active'").fetchone()[0]
                if active >= wip_limit:
                    raise ValueError("WIP limit reached; pause another project or explicitly override")
            if state == "shipped" and not override:
                pending = db.execute("SELECT count(*) FROM tasks WHERE project_id=? AND state!='verified'", (project_id,)).fetchone()[0]
                total = db.execute("SELECT count(*) FROM tasks WHERE project_id=?", (project_id,)).fetchone()[0]
                if not total or pending:
                    raise ValueError("Cannot ship without all tasks verified; explicit override required")
            db.execute("UPDATE projects SET state=?, decision_note=? WHERE id=?", (state, note, project_id))

    def add_task(self, project_id: str, name: str) -> str:
        if not name.strip():
            raise ValueError("Task name is required")
        identity = _new_id("task")
        with self._connect() as db:
            db.execute("INSERT INTO tasks VALUES(?,?,?,?,?)", (identity, project_id, name, "pending", _now()))
        return identity

    def add_evidence(self, task_id: str, uri: str, verified: bool = False, kind: str = "artifact") -> str:
        if not uri.strip():
            raise ValueError("Evidence URI is required")
        identity = _new_id("ev")
        with self._connect() as db:
            db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?)",
                       (identity, task_id, uri, int(verified), kind, _now()))
        return identity

    def verify_task(self, task_id: str) -> None:
        with self._connect() as db:
            task = db.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
            if task is None:
                raise ValueError("Unknown task")
            verified = db.execute("SELECT count(*) FROM evidence WHERE task_id=? AND verified=1", (task_id,)).fetchone()[0]
            if not verified:
                raise ValueError("Task requires an explicitly verified evidence reference")
            db.execute("UPDATE tasks SET state='verified' WHERE id=?", (task_id,))

    def add_resource(self, project_id: str, role: str, provider: str, locator: str) -> str:
        if not all(part.strip() for part in (role, provider, locator)):
            raise ValueError("Resource role/provider/locator required")
        identity = _new_id("resource")
        with self._connect() as db:
            db.execute("INSERT INTO resources VALUES(?,?,?,?,?,?)",
                       (identity, project_id, role, provider, locator, _now()))
        return identity

    def handoff(self, project_id: str) -> dict:
        """A portable summary; not a VM backup or a guarantee that a tool can resume."""
        with self._connect() as db:
            project = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if project is None:
                raise ValueError("Unknown project")
            goals = db.execute(
                "SELECT g.id,g.name,g.domain,pg.contribution FROM goals g JOIN project_goals pg ON pg.goal_id=g.id WHERE pg.project_id=?",
                (project_id,)).fetchall()
            tasks = db.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY created_at,id", (project_id,)).fetchall()
            resources = db.execute("SELECT * FROM resources WHERE project_id=? ORDER BY created_at,id", (project_id,)).fetchall()
            evidence = db.execute(
                "SELECT e.* FROM evidence e JOIN tasks t ON e.task_id=t.id WHERE t.project_id=? ORDER BY e.created_at,e.id",
                (project_id,)).fetchall()
        return {
            "schema": "gep.handoff.v1", "exported_at": _now(),
            "project": dict(project), "goals": [dict(x) for x in goals],
            "tasks": [dict(x) for x in tasks], "evidence": [dict(x) for x in evidence],
            "resources": [dict(x) for x in resources],
            "next_actions": [dict(x) for x in tasks if x["state"] != "verified"]
        }

    def checkpoint(self, project_id: str) -> str:
        identity = _new_id("snapshot")
        payload = json.dumps(self.handoff(project_id), ensure_ascii=False)
        with self._connect() as db:
            db.execute("INSERT INTO snapshots VALUES(?,?,?,?)", (identity, project_id, payload, _now()))
        return identity

    def overview(self) -> dict:
        with self._connect() as db:
            goals = db.execute("SELECT * FROM goals ORDER BY created_at,id").fetchall()
            projects = db.execute("SELECT * FROM projects ORDER BY created_at,id").fetchall()
        return {"goals": [dict(x) for x in goals], "projects": [dict(x) for x in projects]}
