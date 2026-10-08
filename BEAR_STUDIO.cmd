@echo off
setlocal
pushd "%~dp0"
python "%~dp0tools\launch_bear_studio.py" %*
set "BearStudioExit=%ERRORLEVEL%"
popd
if not "%BearStudioExit%"=="0" pause
exit /b %BearStudioExit%
