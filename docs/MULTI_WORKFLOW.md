# Running multiple persistent workflows

The core scheduler is database-backed; each workflow has ordered steps and optional
dependencies. Approval is required before each external execution.

```bash
gep --db gep.db workflow-add PROJECT_ID --name "Build and ship"
gep --db gep.db workflow-step WF_ID --title "Baseline" --provider openclaw \
  --instruction "Build baseline and report artifact location" --workspace /absolute/project
gep --db gep.db workflow-start WF_ID
gep --db gep.db workflow-approve STEP_ID
gep --db gep.db worker-once
gep --db gep.db worker-poll
gep --db gep.db workflows
gep --db gep.db workflow-artifact STEP_ID --kind report --uri report.json
gep --db gep.db workflow-verify STEP_ID --artifact ARTIFACT_ID --accept
gep --db gep.db dashboard
```

Run `worker-once` from a cron/Task Scheduler job only after the machine has the
authorized upstream runtime. The worker is **not** a daemon yet. A submitted
OpenHands task is queried with `worker-poll`; completed results require
separate evidence verification.

Crash recovery intentionally marks expired leased steps as
`needs_reconciliation` rather than blindly replaying actions that may have
already had side effects. Resolve them manually with `workflow-reconcile`.
`resource-plan examples/PROJECT_MANIFEST.json` produces a non-spending
recovery checklist. It is not cloud provisioning.
