# GEP: one goal-aware execution workflow

Live integration pipeline:

1. Read a specific task, the project it belongs to, and **all** linked goals.
2. Optionally read consented 24-hour local ActivityWatch app aggregates
   (`--include-activity`; do not collect titles or URLs).
3. Construct a bounded, goal-aware execution brief.
4. Call OpenClaw CLI or OpenHands Agent Server via the integration adapter.
5. Persist provider, execution run ID, upstream session ID, and reported result.
6. Expose status for resumption; require separate artifact verification before
   declaring the task complete.

```bash
python -m pip install -e .
gep --db state.sqlite integrations-status
gep --db state.sqlite goal-run TASK_ID \
  --provider openclaw --workspace /path/to/project \
  --instruction "Complete one accepted milestone and list artifacts" --approve
# Add --include-activity ONLY on an authorized ActivityWatch-equipped machine.
gep --db state.sqlite runs
gep --db state.sqlite poll-run RUN_ID
```

OpenClaw must be installed, configured, and authenticated on the runner host.
OpenHands must have a live authenticated Agent Server and configured model.
Do not store secrets inside GEP project records.

## Validation boundary

Unit tests use mocks and prove the pipeline's data wiring, not real upstream
success. To obtain a genuine live integration gate, run an actual agent and
check the upstream execution ID, artifact location, and independently verified
test evidence. Never infer task completion from `reported_complete`.

## Current limits

GEP does not run continuously as a daemon, copy local file systems across
devices, provision GPU hosts, deploy Vercel automatically, verify arbitrary
agent-generated artifacts, or exercise OpenHands and OpenClaw live in CI.
