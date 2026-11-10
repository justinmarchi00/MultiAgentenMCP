#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "Die virtuelle Umgebung fehlt. Bitte zuerst ./scripts/setup_unix.sh ausführen." >&2
  exit 1
fi

exec .venv/bin/python -m streamlit run streamlit_app.py \
  --server.address=0.0.0.0 \
  --server.port=8501
