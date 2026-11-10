#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_COMMAND="$PYTHON"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_COMMAND="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_COMMAND="python3"
else
  echo "Python 3.11 wurde nicht gefunden. Bitte zuerst Python 3.11 installieren." >&2
  exit 1
fi

"$PYTHON_COMMAND" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Benötigt wird Python 3.11."'
"$PYTHON_COMMAND" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"

echo "Installation abgeschlossen. Start mit: ./scripts/run_unix.sh"
