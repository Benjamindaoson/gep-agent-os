"""Idempotent example data to explore GEP locally without credentials."""
from __future__ import annotations
from .store import GEPStore
from .life import LifePortfolio
from .engine import WorkflowEngine

def seed(db_path):
    s=GEPStore(db_path);s.initialize()
    if s.overview()["goals"] or s.overview()["projects"]:
        raise ValueError("Demo init requires an empty database to avoid modifying personal data")
    career=s.add_goal("Build an embodied AI career","career")
    study=s.add_goal("Complete academic coursework","learning")
    health=s.add_goal("Maintain sustainable rest and health","life")
    life=LifePortfolio(db_path)
    life.plan(career,priority=1,weekly_hours=15,target="Show verified robot-learning ability")
    life.plan(study,priority=1,weekly_hours=10,protected=True)
    life.plan(health,priority=1,weekly_hours=5,protected=True)
    life.link(study,career,"supports")
    project=s.add_project("VLA demonstration",[career,study])
    s.decide_project(project,"active")
    wf=WorkflowEngine(db_path).create(project,"Baseline to final demo")
    e=WorkflowEngine(db_path)
    first=e.step(wf,"Inspect existing project","openclaw",
                 "Inspect the repository and prepare an evidence-based baseline report",
                 ".",requires_approval=True)
    e.step(wf,"Review and validate the baseline","openhands",
           "Review the baseline, tests and produce a concise verifiable report",".",
           depends_on=[first],requires_approval=True)
    return {"goals":[career,study,health],"project_id":project,"workflow_id":wf,
            "note":"Example records only. No agent is launched; all tasks remain pending."}
