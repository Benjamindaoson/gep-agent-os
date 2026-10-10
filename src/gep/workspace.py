"""Portable Git workspace snapshots with integrity checks and explicit restore.

Snapshots are backups of approved workspace content, not full VM/container images.
Raw secrets are excluded by default; review archives before sharing.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,tarfile,io
from pathlib import Path
from datetime import datetime,timezone

EXCLUDED={".env",".env.local",".env.production","id_rsa","id_ed25519",".npmrc","credentials.json","auth.json"}
def _git(root,*args):
    p=subprocess.run(["git","-C",str(root),*args],capture_output=True,check=True)
    return p.stdout
def _safe(name):
    q=Path(name)
    return not q.is_absolute() and ".." not in q.parts and not any(p in EXCLUDED or p.startswith(".env.") for p in q.parts)
def create_snapshot(repo,archive,max_bytes=50*1024*1024):
    root=Path(repo).resolve()
    base=Path(_git(root,"rev-parse","--show-toplevel").decode().strip())
    archive=Path(archive).resolve()
    if archive.is_relative_to(base):raise ValueError("Archive must be saved outside the repository")
    tracked=_git(base,"ls-files","-z").split(b"\0")
    untracked=_git(base,"ls-files","-z","--others","--exclude-standard").split(b"\0")
    paths=[]
    for raw in tracked+untracked:
        if not raw:continue
        rel=raw.decode("utf-8","surrogateescape")
        if not _safe(rel):continue
        p=base/rel
        if p.is_file() and not p.is_symlink():paths.append((rel,p))
    total=sum(p.stat().st_size for _,p in paths)
    if total>max_bytes:raise ValueError("Workspace snapshot too large; use object storage for datasets")
    meta={"schema":"gep.workspace.v1","created_at":datetime.now(timezone.utc).isoformat(),
          "commit":_git(base,"rev-parse","HEAD").decode().strip(),
          "files":{},"excluded_secret_patterns":True}
    archive.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive,"w:gz") as tar:
        for rel,p in paths:
            content=p.read_bytes()
            meta["files"][rel]={"sha256":hashlib.sha256(content).hexdigest(),"bytes":len(content)}
            info=tarfile.TarInfo("files/"+rel);info.size=len(content);info.mode=0o600
            tar.addfile(info,io.BytesIO(content))
        content=json.dumps(meta,sort_keys=True).encode()
        info=tarfile.TarInfo("manifest.json");info.size=len(content);info.mode=0o600
        tar.addfile(info,io.BytesIO(content))
    return {"archive":str(archive),"files":len(paths),"bytes":total,
            "sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
            "warning":"Review contents before sharing; this snapshot excludes common secrets but cannot identify every secret."}
def restore_snapshot(archive,destination,approved=False):
    if not approved:raise ValueError("Explicit approval required to restore files")
    destination=Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive,"r:gz") as tar:
        mf=tar.extractfile("manifest.json")
        if mf is None:raise ValueError("Missing manifest")
        meta=json.load(mf)
        if meta.get("schema")!="gep.workspace.v1":raise ValueError("Invalid snapshot schema")
        staged=[]
        for rel,check in meta["files"].items():
            if not _safe(rel):raise ValueError("Unsafe archived path")
            member=tar.getmember("files/"+rel)
            if not member.isfile() or member.issym() or member.islnk():raise ValueError("Unsafe archive entry")
            handle=tar.extractfile(member)
            if handle is None:raise ValueError("Missing archived content")
            content=handle.read()
            if hashlib.sha256(content).hexdigest()!=check["sha256"]:
                raise ValueError("Snapshot integrity check failed")
            output=destination/rel
            if not output.resolve().is_relative_to(destination):raise ValueError("Unsafe destination")
            if output.exists():raise ValueError("Restore destination already contains "+rel)
            staged.append((output,content))
        for output,content in staged:
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(content)
    return {"restored_files":len(staged),"destination":str(destination),
            "source_commit":meta["commit"]}
