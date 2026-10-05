param([string]$EngineRoot)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $EngineRoot) {
    $projectSettings = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'project-settings.json') -Raw | ConvertFrom-Json
    $EngineRoot = $projectSettings.engine_root
}
$projectFile = Join-Path $projectRoot 'BossShot\BossShot.uproject'
$buildFile = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
if (-not (Test-Path -LiteralPath $projectFile) -or -not (Test-Path -LiteralPath $buildFile)) {
    throw 'The project or installed Unreal build tool is missing. Run CHECK_SETUP.cmd.'
}
$cacheRoot = Join-Path $projectRoot '.tool-cache'
foreach ($cacheName in @('temp', 'dotnet', 'nuget', 'build', 'uba')) {
    New-Item -ItemType Directory -Path (Join-Path $cacheRoot $cacheName) -Force | Out-Null
}
# These settings apply only to this build process and its children.
$env:TMP = Join-Path $cacheRoot 'temp'
$env:TEMP = $env:TMP
$env:DOTNET_CLI_HOME = Join-Path $cacheRoot 'dotnet'
$env:NUGET_PACKAGES = Join-Path $cacheRoot 'nuget'
$buildLog = Join-Path $cacheRoot 'build/UnrealBuildTool.log'
$ubaRoot = Join-Path $cacheRoot 'uba'
# UE 5.8 still uses its UBA executor with -NoUBA, but disables process detouring.
# Its trace uses UnrealBuildTool's own AppData cache, explicitly listed by the launcher.
& $buildFile BossShotEditor Win64 Development "-Project=$projectFile" -WaitMutex -NoHotReloadFromIDE -NoEngineChanges "-Log=$buildLog" "-UBARootDir=$ubaRoot" -NoUBA
exit $LASTEXITCODE
