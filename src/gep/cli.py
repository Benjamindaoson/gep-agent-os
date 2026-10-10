"""Simple local CLI for the first milestone. No background agent is running yet."""
from __future__ import annotations

import argparse
import json

from .store import GEPStore


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
    cp = subs.add_parser("checkpoint")
    cp.add_argument("project_id")
    subs.add_parser("overview")
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
        elif command == "checkpoint":
            result = {"snapshot_id": store.checkpoint(args.project_id)}
        elif command == "activity-summary":
            from .activitywatch import ActivityWatchReader
            result = ActivityWatchReader().summary(args.hours)
        else:
            result = store.overview()
    except (ValueError, OSError) as exc:
        build_parser().exit(2, f"gep: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
