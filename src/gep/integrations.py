"""External execution providers. Never claims that provider success verifies artifacts."""
import json, os, shutil, subprocess
from urllib.parse import urlparse
from urllib.request import Request, urlopen

class IntegrationError(RuntimeError): pass

class OpenClaw:
    def status(self): return {"installed": shutil.which("openclaw") is not None}
    def launch(self, prompt, workspace):
        if not self.status()["installed"]: raise IntegrationError("Install and configure OpenClaw CLI")
        try:
            p=subprocess.run(["openclaw","agent","exec",prompt,"--cwd",workspace,"--json"],
                             cwd=workspace,text=True,capture_output=True,timeout=630)
        except (OSError,subprocess.TimeoutExpired) as e:
            raise IntegrationError("OpenClaw unavailable or timed out; reconcile remote state before retry") from e
        try: result=json.loads(p.stdout)
        except ValueError as e: raise IntegrationError("No valid OpenClaw JSON envelope") from e
        if p.returncode or not result.get("ok") or result.get("status")!="ok":
            raise IntegrationError("OpenClaw returned failure; check local logs")
        return {"status":"reported_complete","session_id":result.get("sessionId"),
                "result":str(result.get("final",""))[:16000]}

class OpenHands:
    def __init__(self):
        self.url=os.environ.get("GEP_OPENHANDS_URL","http://127.0.0.1:8000").rstrip("/")
        host=urlparse(self.url)
        if not host.hostname or host.scheme not in ("http","https"): raise ValueError("Invalid server URL")
        if host.scheme=="http" and host.hostname not in ("localhost","127.0.0.1","::1"):
            raise ValueError("Remote server must use HTTPS")
    def request(self,method,path,body=None):
        headers={"Accept":"application/json"}
        token=os.environ.get("GEP_OPENHANDS_API_KEY")
        if token: headers["X-Session-API-Key"]=token
        if body is not None: headers["Content-Type"]="application/json"
        req=Request(self.url+path, method=method,headers=headers,
                    data=json.dumps(body).encode() if body is not None else None)
        try:
            with urlopen(req,timeout=30) as resp:return json.load(resp)
        except (OSError,ValueError) as e: raise IntegrationError("OpenHands API unavailable") from e
    def status(self):
        try:return {"connected":bool(self.request("GET","/api/conversations/search?limit=1"))}
        except IntegrationError:return {"connected":False}
    def launch(self,prompt,workspace):
        response=self.request("POST","/api/conversations",{
            "workspace":{"working_dir":workspace},
            "initial_message":{"role":"user","content":[{"type":"text","text":prompt}]}})
        if not response.get("id"):raise IntegrationError("Missing conversation id")
        return {"status":"submitted","session_id":response["id"],"result":""}
    def poll(self,session):
        from uuid import UUID
        UUID(session)
        state=self.request("GET","/api/conversations/"+session)
        status=str(state.get("execution_status","unknown")).lower()
        if status in ("finished","completed"):
            final=self.request("GET","/api/conversations/"+session+"/agent_final_response")
            return {"status":"reported_complete","result":str(final.get("response",""))[:16000]}
        if status in ("failed","error","stopped"):return {"status":"failed","result":""}
        return {"status":"running","result":""}

PROVIDERS={"openclaw":OpenClaw,"openhands":OpenHands}
