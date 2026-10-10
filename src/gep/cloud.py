"""Explicitly approved CLI adapters for existing Vercel and Runpod accounts.

No silent cloud purchases. Provider credentials stay in their CLI config.
"""
from __future__ import annotations
import shutil,subprocess
from pathlib import Path

class CloudActionError(RuntimeError):pass

def _exec(argv,cwd=None,timeout=180):
    try:
        result=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,timeout=timeout,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise CloudActionError("CLI unavailable or timed out; reconcile provider state") from e
    if result.returncode:
        raise CloudActionError("Cloud CLI exited unsuccessfully; check provider CLI logs")
    return result.stdout[-5000:]

class CloudCLI:
    def status(self):
        return {"vercel_cli_installed":shutil.which("vercel") is not None,
                "runpodctl_installed":shutil.which("runpodctl") is not None}
    def vercel_preview(self,workspace,approved=False):
        if not approved:raise ValueError("Explicit approval required for deployment")
        if not Path(workspace).is_dir():raise ValueError("Invalid workspace")
        if not shutil.which("vercel"):raise CloudActionError("Vercel CLI missing")
        output=_exec(["vercel","deploy","--yes"],cwd=str(workspace),timeout=900)
        return {"provider":"vercel","operation":"preview_deploy","status":"submitted",
                "output":output,"verification":"check deployment URL and HTTP health"}
    def runpod_list(self):
        if not shutil.which("runpodctl"):raise CloudActionError("runpodctl missing")
        return {"provider":"runpod","pods":_exec(["runpodctl","pod","list","--all"])}
    def runpod_stop(self,pod_id,approved=False,data_safe=False):
        if not approved or not data_safe:
            raise ValueError("Approve stop and confirm durable data backup first")
        if not pod_id or any(not (c.isalnum() or c in "-_") for c in pod_id):
            raise ValueError("Invalid Pod ID")
        if not shutil.which("runpodctl"):raise CloudActionError("runpodctl missing")
        return {"provider":"runpod","operation":"stop","pod_id":pod_id,
                "status":"reported_complete","output":_exec(["runpodctl","pod","stop",pod_id])}
    def runpod_start(self,pod_id,approved=False):
        if not approved:raise ValueError("Explicit approval required; GPU may incur charges")
        if not pod_id or any(not (c.isalnum() or c in "-_") for c in pod_id):
            raise ValueError("Invalid Pod ID")
        if not shutil.which("runpodctl"):raise CloudActionError("runpodctl missing")
        return {"provider":"runpod","operation":"start","pod_id":pod_id,
                "status":"submitted","output":_exec(["runpodctl","pod","start",pod_id])}
