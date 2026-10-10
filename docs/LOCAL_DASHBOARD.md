# Local GEP Mission Control

Run: `gep --db ./gep.db dashboard --port 8765`

Open http://127.0.0.1:8765 on the same computer.
`/api/status` returns current goals, projects and execution records.

The dashboard is intentionally read-only and listens on loopback only.
It does not authenticate users because it must never be exposed to a public network.
Remote/multi-device access requires an authenticated backend, TLS and proper tenancy.

This MVP dashboard shows data from the same database as GEP executors, so
running a new task updates the ledger. Restart the page to refresh the view.
It is not yet a multi-device mobile dashboard or a full project roadmap UI.
