@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.11 scripts\launcher.py
) else (
    python scripts\launcher.py
)
if errorlevel 1 (
    echo.
    echo Start fehlgeschlagen. Benoetigt wird Python 3.11.
    pause
)
