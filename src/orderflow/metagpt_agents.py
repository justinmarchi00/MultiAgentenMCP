from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any


def friendly_metagpt_error(stderr: str) -> str:
    """Übersetzt technische MetaGPT-/OpenAI-Fehler in sichere Bedienhinweise."""
    sanitized = re.sub(
        r"sk-[A-Za-z0-9_-]{8,}",
        "[API-Schlüssel ausgeblendet]",
        stderr,
    ).strip()
    lowered = sanitized.lower()

    if any(
        marker in lowered
        for marker in (
            "token_invalidated",
            "authenticationerror",
            "incorrect api key",
            "invalid api key",
            "error code: 401",
        )
    ):
        return (
            "Der OpenAI-API-Schlüssel ist ungültig oder wurde deaktiviert. "
            "Erstelle einen neuen Schlüssel und starte den Launcher mit "
            "--replace-api-key erneut."
        )
    if "insufficient_quota" in lowered or "billing_hard_limit_reached" in lowered:
        return (
            "Das OpenAI-API-Guthaben reicht nicht aus oder das Ausgabenlimit wurde erreicht. "
            "Prüfe Guthaben und Limits im OpenAI-Platform-Konto."
        )
    if "rate limit" in lowered or "error code: 429" in lowered:
        return (
            "Das OpenAI-API-Limit wurde vorübergehend erreicht. "
            "Warte kurz und starte den Auftrag anschließend erneut."
        )
    if any(
        marker in lowered
        for marker in ("connection error", "apiconnectionerror", "name or service not known")
    ):
        return (
            "Die OpenAI-API ist nicht erreichbar. Prüfe die Internetverbindung, "
            "Firewall und Proxy-Einstellungen."
        )

    lines = [line.strip() for line in sanitized.splitlines() if line.strip()]
    detail = lines[-1] if lines else "Unbekannter Fehler im MetaGPT-Prozess."
    if len(detail) > 600:
        detail = f"{detail[:597]}..."
    return f"Der MetaGPT-Prozess ist fehlgeschlagen: {detail}"


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
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            timeout=120,
        )
    except TimeoutError as exc:
        process.kill()
        await process.wait()
        raise RuntimeError(
            "MetaGPT hat innerhalb von 120 Sekunden nicht geantwortet. "
            "Prüfe die Internetverbindung und starte den Auftrag erneut."
        ) from exc
    output = stdout.decode("utf-8", errors="replace")
    marker = "ORDERFLOW_METAGPT_RESULT="
    result_line = next(
        (line for line in reversed(output.splitlines()) if line.startswith(marker)),
        None,
    )
    if process.returncode != 0 or result_line is None:
        error = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            friendly_metagpt_error(error)
            if error
            else "MetaGPT hat kein auswertbares Ergebnis geliefert."
        )

    parsed = json.loads(result_line.removeprefix(marker))
    if not isinstance(parsed, dict):
        raise RuntimeError("MetaGPT hat ein ungültiges Ergebnisformat geliefert.")
    return {str(key): str(value) for key, value in parsed.items()}
