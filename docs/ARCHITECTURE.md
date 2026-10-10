# GEP architecture — v0.1

## Core position

A **personal life-and-project orchestration system**. Coding agents are execution providers, not GEP's product. The root object is a *person with multiple goals*. Projects compete for finite resources and must be justified by goals or explicit user override.

```text
User goals (career / learning / life / health / exploration)
  -> Goal & portfolio decisions (go / defer / pause / ship)
    -> Projects -> tasks -> verified evidence
      -> External execution providers (OpenClaw, OpenHands, GitHub, clouds)
        -> Resource registry -> portable handoff/checkpoint -> next action
    <- Read-only observations (ActivityWatch) and user-approved evidence
```

## Implemented state model

SQLite tables: goals, projects, project_goals, tasks, evidence, resources, snapshots.

A `proposed` project cannot become `active` without an explicit goal link, except by user override. Two active projects are allowed by default. A task cannot become `verified` without verified evidence. A project cannot become `shipped` with incomplete tasks unless overridden.

These are initial **user-controlled workflow guardrails**, not universal rules about life priorities.

The handoff export contains goals, state, pending work, evidence and resource locators. It does not recreate an operating system, cloud container, model checkpoint, authentication tokens or persistent data automatically.

## Planned architecture

- **Goal Graph & Life Context**: relationships between work, learning, life and constraints, dynamic trade-offs.
- **Observation Plane**: consent-aware connectors for ActivityWatch, calendar, task providers, skills and experiments.
- **Workflow Orchestrator**: durable task DAGs, human approvals, dependency tracking, scheduling and budgets.
- **Execution Mesh**: existing remote/local agents, containers, GitHub and external APIs.
- **Artifact Verifier**: screenshots, tests, evaluation data, deployment checks, research deliverables.
- **Recovery Plane**: saved resource manifests, data snapshots, environment reconstruction and side-effect reconciliation.
- **Review UI**: visual stage artifacts, per-goal progress and explicit go/no-go decisions.

## Non-goals for v0.1

No always-on screen recording, screenshots, keystroke collection, agent shell execution, GPU purchase, automatic scheduling, cross-device file transfer or claim of autonomous end-to-end delivery.

Security boundaries: opt-in sources, least privilege, no secrets in SQLite handoff, verification before describing a step as complete, user approval on money or externally visible actions.
