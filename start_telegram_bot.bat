@echo off
title Aviator Telegram Bot
cd /d "%~dp0"
echo Starting Aviator Telegram Bot Controller...
.venv\Scripts\python.exe -m aviator_bot.telegram
pause
