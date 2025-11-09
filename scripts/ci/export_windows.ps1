param(
  [string]$GodotBin = $env:GODOT_BIN,
  [string]$Preset = 'Windows Desktop',
  [string]$Output = 'build/Game.exe'
)

$ErrorActionPreference = 'Stop'
if (-not $GodotBin -or -not (Test-Path $GodotBin)) {
  Write-Error "GODOT_BIN is not set or file not found. Pass -GodotBin or set env var."
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Output) | Out-Null
Write-Host "Exporting $Preset to $Output"
# Backend detection message
if (Test-Path "$PSScriptRoot/../../addons/godot-sqlite") {
  Write-Host "Detected addons/godot-sqlite plugin: export will prefer plugin backend."
} else {
  Write-Host "No addons/godot-sqlite found: export relies on Microsoft.Data.Sqlite managed fallback. If runtime missing native e_sqlite3, add SQLitePCLRaw.bundle_e_sqlite3."
}
& "$GodotBin" --headless --path . --export-release "$Preset" "$Output"
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
  Write-Error "Export failed with exit code $exitCode. Ensure export templates are installed in Godot."
}

# Collect artifacts
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest = Join-Path $PSScriptRoot ("../../logs/ci/$ts/export")
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Force $Output $dest 2>$null
Write-Host "Export artifact copied to $dest"
exit $exitCode
