$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11), 'Benötigt wird Python 3.11.'"
    & py -3.11 -m venv .venv
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c "import sys; assert sys.version_info[:2] == (3, 11), 'Benötigt wird Python 3.11.'"
    & python -m venv .venv
} else {
    throw "Python 3.11 wurde nicht gefunden. Bitte Python 3.11 von python.org installieren."
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[dev]"

Write-Host "Installation abgeschlossen. Start mit: start-windows.cmd" -ForegroundColor Green
