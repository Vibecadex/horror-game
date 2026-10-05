param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$engineVersionPath = Join-Path $EngineRoot 'Engine\Build\Build.version'
$version = if (Test-Path -LiteralPath $engineVersionPath) { Get-Content -LiteralPath $engineVersionPath -Raw | ConvertFrom-Json } else { $null }
$checks = [ordered]@{
    checkedAtUtc = [DateTime]::UtcNow.ToString('o')
    engineRoot = $EngineRoot
    engineVersion = $version
    editor = Test-Path -LiteralPath (Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe')
    commandlet = Test-Path -LiteralPath (Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe')
    buildTool = Test-Path -LiteralPath (Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat')
    pythonPlugin = Test-Path -LiteralPath (Join-Path $EngineRoot 'Engine\Plugins\Experimental\PythonScriptPlugin\PythonScriptPlugin.uplugin')
    editorScriptingPlugin = Test-Path -LiteralPath (Join-Path $EngineRoot 'Engine\Plugins\Editor\EditorScriptingUtilities\EditorScriptingUtilities.uplugin')
    project = Join-Path $workspace 'BossShot\BossShot.uproject'
    sourceArchiveSha256 = (Get-FileHash -LiteralPath 'C:\Projects\to-deploy\horror-scene\BossShot.zip' -Algorithm SHA256).Hash.ToLowerInvariant()
    graphics = @(Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion)
    memoryBytes = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
    freeBytes = (Get-PSDrive C).Free
}
$checks | ConvertTo-Json -Depth 6
if (-not ($checks.editor -and $checks.commandlet -and $checks.buildTool -and $checks.pythonPlugin -and $checks.editorScriptingPlugin)) { exit 1 }
