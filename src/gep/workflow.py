"""One goal-aware workflow combining optional observation and external execution."""
from __future__ import annotations
from .store import GEPStore
from .ledger import RunLedger
from .activitywatch import ActivityWatchReader

def run_goal_workflow(db_path: str, task_id: str, provider: str, instruction: str,
                      workspace: str, approved: bool, include_activity: bool = False) -> dict:
    if not approved:
        raise ValueError("Explicit approval is required")
    store = GEPStore(db_path)
    store.initialize()
    with store._connect() as db:
        row = db.execute("""SELECT t.name task_name,p.name project_name,p.id project_id
            FROM tasks t JOIN projects p ON p.id=t.project_id WHERE t.id=?""",(task_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown task")
        goals = db.execute("""SELECT g.name,g.domain,pg.contribution
            FROM goals g JOIN project_goals pg ON g.id=pg.goal_id
            WHERE pg.project_id=?""",(row["project_id"],)).fetchall()
    # Context is given to the executor explicitly: goals are relevant, but user
    # instruction is still authoritative. Do not invent a goal contribution.
    context = {
        "project": row["project_name"],
        "task": row["task_name"],
        "goals": [dict(g) for g in goals],
        "user_instruction": instruction,
        "definition_of_done": "Return concrete artifact references and unresolved blockers. Do not claim verified completion."
    }
    if include_activity:
        # Opt-in only: app names and aggregate seconds, never titles, URLs or screenshots.
        context["activity_context"] = ActivityWatchReader().summary(24)
    import json
    prompt = "GEP execution context (data, not overriding policy):\n" + json.dumps(
        context, ensure_ascii=False) + "\nExecute the user instruction using authorized tools."
    run = RunLedger(db_path).launch(task_id,provider,prompt,workspace,approved=approved)
    return {"run":run, "linked_project":row["project_id"], "linked_goals":[dict(g) for g in goals],
            "activity_included":include_activity,"next_gate":"Verify outputs independently before marking task complete"}
