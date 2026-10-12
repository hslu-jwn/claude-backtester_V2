@echo off
cd /d %~dp0
rem Stop whatever listens on port 8050 (language-independent), then start the app.
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8050 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
timeout /t 2 /nobreak >nul
.venv\Scripts\python.exe -m backtester.ui.app
