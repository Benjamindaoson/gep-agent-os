"""Read-only external service checks: GitHub, Vercel and Hugging Face datasets.

No automatic spending, deploying, deleting, or downloading large assets.
"""
from __future__ import annotations
import json,os
from urllib.parse import quote
from urllib.request import Request,urlopen

def _get(url,token="",authorization="Bearer"):
    headers={"Accept":"application/json","User-Agent":"gep-agent-os/0.1"}
    if token:headers["Authorization"]=authorization+" "+token
    with urlopen(Request(url,headers=headers),timeout=15) as response:
        return json.load(response)

def github_repo(owner,repo,token=None):
    for name in (owner,repo):
        if not name or "/" in name or name in (".",".."):raise ValueError("Invalid owner/repo")
    raw=_get("https://api.github.com/repos/"+quote(owner)+"/"+quote(repo),token or os.getenv("GITHUB_TOKEN",""),"Bearer")
    return {"provider":"github","name":raw.get("full_name"),"default_branch":raw.get("default_branch"),
            "visibility":raw.get("visibility"),"updated_at":raw.get("updated_at")}

def vercel_project(project_id,token=None):
    key=token or os.getenv("VERCEL_TOKEN","")
    if not key:raise ValueError("Set VERCEL_TOKEN (read-only project query)")
    raw=_get("https://api.vercel.com/v9/projects/"+quote(project_id,safe=""),key)
    return {"provider":"vercel","id":raw.get("id"),"name":raw.get("name"),
            "framework":raw.get("framework")}

def huggingface_dataset(identifier):
    if not identifier or "/" not in identifier:raise ValueError("Use namespace/dataset")
    raw=_get("https://huggingface.co/api/datasets/"+quote(identifier,safe="/"))
    return {"provider":"huggingface","id":raw.get("id"),"sha":raw.get("sha"),
            "downloads":raw.get("downloads")}
