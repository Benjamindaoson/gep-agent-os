# Upstream source review and integration decision

Review date: 2026-10-10. This is a first-pass source/license review, not a full security or quality audit.

| Source | Pinned revision | License from repository root | Integration decision |
| --- | --- | --- | --- |
| [OpenClaw](https://github.com/openclaw/openclaw) | `0484b1373e49d6206d6ac6a22958e789cf6703c1` | MIT | Git submodule, inspect gateway/protocol, eventual opt-in tool adapter |
| [ActivityWatch](https://github.com/ActivityWatch/activitywatch) | `94eceed4190bc52c5b6104b098b66a19738b466a` | MPL-2.0 | Git submodule and read-only local HTTP adapter |
| [OpenHands / Agent Canvas](https://github.com/OpenHands/OpenHands) | `03f356c5c81aefed7afad926c54e53f75230f5f6` | MIT | Git submodule, potential opt-in coding-agent executor |
| [n8n](https://github.com/n8n-io/n8n) | not vendored | Sustainable Use License (with separate EE terms) | Do not copy source into GEP; possible external instance under appropriate terms |

All three submodules are **references to exact upstream commits**. Source checkout requires `git submodule update --init`. The GEP repository has not copied or merged their source into its own modules.

## What we checked in upstream code

- OpenClaw README and `docs/gateway/protocol.md`: a Gateway WebSocket protocol with handshake, roles, methods, scoped tool access, nodes and approvals. Direct integration must adhere to authentication and permission rules; no unverified direct API adapter has been invented here.
- ActivityWatch: repository is itself a superproject with submodules such as `aw-client`, `aw-server`, `aw-watcher-window`, `aw-watcher-afk`. Root `LICENSE.txt` specifies MPL-2.0. GEP's first adapter only queries the **local** ActivityWatch HTTP API and returns aggregate app durations, not window titles.
- OpenHands README: current Agent Canvas is a self-hosted control center supporting OpenHands, Codex, Claude Code and other backends, and local/remote/cloud agent deployment. GEP will NOT duplicate this execution layer.
- n8n `LICENSE.md`: Sustainable Use License restricts use/distribution; GEP must not copy it into a commercial offering by default. Separate n8n hosting/licensing analysis is needed before commercial integration.

## Proposed reuse boundaries

1. Keep proprietary/personal goal logic, task state, verification and orchestration policies in original `src/gep`.
2. Use **process/API adapters**, not modifications of large upstream internals, until integration requirements are tested.
3. Maintain upstream license/notice files with upstream code. Assess each dependency and nested submodule separately before distribution.
4. Do not store user secrets, personal activity titles, cloud tokens or private data in public Git repositories.
5. Test real external APIs in a separate credentialed integration environment; core CI runs offline.

## Next experiments

- ActivityWatch: run the local server, fetch real bucket events, verify event timestamps/duration handling and permissions.
- OpenClaw: small gateway test with an explicitly paired/authorized client; verify session identity and safe tool approval flow.
- OpenHands: launch one isolated, low-risk code task and collect results into GEP evidence.
- Resource workflow: link GitHub, deployment provider and cloud compute via explicit manifests; simulate outages.
