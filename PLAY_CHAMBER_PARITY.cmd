@echo off
setlocal
cd /d "%~dp0"
python tools\open_chamber_parity.py %*
exit /b %errorlevel%
