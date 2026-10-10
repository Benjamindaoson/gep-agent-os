# GEP Agent OS

**Your goals, continuously advanced — not another coding agent.**

GEP is a **goal-aligned personal orchestration layer**. It helps decide whether a project deserves attention, connects it to work/learning/life goals, tracks verifiable results, and hands off execution to existing tools. It does not attempt to replace OpenClaw, Codex, GitHub, Vercel, cloud providers, or GPU services.

## Implemented in the current prototype

- A local SQLite **goal → project → task → evidence** store.
- Explicit **go/no-go project decisions** and a configurable work-in-progress limit.
- No task can be marked verified without a recorded, verified evidence reference.
- Resource registry and reproducible JSON handoff for resuming a project in a new session/device.
- Optional **read-only Git workspace inspection**: commit, branch, dirty/untracked paths, and a warning that uncommitted code still needs backup.
- Optional **read-only ActivityWatch adapter** for local, privacy-reduced activity summaries.
- Pin-based upstream Git submodules (not copied/merged code).
- Unified approved task dispatch to OpenClaw CLI or OpenHands Agent Server, with a SQLite execution ledger and polling.\n- Goal-aware execution briefs with opt-in aggregate ActivityWatch context.\n- Local read-only Mission Control dashboard (127.0.0.1 only).\n- Unit tests and CI.

These are **working integration adapters and local orchestration foundations**, not a fully deployed autonomous personal assistant. Real upstream services must be installed/authenticated separately; CI tests mock upstream responses. Cross-device execution, automatic environment rebuilding, and unattended recovery remain future work.

## Try it locally (Python 3.11+)\n\n```bash\npython -m pip install -e .\ngep --db demo.sqlite demo-init\ngep --db demo.sqlite dashboard\n```\n\nOpen http://127.0.0.1:8765. The demo creates example records only and will not launch an external Agent.\n\n## Quick start (Python 3.11+)

```bash
python -m pip install -e .
gep --db ./gep.db init
gep --db ./gep.db goal-add --name "Embodied AI career" --domain career
gep --db ./gep.db project-add --name "VLA-Forge experiments" --goal GOAL_ID
gep --db ./gep.db project-start PROJECT_ID
gep --db ./gep.db task-add PROJECT_ID --name "Baseline evaluation"
gep --db ./gep.db evidence-add TASK_ID --uri "artifacts/baseline.json" --verified
gep --db ./gep.db task-verify TASK_ID
gep --db ./gep.db handoff PROJECT_ID --repo /path/to/local/git-checkout
gep --db ./gep.db repo-inspect /path/to/local/git-checkout
gep --db ./gep.db overview\n# Once official OpenClaw CLI / OpenHands server are installed and configured:\ngep --db ./gep.db integrations-status\ngep --db ./gep.db goal-run TASK_ID --provider openclaw --workspace /absolute/project/path --instruction "Deliver one testable milestone" --approve\ngep --db ./gep.db goal-run TASK_ID --provider openhands --workspace /absolute/project/path --instruction "Deliver one testable milestone" --approve\ngep --db ./gep.db runs\ngep --db ./gep.db poll-run RUN_ID\ngep --db ./gep.db dashboard --port 8765
python -m unittest discover -s tests -v
```

Replace the IDs with those printed by the CLI. `--verified` is **human-confirmed evidence** in this prototype; it is not independent machine verification.

## Review the upstream source

The submodules preserve original history/attribution without dumping large repositories into the GEP core.

```bash
git submodule update --init upstream/activitywatch
git submodule update --init upstream/openclaw
git submodule update --init upstream/openhands
```

ActivityWatch itself has nested submodules; use `git -C upstream/activitywatch submodule update --init <component>` for specific source components. OpenClaw / OpenHands are large repositories; initialize only what you intend to inspect.

- [OpenClaw](https://github.com/openclaw/openclaw) — personal agent gateway / device and tool execution.
- [ActivityWatch](https://github.com/ActivityWatch/activitywatch) — local activity observation.
- [OpenHands Agent Canvas](https://github.com/OpenHands/OpenHands) — optional coding-agent execution frontend/backend.
- [n8n](https://github.com/n8n-io/n8n) — **reference/external service only**; its source license imposes restrictions.

See [implementation status](docs/DELIVERY_STATUS.md), [worker setup](docs/SCHEDULER.md), [workspace recovery](docs/WORKSPACE_RECOVERY.md), [cloud connectors](docs/CLOUD_CONNECTORS.md), and [multi-workflow commands](docs/MULTI_WORKFLOW.md).\n\nSee [upstream review](docs/UPSTREAM_REVIEW.md), [architecture](docs/ARCHITECTURE.md), [goal-aware execution](docs/GOAL_EXECUTION_WORKFLOW.md), and [local dashboard](docs/LOCAL_DASHBOARD.md).

## Product principles

1. **A person is the unit of management**, not a single coding project.
2. **Goal relevance before execution**; work, learning, rest, and life each have legitimate standing.
3. **Observed activity is not proof of progress**.
4. **No unverified success**; preserve task state and evidence.
5. **Low user-maintenance burden** and opt-in observation.
6. **Existing tools execute**; GEP coordinates and checks.
7. **Explicit approval for external side effects** and any spending.
8. **Portable state and no vendor lock-in.**

No credentials are stored in this repository. The prototype has no browser-control or cloud-spending permissions.
