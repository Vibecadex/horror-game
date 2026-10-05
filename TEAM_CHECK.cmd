@echo off
setlocal
pushd "%~dp0"
python "%~dp0tools\team_check.py" %*
set "TeddyTeamCheckExit=%ERRORLEVEL%"
popd
if not "%TeddyTeamCheckExit%"=="0" pause
exit /b %TeddyTeamCheckExit%
