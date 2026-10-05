@echo off
setlocal
pushd "%~dp0"
python "%~dp0tools\astra_setup.py" check %*
set "AstraCheckExit=%ERRORLEVEL%"
popd
echo.
pause
exit /b %AstraCheckExit%
