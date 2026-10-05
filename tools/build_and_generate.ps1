param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$project = Join-Path $workspace 'BossShot\BossShot.uproject'
$builder = Join-Path $workspace 'BossShot\Content\Python\create_boss_arena.py'
& (Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat') BossShotEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE -NoEngineChanges
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe') $project -run=pythonscript "-script=$builder" -unattended -nullrhi -nosplash -nop4 -NoSound
exit $LASTEXITCODE
