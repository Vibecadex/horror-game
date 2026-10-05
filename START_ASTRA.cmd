@echo off
setlocal
pushd "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not on PATH. The verified installation is C:\Python314\python.exe.
  popd
  pause
  exit /b 1
)
python "%~dp0tools\astra_setup.py" start %*
set "AstraLaunchExit=%ERRORLEVEL%"
popd
if not "%AstraLaunchExit%"=="0" pause
exit /b %AstraLaunchExit%
