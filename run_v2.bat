@echo off
title Item Farming Bot v2 (hidden)
cd /d "%~dp0"

REM ===== Need Administrator rights (else key input won't reach the game) =====
net session >nul 2>&1
if not %errorlevel%==0 (
    echo Requesting Administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Find pythonw (no console window)
where pyw >nul 2>&1
if %errorlevel%==0 (set PYW=pyw) else (set PYW=pythonw)

start "" %PYW% stone_main_v2.py
exit
