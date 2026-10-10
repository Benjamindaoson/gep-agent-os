"""Simple local CLI for the first milestone. No background agent is running yet."""
from __future__ import annotations

import argparse
import json

from .store import GEPStore
from .git_context import inspect_repo
from .ledger import RunLedger
from .workflow import run_goal_workflow
from .dashboard import serve
from .engine import WorkflowEngine
from .runner import WorkflowWorker
from .portfolio import review
from .resources import recovery_plan
from .workspace import create_snapshot,restore_snapshot
from .integrations import OpenClaw,OpenHands,IntegrationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gep", description="GEP Agent OS prototype")
    parser.add_argument("--db", default="gep.db", help="Local SQLite database path")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("init")
    goal = subs.add_parser("goal-add")
    goal.add_argument("--name", required=True)
    goal.add_argument("--domain", required=True)
    project = subs.add_parser("project-add")
    project.add_argument("--name", required=True)
    project.add_argument("--goal", action="append", default=[], help="Existing goal ID; repeatable")
    start = subs.add_parser("project-start")
    start.add_argument("project_id")
    start.add_argument("--override", action="store_true")
    start.add_argument("--wip-limit", type=int, default=2)
    change = subs.add_parser("project-state")
    change.add_argument("project_id")
    change.add_argument("--state", choices=["paused", "rejected", "shipped"], required=True)
    change.add_argument("--note", default="")
    change.add_argument("--override", action="store_true")
    task = subs.add_parser("task-add")
    task.add_argument("project_id")
    task.add_argument("--name", required=True)
    evidence = subs.add_parser("evidence-add")
    evidence.add_argument("task_id")
    evidence.add_argument("--uri", required=True)
    evidence.add_argument("--verified", action="store_true", help="Explicit human verification, not automatic")
    verify = subs.add_parser("task-verify")
    verify.add_argument("task_id")
    res = subs.add_parser("resource-add")
    res.add_argument("project_id")
    res.add_argument("--role", required=True)
    res.add_argument("--provider", required=True)
    res.add_argument("--locator", required=True)
    handoff = subs.add_parser("handoff")
    handoff.add_argument("project_id")
    handoff.add_argument("--repo", help="Optional local Git checkout to include in handoff")
    cp = subs.add_parser("checkpoint")
    cp.add_argument("project_id")
    subs.add_parser("overview")
    backup=subs.add_parser("workspace-backup")
    backup.add_argument("--repo",required=True)
    backup.add_argument("--archive",required=True)
    restore=subs.add_parser("workspace-restore")
    restore.add_argument("--archive",required=True)
    restore.add_argument("--destination",required=True)
    restore.add_argument("--approve",action="store_true")
    createwf=subs.add_parser("workflow-add")
    createwf.add_argument("project_id")
    createwf.add_argument("--name",required=True)
    addstep=subs.add_parser("workflow-step")
    addstep.add_argument("workflow_id")
    addstep.add_argument("--title",required=True)
    addstep.add_argument("--provider",choices=["openclaw","openhands"],required=True)
    addstep.add_argument("--instruction",required=True)
    addstep.add_argument("--workspace",required=True)
    addstep.add_argument("--depends-on",action="append",default=[])
    wfs=subs.add_parser("workflow-start")
    wfs.add_argument("workflow_id")
    wfp=subs.add_parser("workflow-pause")
    wfp.add_argument("workflow_id")
    approve=subs.add_parser("workflow-approve")
    approve.add_argument("step_id")
    worker=subs.add_parser("worker-once")
    subs.add_parser("worker-poll")
    subs.add_parser("workflows")
    artifact=subs.add_parser("workflow-artifact")
    artifact.add_argument("step_id")
    artifact.add_argument("--kind",required=True)
    artifact.add_argument("--uri",required=True)
    verified=subs.add_parser("workflow-verify")
    verified.add_argument("step_id")
    verified.add_argument("--artifact",required=True)
    verified.add_argument("--accept",action="store_true")
    recheck=subs.add_parser("workflow-reconcile")
    recheck.add_argument("step_id")
    recheck.add_argument("--state",choices=["pending","awaiting_verification","failed"],required=True)
    portfolio=subs.add_parser("project-review")
    portfolio.add_argument("project_id")
    resource=subs.add_parser("resource-plan")
    resource.add_argument("manifest")
    subs.add_parser("integrations-status")
    run=subs.add_parser("run-task")
    run.add_argument("task_id")
    run.add_argument("--provider",choices=["openclaw","openhands"],required=True)
    run.add_argument("--workspace",required=True)
    run.add_argument("--instruction",required=True)
    run.add_argument("--approve",action="store_true")
    check=subs.add_parser("poll-run")
    check.add_argument("run_id")
    subs.add_parser("runs")
    dash=subs.add_parser("dashboard")
    dash.add_argument("--port",type=int,default=8765)
    flow=subs.add_parser("goal-run")
    flow.add_argument("task_id")
    flow.add_argument("--provider",choices=["openclaw","openhands"],required=True)
    flow.add_argument("--workspace",required=True)
    flow.add_argument("--instruction",required=True)
    flow.add_argument("--include-activity",action="store_true")
    flow.add_argument("--approve",action="store_true")
    repo = subs.add_parser("repo-inspect")
    repo.add_argument("path", help="Path to existing local Git repository")
    activity = subs.add_parser("activity-summary")
    activity.add_argument("--hours", type=int, default=24)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    store = GEPStore(args.db)
    store.initialize()
    try:
        command = args.command
        if command == "init":
            result = {"db": args.db, "ready": True}
        elif command == "goal-add":
            result = {"goal_id": store.add_goal(args.name, args.domain)}
        elif command == "project-add":
            result = {"project_id": store.add_project(args.name, args.goal)}
        elif command == "project-start":
            store.decide_project(args.project_id, "active", wip_limit=args.wip_limit, override=args.override)
            result = {"state": "active"}
        elif command == "project-state":
            store.decide_project(args.project_id, args.state, note=args.note, override=args.override)
            result = {"state": args.state}
        elif command == "task-add":
            result = {"task_id": store.add_task(args.project_id, args.name)}
        elif command == "evidence-add":
            result = {"evidence_id": store.add_evidence(args.task_id, args.uri, args.verified)}
        elif command == "task-verify":
            store.verify_task(args.task_id)
            result = {"state": "verified"}
        elif command == "resource-add":
            result = {"resource_id": store.add_resource(args.project_id, args.role, args.provider, args.locator)}
        elif command == "handoff":
            result = store.handoff(args.project_id)
            if args.repo:
                result["git_workspace"] = inspect_repo(args.repo)
        elif command == "checkpoint":
            result = {"snapshot_id": store.checkpoint(args.project_id)}
        elif command == "workspace-backup":
            result=create_snapshot(args.repo,args.archive)
        elif command == "workspace-restore":
            result=restore_snapshot(args.archive,args.destination,args.approve)
        elif command == "workflow-add":
            result={"workflow_id":WorkflowEngine(args.db).create(args.project_id,args.name)}
        elif command == "workflow-step":
            result={"step_id":WorkflowEngine(args.db).step(args.workflow_id,args.title,args.provider,
                       args.instruction,args.workspace,args.depends_on)}
        elif command == "workflow-start":
            WorkflowEngine(args.db).start(args.workflow_id)
            result={"state":"running"}
        elif command == "workflow-pause":
            WorkflowEngine(args.db).pause(args.workflow_id)
            result={"state":"paused"}
        elif command == "workflow-approve":
            WorkflowEngine(args.db).approve(args.step_id)
            result={"approved":True}
        elif command == "worker-once":
            result=WorkflowWorker(args.db).run_once()
        elif command == "worker-poll":
            result=WorkflowWorker(args.db).poll_submitted()
        elif command == "workflows":
            result=WorkflowEngine(args.db).snapshot()
        elif command == "workflow-artifact":
            result={"artifact_id":WorkflowEngine(args.db).artifact(args.step_id,args.kind,args.uri)}
        elif command == "workflow-verify":
            WorkflowEngine(args.db).verify(args.step_id,args.artifact,args.accept)
            result={"verified":True}
        elif command == "workflow-reconcile":
            WorkflowEngine(args.db).reconcile(args.step_id,args.state)
            result={"state":args.state}
        elif command == "project-review":
            result=review(args.db,args.project_id)
        elif command == "resource-plan":
            result=recovery_plan(args.manifest)
        elif command == "integrations-status":
            result={"openclaw":OpenClaw().status(),"openhands":OpenHands().status()}
        elif command == "run-task":
            result=RunLedger(args.db).launch(args.task_id,args.provider,args.instruction,args.workspace,args.approve)
        elif command == "poll-run":
            result=RunLedger(args.db).poll(args.run_id)
        elif command == "dashboard":
            serve(args.db,args.port)
            return
        elif command == "goal-run":
            result=run_goal_workflow(args.db,args.task_id,args.provider,args.instruction,
                                     args.workspace,args.approve,args.include_activity)
        elif command == "runs":
            result=RunLedger(args.db).list()
        elif command == "repo-inspect":
            result = inspect_repo(args.path)
        elif command == "activity-summary":
            from .activitywatch import ActivityWatchReader
            result = ActivityWatchReader().summary(args.hours)
        else:
            result = store.overview()
    except (ValueError, OSError, IntegrationError) as exc:
        build_parser().exit(2, f"gep: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
