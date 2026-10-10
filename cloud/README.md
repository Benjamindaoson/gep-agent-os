# GEP Cloud: zero-install web MVP

An independently hosted browser interface for phone, tablet and desktop.
End users do not need to install Python, Docker, an agent, or a mobile app.

## Local development

```bash
pip install -r cloud/requirements.txt
uvicorn cloud.app:app --reload
```

Then visit http://127.0.0.1:8000. Local SQLite is for development only.

## Hosting

1. Provision a managed PostgreSQL database.
2. Build Docker image from repository root using `cloud/Dockerfile`.
3. Set `GEP_ENV=production`, `DATABASE_URL`, `GEP_SESSION_SECRET` (random secret) and `GEP_ALLOWED_HOSTS` (your domain) in host secret settings.
4. Expose via HTTPS; never use SQLite on ephemeral production storage.
5. Set up migrations/backups/monitoring before public beta.

The cloud API uses strict same-site HttpOnly browser cookies, Origin checks,
per-user row filtering, protected credentials and explicit mission approval.
No third-party API keys are required for the user to register and organize
goals, projects and missions.

**Scope:** This is a working web MVP for cloud-hosted *state and manual
mission progression*. It does not yet run OpenClaw/OpenHands in the cloud
or execute autonomous tasks for customers. Device activity monitoring
requires permissioned clients; iPhone Safari cannot inspect other apps.

## Security limitations before public launch

Add production database migrations, email verification, password recovery,
login rate limits, strict TLS/proxy verification, audit retention and
background multi-tenant executor isolation before accepting outside users.
The starter UI is a functional responsive prototype, not a mature mobile app.
