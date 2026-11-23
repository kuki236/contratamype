[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$digestOut = Join-Path $root "artifacts\alerts\run1"
$state = Join-Path $root "artifacts\alerts\state.json"

& $python -m contratamype digest `
    --db (Join-Path $root "data\processed\contratamype.duckdb") `
    --artifacts (Join-Path $root "artifacts\2025") `
    --out $digestOut `
    --state $state `
    --since 2024-01-01
if ($LASTEXITCODE -ne 0) {
    throw "digest failed with exit code $LASTEXITCODE"
}

& (Join-Path $PSScriptRoot "send_digest.ps1") `
    -Csv (Join-Path $digestOut "alert_digest.csv") `
    -DryRun:$DryRun
