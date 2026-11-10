$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Die virtuelle Umgebung fehlt. Bitte zuerst setup-windows.cmd ausführen."
}

& $VenvPython -m streamlit run streamlit_app.py `
    --server.address=0.0.0.0 `
    --server.port=8501
