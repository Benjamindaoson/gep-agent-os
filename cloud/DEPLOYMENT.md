# Hosted GEP — deployment and real acceptance

The **customer** needs only a browser. The **operator** deploys the web service,
PostgreSQL and a worker once, and funds model calls. Optional device collectors
are separate.

## Deployment checklist

1. Use `cloud/render.yaml` as a reference Blueprint. Adjust host and
   database resource sizes and secret settings before billing.
2. Set a managed PostgreSQL database URL.
3. Set `GEP_SESSION_SECRET` (high-entropy 32+ bytes) on web.
4. Set `GEP_ALLOWED_HOSTS` to the real public hostname. Configure HTTPS.
5. Set `GEP_MODEL_API_KEY` only on worker (never browser). The default model API
   expects a compatible HTTPS chat-completions endpoint; verify provider terms.
6. Apply security hardening before external users: email confirmation, abuse
   protection, database migrations, backup/restore, audit and observability.
7. Create a goal, mission, approve it; verify the worker creates a **draft**.
   Never mark it as an executed real-world task automatically.
8. Log in from phone and laptop and check the same mission is visible.

## Honest scope

This deployment can provide zero-install web access, durable shared goal state,
a hosted AI **planning** worker and manual milestone acceptance.

It does not yet perform autonomous browser/computer tasks, payment, cloud GPU
provisioning, device-wide mobile telemetry, or guarantee long-horizon execution
across arbitrary resources. Those require sandboxed tool connectors, scoped OAuth,
secure approval infrastructure, and real staging E2E tests.
