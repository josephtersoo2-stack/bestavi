@echo off
title Aviator Django Backend (Live Browser Host)
cd /d "%~dp0"
echo =======================================================
echo   Starting Aviator Django Backend on port 8000...
echo   Interactive Browser Mode: Enabled
echo =======================================================
cd backend
..\.venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
pause
