param(
  [string]$GodotBin = $env:GODOT_BIN,
  [switch]$WithExport = $false,
  [switch]$IncludeDemo = $false,
  [switch]$WithCoverage = $false,
  [int]$PerfP95Ms = 0
)

$ErrorActionPreference = 'Stop'

function Run-Step($name, [ScriptBlock]$block) {
  Write-Host "=== [$name] ==="
  try { & $block; return $LASTEXITCODE } catch { Write-Error $_; return 1 }
}

$fail = 0

# 1) dotnet tests (optionally coverage)
if ($WithCoverage) {
  $c = Run-Step 'dotnet coverage' { & "$PSScriptRoot/run_dotnet_coverage.ps1" -Solution 'Game.sln' }
} else {
  $c = Run-Step 'dotnet tests' { & "$PSScriptRoot/run_dotnet_tests.ps1" -Solution 'Game.sln' }
}
if ($c -ne 0) { $fail++ }

# 2) GdUnit4 tests (respect demo flag)
if ($IncludeDemo) { $env:TEMPLATE_DEMO = '1' }
$c = Run-Step 'GdUnit4 tests' { & "$PSScriptRoot/run_gdunit_tests.ps1" -GodotBin $GodotBin }
if ($IncludeDemo) { Remove-Item Env:TEMPLATE_DEMO -ErrorAction SilentlyContinue }
if ($c -ne 0) { $fail++ }

# 3) Headless smoke
$c = Run-Step 'Headless smoke' { & "$PSScriptRoot/smoke_headless.ps1" -GodotBin $GodotBin -TimeoutSec 5 }
if ($c -ne 0) { $fail++ }

# 4) Export + EXE smoke (optional)
if ($WithExport) {
  $c = Run-Step 'Export Windows EXE' { & "$PSScriptRoot/export_windows.ps1" -GodotBin $GodotBin -Output 'build/Game.exe' }
  if ($c -ne 0) { $fail++ }
  $c = Run-Step 'Smoke EXE' { & "$PSScriptRoot/smoke_exe.ps1" -ExePath 'build/Game.exe' -TimeoutSec 5 }
  if ($c -ne 0) { $fail++ }
}

# 5) Perf budget (optional)
if ($PerfP95Ms -gt 0) {
  $c = Run-Step "Perf budget <= $PerfP95Ms ms" { & "$PSScriptRoot/check_perf_budget.ps1" -MaxP95Ms $PerfP95Ms }
  if ($c -ne 0) { $fail++ }
}

# Final status and smoke hint (printed last)
if ($fail -gt 0) {
  Write-Host "QUALITY GATE: FAIL ($fail)"
  $exitCode = 1
} else {
  Write-Host 'QUALITY GATE: PASS'
  $exitCode = 0
}
Write-Host 'SMOKE TIP: Prefer [TEMPLATE_SMOKE_READY] (marker), fallback [DB] opened (logs).'
exit $exitCode
