@echo off
title Aviator Bot Full-Stack Launcher
cd /d "%~dp0"

echo =======================================================
echo   AVIATOR AUTO-STAKE BOT: FULL-STACK LAUNCHER
echo   - Backend: Django REST Framework + PostgreSQL
echo   - Frontend: React Admin Control Center (Vite)
echo =======================================================
echo.

:: 1. Apply database migrations
echo [1/3] Checking PostgreSQL migrations...
.venv\Scripts\python.exe backend\manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PostgreSQL migration failed. Please ensure PostgreSQL is running.
    pause
    exit /b 1
)

:: 2. Start Django Backend Server in new console
echo [2/3] Starting Django Backend server on port 8000...
start "Aviator Django Backend" cmd /k "cd backend && ..\.venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 config.asgi:application"

:: 3. Start React Admin Frontend
echo [3/3] Starting React Admin Frontend on port 5173...
start "Aviator React Frontend" cmd /k "cd frontend && npm run dev -- --host 0.0.0.0"

echo.
echo =======================================================
echo   Services are running!
echo   Opening React Admin Dashboard: http://localhost:5173
echo =======================================================
timeout /t 3 >nul
start http://localhost:5173

pause
