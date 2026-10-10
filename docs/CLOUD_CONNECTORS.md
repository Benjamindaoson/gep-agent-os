# Live cloud CLI adapters

Use pre-authenticated official CLIs on your own device. GEP **never stores**
their API keys.

```bash
gep cloud-status
gep vercel-preview --workspace /absolute/repository --approve
gep runpod-list
gep runpod-start POD_ID --approve
gep workspace-backup --repo /path/to/code --archive /persistent/backup.tar.gz
gep runpod-stop POD_ID --data-backed-up --approve
```

A Vercel preview deployment is requested, not verified; check the returned
URL and HTTP health separately. Runpod startup may incur GPU/storage costs;
explicit user approval is mandatory. Stopping a Pod may still incur storage
charges and can strand machine-local storage; do not treat stop as data backup.
GEP will not automatically create or delete GPU resources in this first
connector because cost and storage placement must be checked against
provider pricing and the user's explicit budget.

See [Vercel deployment docs](https://vercel.com/docs/deployments/overview) and
[Runpod CLI Pod docs](https://docs.runpod.io/runpodctl/reference/runpodctl-remove-pods).
Runpod's API is evolving; using its official CLI avoids hardcoding soon-to-be
retired API v1 endpoints.
