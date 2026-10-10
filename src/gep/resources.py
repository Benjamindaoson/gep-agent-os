"""Provider-neutral resource manifests, checksums and recovery planning.

Never auto-spend or provision. Credentials are environmental, not serialized.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROLE_SET={"code","frontend","backend","database","gpu","storage","dataset","artifact"}
def load_manifest(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not isinstance(data.get("resources"),dict):
        raise ValueError("Project manifest must contain resource map")
    for role,info in data["resources"].items():
        if role not in ROLE_SET:raise ValueError("Unknown resource role: "+role)
        if not isinstance(info,dict) or not info.get("provider"):
            raise ValueError("Resource provider is required")
        if any("token" in k.lower() or "password" in k.lower() or "secret" in k.lower()
               for k in info):raise ValueError("Credentials must not appear in manifest")
    return data
def file_digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def recovery_plan(path):
    m=load_manifest(path)
    actions=[]
    for role,meta in m["resources"].items():
        actions.append({"role":role,"provider":meta["provider"],
                        "locator":meta.get("locator"),"persistent":bool(meta.get("persistent")),
                        "check":"verify credentials, availability, version and data integrity",
                        "ready":False})
    return {"project":m.get("project"),"resources":actions,
            "needs_approval":True,"state":"planned_not_provisioned"}
