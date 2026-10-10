# GEP Integration Audit and Acceptance Gates — 2026-10-10

## Scope and verified baseline

Repository: `Benjamindaoson/gep-agent-os`, main at `d3b475c8850b0afc26a35877d0dc0ba8561e32ee` when audited.
GitHub Actions run `38014946134`: success, 7 unit tests. Current CI uses `submodules: false`.

### Upstream integration truth

| Upstream | Gitlink pinned | GEP runtime adapter | Real integration test | Status |
| --- | --- | --- | --- | --- |
| OpenClaw | Yes | No | No | Not connected |
| ActivityWatch | Yes | Read-only local API reader | No, mocked only | Partial |
| OpenHands | Yes | No | No | Not connected |
| n8n | No (license review only) | No | No | Not integrated |

Gitlinks do not mean sources were cloned into a running environment. No live OpenClaw Gateway, OpenHands agent, ActivityWatch server, GPU node, Vercel deploy or cross-device task was tested.

### GEP core capabilities

- SQLite: goals, projects, goal associations, tasks, evidence, resource locators, JSON handoff snapshots.
- Guardrails: project cannot become active without a goal link unless explicitly overridden; default WIP limit of two; shipped requires all tasks verified unless overridden.
- Evidence verification currently means the user sets a boolean; the actual artifact is not opened, validated or benchmarked.
- `repo-inspect`: SHA, branch, dirty/untracked paths; read-only and does not back up modifications.
- `activity-summary`: aggregates mock-tested window events from local AW API; does not yet normalize overlapping intervals or paginate beyond request limit.
- No web UI, API server, durable workflow runner, long-memory index, cloud cost controls or actual environment rehydration.

## Non-negotiable acceptance definition

Every milestone passes **three gates**:

1. **L1 Engineering:** code, unit/integration tests, errors and permission boundaries are covered.
2. **L2 End-to-end:** actual upstream service is running, output comes from real execution, logs/artifacts retained, failures injected.
3. **L3 User outcome:** reduced manual steps/recovery time, increased verified goal-aligned deliverables, with a baseline comparison.

**A green unit-test CI alone is not an L2 or L3 pass.** All percentages in UI must derive from accepted milestone evidence, not arbitrary agent estimates.

## Sequential modification roadmap

### Gate 0: Source and contract sanity

- Run `git submodule update --init upstream/activitywatch upstream/openclaw upstream/openhands` in a disposable environment.
- Check the pinned SHA of each source and nested licensing obligations.
- Determine API contract and security permissions for each adapter.
- Preserve attribution; n8n must remain an independent/external service unless licensing reviewed.

Acceptance: all three pinned sources checked out and source manifest/license report generated; clean build of GEP core and CI remains green.

### Gate 1: Observation works on a real desktop

- Install/run ActivityWatch separately on an authorized machine.
- Query actual local buckets for app duration, idle status, exclusions.
- Correct pagination/time-window overlap, idle adjustment and error messages.
- Never collect window titles, URLs, keystrokes or screenshots by default.

Acceptance: capture a real consented 2-hour session; compare app duration report against an independently checked sample; no private titles sent or persisted; disconnected AW yields an explicit error.

### Gate 2: One genuine executor

- Choose OpenClaw first for general personal tools, or OpenHands when the task is specifically code-oriented.
- Connect to a running authorized backend through a supported API/protocol.
- Persist execution ID, status, timestamp and artifact URI.
- Do not grant shell, mail, deletion or cloud-spending powers by default.

Acceptance: launch one bounded task through GEP, receive actual execution evidence, reject unauthorized actions, and verify an observable output.

### Gate 3: Durable handoff and crash recovery

- Build a persistent task state machine with run/step IDs, durable events and idempotency keys.
- Capture Git state plus backed-up uncommitted work using an explicitly authorized storage strategy.
- Store environment manifest, dataset hashes, artifact/checkpoint locations and lease/heartbeat.
- Handle ambiguous side effects through reconciliation before retry.

Acceptance: terminate a worker mid-run and continue without lost task identity or duplicate external side effects; document remaining blocked resources.

### Gate 4: Resource orchestration

- Integrate GitHub + one deployment provider + one GPU provider; no vendor-specific assumptions in the core schema.
- Track budget caps and approval, ephemeral vs persistent resources, integrity of data/weights.
- Test cloud resource change with a fresh environment.

Acceptance: launch disposable job, store checkpoint in durable storage, release the instance, restore on a different machine and verify same test output within a declared tolerance. Spending requires approval.

### Gate 5: Visible verified deliveries

- Project roadmap shows stages, goal contribution, cost, owner, execution state.
- Every gate exposes a meaningful artifact (preview/test table/video/experiment), tailored to task.
- UI must distinguish `planned`, `running`, `blocked`, `verified`, `shipped`.
- Show explicit next step and recovery blocker, not agent success claims.

Acceptance: a user can inspect proof at each stage and resume from a different device. Failure stays visible as failure.

### Gate 6: Goal-aligned personal coordination

- Goals include career, learning, health, life and exploration independently.
- Describe opportunity cost of a new project and why it advances a goal; user has final override.
- Detect drift using real activity + evidence, not activity alone; offer small reversible actions.

Acceptance: scenario with concurrent coursework, career project and health obligations; system proposes sensible schedule, identifies a diversion, and demonstrates later verified progress without violating a protected obligation.

## Metrics to collect

- `integration_success_rate`: successful authenticated real upstream calls / attempted calls.
- `end_to_end_task_success_rate`: verified outputs / assigned tasks, with confidence and task class.
- `resume_success_rate`: state recovered and verified after injected interruption / trials.
- `duplicate_side_effect_count`: count for non-idempotent operations (must be zero in test).
- `manual_setup_minutes`: time to recover an interrupted project versus baseline.
- `goal_aligned_verified_deliveries`: deliverables mapped to a user-approved goal with evidence.
- `maintenance_minutes_per_day`: time spent logging and administering GEP.
- `cloud_spend_usd`: actual cost with provider evidence, compared to budget.

## Priority

Start with **Gate 0 → Gate 1 → Gate 2**, not parallel building of three full forks. Only modify upstream internals after proving a necessary gap. Prefer adapter boundaries to minimize fork drift.

This audit is a point-in-time source review. It does not claim production deployment or an external integration pass.
