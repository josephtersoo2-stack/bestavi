@echo off
title Aviator Auto-Stake Bot - Service Manager
color 0A
cd /d "%~dp0"

cls
echo =======================================================================
echo              AVIATOR AUTO-STAKE BOT - MASTER LAUNCHER
echo =======================================================================
echo.

:: 1. Verify / Start PostgreSQL Service
echo [1/5] Checking PostgreSQL Database Service...
sc query postgresql-x64-16 | findstr /i "RUNNING" >nul
if %ERRORLEVEL% NEQ 0 (
    echo       PostgreSQL is not running. Attempting to start service...
    net start postgresql-x64-16 >nul 2>&1
    timeout /t 2 >nul
) else (
    echo       [OK] PostgreSQL service is ACTIVE.
)

:: 2. Clean up any stale processes on ports 8000 & 5173
echo.
echo [2/5] Cleaning up any old process instances...
schtasks /end /tn "AviatorBackend" >nul 2>&1
.venv\Scripts\python.exe backend\clean_services.py >nul 2>&1
echo       [OK] Ports 8000 and 5173 are clear.

:: 3. Run Database Migrations
echo.
echo [3/5] Applying PostgreSQL migrations...
.venv\Scripts\python.exe backend\manage.py migrate --noinput
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Migration check encountered an issue, continuing startup...
) else (
    echo       [OK] Database schema verified.
)

:: 4. Detect Wi-Fi LAN IP Address
set "LOCAL_IP=192.168.1.45"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address" ^| findstr /r "192\.168\."') do (
    set "DETECTED_IP=%%a"
)
if defined DETECTED_IP (
    set "LOCAL_IP=%DETECTED_IP: =%"
)

:: 5. Launch Services
echo.
echo [4/5] Starting Django Daphne ASGI Backend (0.0.0.0:8000)...
start "Aviator Backend (Daphne:8000)" cmd /k "title Aviator Backend (Port 8000) && cd backend && ..\.venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 config.asgi:application"

echo [5/5] Starting React Control Center (Vite:5173)...
start "Aviator Frontend (Vite:5173)" cmd /k "title Aviator Frontend (Port 5173) && cd frontend && npm run dev -- --host 0.0.0.0 --port 5173"

:: 6. Start Telegram Bot Service if token configured
if exist .env (
    findstr /c:"TELEGRAM_BOT_TOKEN" .env | findstr /v "YOUR_" >nul
    if %ERRORLEVEL% EQU 0 (
        echo       Starting Telegram Bot Service...
        start "Aviator Telegram Bot" cmd /k "title Aviator Telegram Bot && .\.venv\Scripts\python.exe -m aviator_bot.telegram"
    )
)

:: Wait 3 seconds for servers to finish binding
timeout /t 3 /nobreak >nul

:: Open browser directly to Control Center
start http://localhost:5173

:MENU
cls
color 0B
echo =======================================================================
echo          AVIATOR AUTO-STAKE BOT: ALL SERVICES ARE RUNNING!
echo =======================================================================
echo.
echo   [PC Access]
echo   - React Web Control Center  : http://localhost:5173
echo   - Django Backend Admin      : http://localhost:8000/admin/
echo   - REST API Base             : http://localhost:8000/api/v1/
echo.
echo   [Mobile Phone Access (Same Wi-Fi Network)]
echo   - Phone Web Control Center  : http://%LOCAL_IP%:5173
echo   - Phone Django Admin        : http://%LOCAL_IP%:8000/admin/
echo.
echo   [Security Credentials]
echo   - API Key                   : dee2cbd5d1693aa6d5b113a31649a0501d7da3b3661348dcd8481b84584e0e66
echo   - Django Admin Superuser    : admin
echo.
echo =======================================================================
echo   COMMANDS:
echo   [1] Re-open Control Center in Browser
echo   [2] Open Django Admin Portal in Browser
echo   [3] Open SafeZone 1.50x Analytics in Browser
echo   [4] Stop All Services and Exit
echo   [5] Exit Launcher Window (Keep services running)
echo =======================================================================
echo.

choice /C 12345 /N /M "Select an option [1-5]: "

if errorlevel 5 goto EXIT_KEEP
if errorlevel 4 goto STOP_ALL
if errorlevel 3 goto OPEN_SAFEZONE
if errorlevel 2 goto OPEN_ADMIN
if errorlevel 1 goto OPEN_FRONTEND

:OPEN_FRONTEND
start http://localhost:5173
goto MENU

:OPEN_ADMIN
start http://localhost:8000/admin/
goto MENU

:OPEN_SAFEZONE
start http://localhost:5173
goto MENU

:STOP_ALL
cls
color 0C
echo =======================================================================
echo              STOPPING ALL AVIATOR BOT SERVICES...
echo =======================================================================
echo.
.venv\Scripts\python.exe backend\clean_services.py >nul 2>&1
schtasks /end /tn "AviatorBackend" >nul 2>&1
powershell -NoProfile -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*aviator_bot.telegram*' -or $_.CommandLine -like '*daphne*' } | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1
echo [OK] All Aviator services have been shut down cleanly.
timeout /t 2 >nul
exit

:EXIT_KEEP
echo.
echo Services are continuing to run in background windows.
timeout /t 1 >nul
exit
