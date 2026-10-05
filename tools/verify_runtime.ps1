param([switch]$CaptureSequence, [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$project = Join-Path $workspace 'BossShot\BossShot.uproject'
$log = Join-Path $workspace ('evidence\runtime-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '.log')
$engineExe = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$gameArgs = @(('"' + $project + '"'), '/Game/Maps/BossArena', '-game', '-RenderOffscreen', '-ResX=1600', '-ResY=900', '-unattended', '-nosplash', '-NoSound', '-BossShotVerify', '-BossShotVerifyQuit', ('-abslog="' + $log + '"'))
if ($CaptureSequence) { $gameArgs += '-BossShotCaptureSequence' }
$process = Start-Process -FilePath $engineExe -ArgumentList $gameArgs -WorkingDirectory (Split-Path -Parent $project) -WindowStyle Hidden -PassThru
[pscustomobject]@{ProcessId=$process.Id;Log=$log;Reports=Join-Path $workspace 'BossShot\Saved\Verification'} | Format-List
