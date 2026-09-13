@echo off
title Best Aviator - Desktop Runner Agent
echo ============================================================
echo   Best Aviator - Local Residential Desktop Runner
echo   Connecting your local Chrome browser to Cloud Web Platform
echo ============================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m desktop_agent
) else (
    python -m desktop_agent
)

pause
