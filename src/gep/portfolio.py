"""Goal alignment and conservative drift detection, with human-controlled decisions."""
from __future__ import annotations
from .store import GEPStore

def review(db_path,project_id):
    store=GEPStore(db_path);store.initialize()
    state=store.handoff(project_id)
    goals=state["goals"];tasks=state["tasks"];evidence=state["evidence"]
    verified_tasks=sum(1 for t in tasks if t["state"]=="verified")
    evidence_count=sum(1 for e in evidence if e["verified"])
    issues=[]
    if not goals:issues.append("No explicit goal contribution recorded. Decide whether to defer this project.")
    if state["project"]["state"]=="active" and not tasks:
        issues.append("Active project has no defined deliverable. Add a measurable milestone.")
    if tasks and verified_tasks==0:
        issues.append("No verified milestone yet. Activity alone is not progress evidence.")
    return {"project_id":project_id,"goal_links":[{"name":g["name"],"domain":g["domain"]} for g in goals],
            "verified_tasks":verified_tasks,"total_tasks":len(tasks),"verified_evidence":evidence_count,
            "issues":issues,"suggested_decision":"review" if issues else "continue",
            "note":"Heuristic only: no autonomous goal changes or productivity judgments."}
