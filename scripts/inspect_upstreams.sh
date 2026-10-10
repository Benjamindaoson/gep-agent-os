#!/usr/bin/env bash
set -euo pipefail
# Pin-aware checkout. Nothing is copied into GEP's original source.
for name in activitywatch openclaw openhands; do
  echo "===> Checking out upstream/$name (may be a large download)"
  git submodule update --init -- "upstream/$name"
done
echo "Upstream source is available under upstream/. Nested ActivityWatch submodules are optional."
