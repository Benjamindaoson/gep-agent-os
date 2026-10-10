"""Read-only, portable local Git work context for project handoffs.

Captures hashes and paths, never file contents, diffs, remotes, or credentials.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _git(path: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", path, *args],
        capture_output=True, text=True, timeout=15, check=False
    )
    if result.returncode:
        raise ValueError("Cannot inspect Git workspace: " + (result.stderr.strip() or "git failed"))
    return result.stdout.rstrip("\\r\\n")


def inspect_repo(path: str | Path) -> dict:
    """Describe the code state without modifying a repo or copying private code."""
    selected = str(Path(path).expanduser().resolve())
    root = _git(selected, "rev-parse", "--show-toplevel")
    head = _git(selected, "rev-parse", "HEAD")
    branch = _git(selected, "branch", "--show-current") or "(detached HEAD)"
    status = _git(selected, "status", "--porcelain=v1", "--untracked-files=normal")
    changes = status.splitlines() if status else []
    return {
        "workspace_path": root,
        "commit_sha": head,
        "branch": branch,
        "clean": not bool(changes),
        "changed_count": len(changes),
        "untracked_count": sum(line.startswith("??") for line in changes),
        "changed_paths": [line[3:] for line in changes[:200]],
        "truncated": len(changes) > 200,
        "note": "Informational snapshot only; uncommitted code is NOT backed up."
    }
