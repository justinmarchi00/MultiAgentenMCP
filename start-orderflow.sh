#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if command -v python3.11 >/dev/null 2>&1; then
  exec python3.11 scripts/launcher.py "$@"
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/launcher.py "$@"
fi

echo "Python 3.11 wurde nicht gefunden. Bitte Python 3.11 installieren." >&2
exit 1
