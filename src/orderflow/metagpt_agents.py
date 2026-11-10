from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _metagpt_python() -> Path:
    executable = Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")
    return _project_root() / ".venv-metagpt" / executable


def metagpt_configured() -> bool:
    """Erkennt, ob die lokale Konfiguration einen echten API-Schlüssel enthält."""
    config = _project_root() / "config" / "config2.yaml"
    if not config.is_file():
        return False
    content = config.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*api_key:\s*(\S+)\s*$", content)
    if match is None:
        return False
    value = match.group(1)
    return value != "sk-demo-not-configured" and "<" not in value


@lru_cache(maxsize=1)
def metagpt_available() -> bool:
    """Prüft die isolierte MetaGPT-Laufzeit ohne den Streamlit-Prozess zu belasten."""
    python = _metagpt_python()
    if not python.is_file():
        return False

    try:
        result = subprocess.run(
            [
                str(python),
                "-c",
                "from metagpt.actions import Action; from metagpt.roles import Role",
            ],
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


async def run_metagpt_review(payload: dict[str, Any]) -> dict[str, str]:
    """Startet das MetaGPT-Review in einer getrennten, kompatiblen Python-Umgebung."""
    if not metagpt_available():
        raise RuntimeError(
            "MetaGPT ist nicht eingerichtet. Bitte das plattformspezifische Setup ausführen."
        )
    if not metagpt_configured():
        raise RuntimeError("Bitte zuerst den API-Schlüssel in config/config2.yaml eintragen.")

    worker = Path(__file__).with_name("metagpt_worker.py")
    process = await asyncio.create_subprocess_exec(
        str(_metagpt_python()),
        str(worker),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(
        process.communicate(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        timeout=120,
    )
    output = stdout.decode("utf-8", errors="replace")
    marker = "ORDERFLOW_METAGPT_RESULT="
    result_line = next(
        (line for line in reversed(output.splitlines()) if line.startswith(marker)),
        None,
    )
    if process.returncode != 0 or result_line is None:
        error = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(error or "MetaGPT hat kein auswertbares Ergebnis geliefert.")

    parsed = json.loads(result_line.removeprefix(marker))
    if not isinstance(parsed, dict):
        raise RuntimeError("MetaGPT hat ein ungültiges Ergebnisformat geliefert.")
    return {str(key): str(value) for key, value in parsed.items()}
