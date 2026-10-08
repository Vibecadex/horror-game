@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    set "WORKSPACE_PYTHON=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Installed Python 3.11 or newer is required. No software is installed here.
        pause
        exit /b 1
    )
    set "WORKSPACE_PYTHON=python"
)
%WORKSPACE_PYTHON% tools\workspace.py serve --open
if errorlevel 1 pause
endlocal
