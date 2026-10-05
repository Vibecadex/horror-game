@echo off
setlocal
pushd "%~dp0"
python "%~dp0tools\astra_setup.py" open --mode edit %*
set "BossShotLaunchExit=%ERRORLEVEL%"
popd
if not "%BossShotLaunchExit%"=="0" pause
exit /b %BossShotLaunchExit%
