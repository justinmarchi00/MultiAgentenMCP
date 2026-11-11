@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.11 scripts\launcher.py --setup-only %*
) else (
    python scripts\launcher.py --setup-only %*
)
if errorlevel 1 pause
