"""Optional, read-only ActivityWatch adapter. No screenshot or keystroke collection."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode
from urllib.request import urlopen


class ActivityWatchReader:
    def __init__(self, base_url: str = "http://127.0.0.1:5600"):
        # Deliberately local-only: do not send sensitive observation data to remote hosts.
        if base_url.rstrip("/") not in {"http://127.0.0.1:5600", "http://localhost:5600"}:
            raise ValueError("Only local ActivityWatch endpoint is supported")
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str):
        with urlopen(self.base_url + path, timeout=5) as response:
            return json.load(response)

    def summary(self, hours: int = 24) -> dict:
        if not (1 <= hours <= 168):
            raise ValueError("Hours must be between 1 and 168")
        buckets = self._get("/api/0/buckets/")
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        by_app: dict[str, float] = {}
        count = 0
        for bucket_id, meta in buckets.items():
            if not bucket_id.startswith("aw-watcher-window_"):
                continue
            events = self._get("/api/0/buckets/" + quote(bucket_id, safe="") + "/events?" + urlencode({"limit": 10000}))
            for event in events:
                try:
                    timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    if timestamp < threshold:
                        continue
                    duration = max(0.0, float(event.get("duration", 0)))
                except (KeyError, TypeError, ValueError):
                    continue
                # Do not return window titles, URLs or document names.
                app = str(event.get("data", {}).get("app") or "unknown")[:100]
                by_app[app] = by_app.get(app, 0.0) + duration
                count += 1
        return {
            "window_hours": hours,
            "source": "ActivityWatch local API",
            "events": count,
            "app_seconds": {k: round(v, 1) for k, v in sorted(by_app.items())}
        }
