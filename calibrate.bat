@echo off
chcp 65001 >nul
title Item Farming Bot - Calibrate
cd /d "%~dp0"

REM ===== Need Administrator rights =====
net session >nul 2>&1
if not %errorlevel%==0 (
    echo Requesting Administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

py --version >nul 2>&1
if %errorlevel%==0 (set PY=py) else (set PY=python)

echo =======================================================
echo    Calibrate - capture positions and templates
echo    Keep the game open and follow the instructions
echo    (switch to the game, press keys 1-8, press 0 to finish)
echo =======================================================
echo.

%PY% bot\calibrate.py

echo.
pause
