@echo off
title Item Farming Bot v2 (hidden)
cd /d "%~dp0"

REM ===== Administrator check =====
REM Not using "net session": it needs the Server service (LanmanServer).
REM On a PC with that service off the check never passes and the script
REM relaunches itself forever, which looks like the screen flickering.
REM %1 = --elevated means we already asked once. Never ask twice.
powershell -NoProfile -Command "exit ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"
if %errorlevel%==1 goto :is_admin
if "%~1"=="--elevated" (
    echo [!] Could not get Administrator rights - running as normal user.
    echo     Key presses may not reach the game.
    timeout /t 3 >nul
    goto :is_admin
)
echo Requesting Administrator rights...
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '--elevated' -Verb RunAs"
exit /b
:is_admin

REM Find pythonw (no console window)
where pyw >nul 2>&1
if %errorlevel%==0 (set PYW=pyw) else (set PYW=pythonw)

start "" %PYW% bot\stone_main_v2.py
exit
