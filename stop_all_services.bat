@echo off
title Stop All Aviator Services
color 0C
cd /d "%~dp0"

echo =======================================================================
echo              STOPPING ALL AVIATOR AUTO-STAKE BOT SERVICES
echo =======================================================================
echo.

echo [1/2] Terminating Ports 8000 & 5173 and lingering browsers...
.venv\Scripts\python.exe backend\clean_services.py >nul 2>&1
schtasks /end /tn "AviatorBackend" >nul 2>&1

echo [2/2] Terminating Telegram Bot Service & Python processes...
powershell -NoProfile -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*aviator_bot.telegram*' -or $_.CommandLine -like '*daphne*' } | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1

echo.
echo =======================================================================
echo   [OK] ALL AVIATOR SERVICES HAVE BEEN STOPPED SUCCESSFULLY.
echo =======================================================================
echo.
timeout /t 3
exit
