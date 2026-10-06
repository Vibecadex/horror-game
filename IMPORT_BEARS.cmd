@echo off
setlocal
pushd "%~dp0"
if not defined TEDDY_TEST_TIMEOUT set "TEDDY_TEST_TIMEOUT=1800"
if not "%~1"=="" set "BEAR_SOURCE=%~1"
python "%~dp0tools\run_encounter_test.py" "%~dp0tools\import_scanned_bears.py"
set "BearImportExit=%ERRORLEVEL%"
popd
if not "%BearImportExit%"=="0" pause
exit /b %BearImportExit%
