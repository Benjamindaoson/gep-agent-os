# Local unattended worker and opt-in observation

Run the local worker process on a secured computer or container with authorized
OpenClaw / OpenHands runtimes:

```bash
gep --db /persistent/gep.db worker-loop --interval 15
```

The worker checks previously approved workflow steps and polls submitted
OpenHands sessions. It persists state and will not blindly retry ambiguous
operations. You can run it using a trusted service manager (systemd, Windows
Task Scheduler). Keep the SQLite database on persistent storage; do not put it
on an ephemeral GPU root filesystem.

Activity observation is **opt-in**, separate from execution:

```bash
gep --db /persistent/gep.db activity-import --hours 24
gep --db /persistent/gep.db activity-latest
```

Only local ActivityWatch aggregate app time is stored; no window titles or URLs.
You may schedule the import separately. Observation does NOT assign moral or
productivity judgments to browser/IDE usage.
