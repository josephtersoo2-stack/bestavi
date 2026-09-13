@echo off
title Aviator Desktop Dashboard
cd /d "%~dp0"
echo Starting Aviator Desktop Dashboard...
.venv\Scripts\python.exe -m aviator_bot.main
pause
