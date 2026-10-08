@echo off
setlocal
pushd "%~dp0"
set "TEAM_RIG_RETARGET=1"
echo Checking the saved synthetic team rig and mannequin retargets in Unreal.
echo Close any running game or editor first. Fresh evidence will be saved; no map is changed.
python "%~dp0tools\run_encounter_test.py" "%~dp0tools\verify_team_rig_fixture.py"
set "TeamRigReviewExit=%ERRORLEVEL%"
popd
if not "%TeamRigReviewExit%"=="0" pause
exit /b %TeamRigReviewExit%
