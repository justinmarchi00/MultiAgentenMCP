from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "config2.yaml"


def environment_python(name: str) -> Path:
    executable = Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")
    return ROOT / name / executable


def run(*arguments: str) -> None:
    subprocess.run(arguments, check=True, cwd=ROOT)


def require_python_311() -> None:
    if sys.version_info[:2] != (3, 11):
        raise SystemExit(
            "OrderFlow benötigt Python 3.11. Installiere diese Version und starte "
            "den Launcher erneut."
        )


def ensure_base_environment() -> Path:
    python = environment_python(".venv")
    created = not python.is_file()
    if created:
        print("Erster Start: Basisumgebung wird eingerichtet ...")
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")

    import_check = subprocess.run(
        [str(python), "-c", "import mcp, orderflow, streamlit"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if created or import_check.returncode != 0:
        run(str(python), "-m", "pip", "install", "--upgrade", "pip")
        run(str(python), "-m", "pip", "install", "-e", ".[dev]")
    return python


def metagpt_is_ready() -> bool:
    python = environment_python(".venv-metagpt")
    if not python.is_file():
        return False
    check = subprocess.run(
        [
            str(python),
            "-c",
            "from metagpt.actions import Action; from metagpt.roles import Role",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return check.returncode == 0


def ensure_metagpt(base_python: Path) -> bool:
    if metagpt_is_ready():
        return True
    print("Erster Start: Die isolierte MetaGPT-Umgebung wird eingerichtet.")
    print("Das kann abhängig von der Internetverbindung einige Minuten dauern ...")
    try:
        run(str(base_python), str(ROOT / "scripts" / "setup_metagpt.py"))
    except subprocess.CalledProcessError:
        print(
            "MetaGPT konnte nicht automatisch installiert werden. "
            "Die regelbasierte Anwendung wird trotzdem gestartet.",
            file=sys.stderr,
        )
        return False
    return metagpt_is_ready()


def configured_api_key() -> bool:
    if not CONFIG.is_file():
        return False
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("api_key:"):
            value = line.split(":", 1)[1].strip()
            return bool(value and value != "sk-demo-not-configured" and "<" not in value)
    return False


def save_api_key(api_key: str) -> None:
    if not api_key or "\n" in api_key or "\r" in api_key:
        raise ValueError("Der API-Schlüssel ist ungültig.")
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(
        "llm:\n"
        "  api_type: openai\n"
        "  model: gpt-4o-mini\n"
        "  base_url: https://api.openai.com/v1\n"
        f"  api_key: {api_key}\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        CONFIG.chmod(0o600)


def ensure_api_key(metagpt_ready: bool) -> None:
    if not metagpt_ready:
        return
    environment_key = os.getenv("OPENAI_API_KEY", "").strip()
    if environment_key:
        save_api_key(environment_key)
        print("OpenAI-API-Schlüssel wurde aus der Umgebungsvariable übernommen.")
        return
    if configured_api_key():
        return

    print("MetaGPT benötigt für seine Erklärungen einen persönlichen OpenAI-API-Schlüssel.")
    print("Der Schlüssel wird nur lokal in der ignorierten Datei config/config2.yaml gespeichert.")
    api_key = getpass.getpass(
        "API-Schlüssel eingeben oder mit Enter MetaGPT zunächst überspringen: "
    ).strip()
    if api_key:
        save_api_key(api_key)
        print("API-Schlüssel wurde lokal gespeichert.")
    else:
        print("MetaGPT bleibt deaktiviert; alle regelbasierten Funktionen sind verfügbar.")


def server_is_healthy() -> bool:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8501/_stcore/health", timeout=1
        ) as response:
            return response.status == 200
    except OSError:
        return False


def wait_until_healthy(timeout_seconds: int = 30) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if server_is_healthy():
            return True
        time.sleep(0.3)
    return False


def start_application(base_python: Path, *, open_browser: bool) -> int:
    if server_is_healthy():
        print("OrderFlow AI läuft bereits unter http://localhost:8501.")
        if open_browser:
            webbrowser.open("http://localhost:8501")
        return 0
    print("OrderFlow AI wird unter http://localhost:8501 gestartet ...")
    process = subprocess.Popen(
        [
            str(base_python),
            "-m",
            "streamlit",
            "run",
            "streamlit_app.py",
            "--server.address=0.0.0.0",
            "--server.port=8501",
        ],
        cwd=ROOT,
    )
    try:
        if wait_until_healthy() and open_browser:
            webbrowser.open("http://localhost:8501")
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            return process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Richtet OrderFlow ein und startet die Anwendung.")
    parser.add_argument("--setup-only", action="store_true")
    parser.add_argument("--skip-metagpt", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    require_python_311()
    base_python = ensure_base_environment()
    metagpt_ready = False
    if not arguments.skip_metagpt:
        metagpt_ready = ensure_metagpt(base_python)
        ensure_api_key(metagpt_ready)

    if arguments.setup_only:
        print("OrderFlow AI ist vollständig eingerichtet.")
        return
    raise SystemExit(start_application(base_python, open_browser=not arguments.no_browser))


if __name__ == "__main__":
    main()
