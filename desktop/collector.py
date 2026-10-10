"""Observe local ActivityWatch aggregates and explicitly selected Git workspaces.

No screenshot, keyboard, browser URL, document title or source-code collection.
"""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.parse import quote, urlencode

class CollectionError(RuntimeError): pass

def _ms(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()*1000)

def app_seconds(events, start_ms, end_ms):
    """Conservatively clip reported window events to the chosen interval."""
    totals = {}
    for event in events:
        data = event.get("data") or {}
        app = str(data.get("app") or "unknown").strip()[:180]
        if not app: app = "unknown"
        try:
            start = _ms(event["timestamp"])
            duration = max(0, int(float(event.get("duration", 0))*1000))
        except (KeyError, ValueError, TypeError, OverflowError):
            continue
        overlap = max(0, min(end_ms, start+duration)-max(start_ms,start))
        if overlap:
            totals[app] = totals.get(app, 0) + overlap
    return {app: min((end_ms-start_ms)//1000, ms//1000)
            for app,ms in totals.items() if ms >= 1000}

class ActivityWatchCollector:
    def __init__(self, url="http://127.0.0.1:5600"):
        if url.rstrip("/") not in ("http://127.0.0.1:5600","http://localhost:5600"):
            raise ValueError("Only loopback ActivityWatch is allowed")
        self.url=url.rstrip("/")
    def _get(self, path):
        try:
            with urlopen(self.url+path,timeout=5) as response:
                return json.load(response)
        except (OSError, ValueError) as e:
            raise CollectionError("ActivityWatch is not running on this computer") from e
    def collect(self,start_ms,end_ms):
        if end_ms<=start_ms or end_ms-start_ms>24*3600*1000:
            raise ValueError("Invalid ActivityWatch collection window")
        buckets = self._get("/api/0/buckets/")
        totals = {}
        for bucket in buckets:
            if not bucket.startswith("aw-watcher-window_"):
                continue
            params = urlencode({
                "start": datetime.fromtimestamp(start_ms/1000,timezone.utc).isoformat(),
                "end": datetime.fromtimestamp(end_ms/1000,timezone.utc).isoformat(),
                "limit": 10000})
            raw = self._get("/api/0/buckets/"+quote(bucket,safe="")+"/events?"+params)
            if not isinstance(raw,list):
                continue
            for app, seconds in app_seconds(raw,start_ms,end_ms).items():
                totals[app] = min((end_ms-start_ms)//1000,
                                  totals.get(app,0)+seconds)
        return [{"start_ms":start_ms,"end_ms":end_ms,"kind":"app",
                 "identifier":app,"seconds":seconds}
                for app,seconds in sorted(totals.items()) if seconds>0]

def git_status(directory):
    """Read metadata only, without collecting filenames or repository contents."""
    root=Path(directory).expanduser().resolve()
    if not root.is_dir():raise CollectionError("Git directory is missing")
    def git(*args):
        try:
            result=subprocess.run(["git","-C",str(root),*args],capture_output=True,
                                  text=True,timeout=15,check=False)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise CollectionError("Git unavailable") from exc
        if result.returncode:raise CollectionError("Not an accessible Git repository")
        return result.stdout.strip()
    repository=Path(git("rev-parse","--show-toplevel")).name[:180]
    branch=git("branch","--show-current")[:55] or "detached"
    sha=git("rev-parse","--short","HEAD")[:16]
    dirty=bool(git("status","--porcelain","--untracked-files=normal"))
    return {"repository":repository,"detail":f"branch:{branch} commit:{sha} dirty:{str(dirty).lower()}"[:200]}

def git_observations(paths,start_ms,end_ms):
    results=[]
    for path in paths:
        try:
            info=git_status(path)
        except CollectionError:
            continue
        results.append({"start_ms":start_ms,"end_ms":end_ms,"kind":"git",
                        "identifier":info["repository"],"seconds":0,
                        "detail":info["detail"]})
    return results
