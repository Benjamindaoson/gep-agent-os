"""Secure on-device state and idempotent cloud sync."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from .collector import ActivityWatchCollector, git_observations, CollectionError

SERVICE="gep-windows-companion"
ACCOUNT="device-token"
def settings_file():
    base=Path(os.environ.get("LOCALAPPDATA",str(Path.home()))) / "GEP"
    base.mkdir(parents=True,exist_ok=True)
    return base/"desktop.json"

def read_settings():
    p=settings_file()
    if not p.exists():
        return {"server":"","git_paths":[],"last_sync_ms":0,"enabled":False}
    value=json.loads(p.read_text(encoding="utf-8"))
    return {"server":value.get("server",""),
            "git_paths":value.get("git_paths",[]),
            "last_sync_ms":value.get("last_sync_ms",0),
            "enabled":bool(value.get("enabled",False))}

def save_settings(value):
    safe={k:value[k] for k in ("server","git_paths","last_sync_ms","enabled") if k in value}
    p=settings_file()
    tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(safe,indent=2),encoding="utf-8")
    tmp.replace(p)

def set_token(secret):
    import keyring
    if not secret.startswith("gep_android_"):
        raise ValueError("Paste a GEP device token from the web dashboard")
    keyring.set_password(SERVICE,ACCOUNT,secret)

def get_token():
    import keyring
    return keyring.get_password(SERVICE,ACCOUNT)

def clear_token():
    import keyring
    try:keyring.delete_password(SERVICE,ACCOUNT)
    except keyring.errors.PasswordDeleteError:pass

def validate_server(server):
    parsed=urlparse(server.rstrip("/"))
    if parsed.scheme=="https" and parsed.hostname and not parsed.username and not parsed.password:
        return server.rstrip("/")
    # Development only: loopback HTTP, never exposed as a consumer option
    if parsed.scheme=="http" and parsed.hostname in ("localhost","127.0.0.1") and os.getenv("GEP_DEV_HTTP")=="1":
        return server.rstrip("/")
    raise ValueError("Enter an HTTPS GEP server URL")

def send(server,token,payload):
    body=json.dumps(payload).encode("utf-8")
    request=Request(server+"/api/desktop/events",data=body,method="POST",
                    headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
    with urlopen(request,timeout=20) as response:
        return json.load(response)

def sync_once(collector=None,clock=None):
    config=read_settings()
    if not config["enabled"]:raise ValueError("Activity sync is paused")
    server=validate_server(config["server"])
    token=get_token()
    if not token:raise ValueError("Connect a device token first")
    now_ms=int((clock or time.time)()*1000)
    start_ms=int(config["last_sync_ms"] or (now_ms-15*60*1000))
    if now_ms<=start_ms:return {"accepted":0,"note":"Already current"}
    end_ms=min(now_ms,start_ms+24*3600*1000)
    source=collector or ActivityWatchCollector()
    events=source.collect(start_ms,end_ms)
    events+=git_observations(config["git_paths"],start_ms,end_ms)
    # Advance cursor only after server acknowledges. Retry uses same interval.
    result=send(server,token,{"events":events})
    if not isinstance(result,dict) or "accepted" not in result:
        raise RuntimeError("Cloud did not acknowledge the batch")
    config["last_sync_ms"]=end_ms
    save_settings(config)
    return {"accepted":result["accepted"],"duplicates":result.get("duplicates",0),
            "interval_start_ms":start_ms,"interval_end_ms":end_ms,
            "source_events":len(events)}
