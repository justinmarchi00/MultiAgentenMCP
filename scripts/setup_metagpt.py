from __future__ import annotations

import os
import subprocess
import venv
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv-metagpt"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
CONFIG = ROOT / "config" / "config2.yaml"
CONFIG_EXAMPLE = ROOT / "config" / "config2.example.yaml"

REQUIREMENT_GROUPS = [
    [
        "pydantic>=2.5,<3",
        "aiohttp==3.8.6",
        "openai~=1.39.0",
        "anthropic==0.18.1",
        "PyYAML==6.0.1",
        "loguru==0.6.0",
        "tenacity==8.2.3",
        "tiktoken==0.7.0",
        "tqdm==4.66.2",
        "numpy~=1.26.4",
        "typing-inspect==0.8.0",
        "libcst==1.0.1",
        "networkx~=3.2.1",
        "aiofiles==23.2.1",
        "gitpython==3.1.40",
        "rich==13.6.0",
        "httpx==0.27.2",
        "requests>=2.31",
        "beautifulsoup4==4.12.3",
        "fire==0.4.0",
        "typer==0.9.0",
        "python-docx==0.8.11",
        "chardet",
    ],
    [
        "pandas==2.1.1",
        "openpyxl~=3.1.5",
        "Pillow",
        "scikit-learn==1.3.2",
        "playwright>=1.26",
        "anytree",
        "gitignore-parser==0.1.9",
        "rank-bm25==0.2.2",
        "jieba==0.42.1",
        "tree-sitter~=0.23.2",
        "tree-sitter-python~=0.23.2",
        "imap-tools==1.5.0",
        "websocket-client~=1.8.0",
        "httplib2~=0.22.0",
        "redis~=5.0.0",
        "socksio~=1.0.0",
        "wrapt==1.15.0",
    ],
    [
        "google-generativeai==0.4.1",
        "zhipuai~=2.1.5",
        "dashscope~=1.19.3",
        "qianfan~=0.4.4",
        "boto3~=1.34.69",
        "spark-ai-python~=0.3.30",
        "volcengine-python-sdk[ark]~=1.0.94",
        "curl-cffi~=0.7.0",
        "websockets>=10,<12",
    ],
    [
        "nbclient==0.9.0",
        "nbformat==5.9.2",
        "ipython==8.17.2",
        "ipykernel==6.27.1",
        "ipywidgets==8.1.1",
    ],
    [
        "gymnasium==0.29.1",
        "qdrant-client==1.7.0",
        "grpcio~=1.67.0",
        "grpcio-tools~=1.62.3",
        "grpcio-status~=1.62.3",
        "protobuf~=4.25.5",
        "faiss-cpu==1.7.4",
        "meilisearch==0.21.0",
        "ta==0.10.2",
    ],
]


def run(*arguments: str) -> None:
    subprocess.run(arguments, check=True, cwd=ROOT)


def main() -> None:
    print("Erstelle isolierte MetaGPT-Laufzeit ...")
    if not PYTHON.is_file():
        venv.EnvBuilder(with_pip=True).create(VENV)
    run(str(PYTHON), "-m", "pip", "install", "--upgrade", "pip")
    run(str(PYTHON), "-m", "pip", "install", "--no-deps", "metagpt==0.8.2")
    for requirements in REQUIREMENT_GROUPS:
        run(str(PYTHON), "-m", "pip", "install", *requirements)

    if not CONFIG.exists():
        copyfile(CONFIG_EXAMPLE, CONFIG)
    run(
        str(PYTHON),
        "-c",
        "from metagpt.actions import Action; from metagpt.roles import Role; "
        "print('MetaGPT-Rollen erfolgreich geladen.')",
    )
    print(
        "MetaGPT ist einsatzbereit. Bitte den API-Schlüssel in config/config2.yaml setzen. "
        "Nicht benötigte optionale Alt-Abhängigkeiten wurden bewusst ausgelassen."
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
