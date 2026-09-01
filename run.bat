@echo off
chcp 65001 >nul
title Item Farming Bot
cd /d "%~dp0"

REM ===== Need Administrator rights (else key input won't reach the game) =====
net session >nul 2>&1
if not %errorlevel%==0 (
    echo Requesting Administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Find Python
py --version >nul 2>&1
if %errorlevel%==0 (set PY=py) else (set PY=python)

%PY% bot\stone_main.py

echo.
echo (Bot stopped) Press any key to close
pause >nul
