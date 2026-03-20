param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$SkipPlaywright,
    [switch]$SkipLoad
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = Join-Path "docs/uat-local" $timestamp
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    $logPath = Join-Path $outputDir ("{0}.log" -f ($Name -replace "[^a-zA-Z0-9_-]", "_"))
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $nativePreferenceVariable = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
    $previousNativePreference = if ($null -ne $nativePreferenceVariable) { $nativePreferenceVariable.Value } else { $null }
    try {
        $global:PSNativeCommandUseErrorActionPreference = $false
        $output = & $Command 2>&1
        $exitCode = $LASTEXITCODE
        $output | Set-Content -Path $logPath -Encoding UTF8
        if ($exitCode -ne 0) {
            throw "Native command exited with code $exitCode"
        }
        Write-Host "[OK] $Name" -ForegroundColor Green
        return [ordered]@{
            name = $Name
            ok = $true
            log = $logPath
        }
    } catch {
        $failure = $_ | Out-String
        $failure | Set-Content -Path $logPath -Encoding UTF8
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        throw
    } finally {
        if ($null -ne $previousNativePreference) {
            $global:PSNativeCommandUseErrorActionPreference = $previousNativePreference
        } else {
            Remove-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
        }
    }
}

$summary = New-Object System.Collections.Generic.List[object]

if (-not $SkipBackend) {
    $summary.Add((Invoke-Step -Name "backend_uat_contracts" -Command {
        python -m pytest `
          backend/tests/integration/test_chat_endpoint.py `
          backend/tests/integration/test_chat_history_endpoint.py `
          backend/tests/integration/test_memory_endpoint.py `
          backend/tests/integration/test_ingest_endpoint.py `
          backend/tests/test_chat_automation_service.py `
          backend/tests/test_chatbi_deterministic_rules.py -q
    }))
}

if (-not $SkipFrontend) {
    $summary.Add((Invoke-Step -Name "frontend_typecheck" -Command {
        cmd /c "frontend-solid\\node_modules\\.bin\\tsc.cmd --noEmit -p frontend-solid/tsconfig.json"
    }))
    $summary.Add((Invoke-Step -Name "frontend_unit_tests" -Command {
        Set-Location frontend-solid
        try {
            cmd /c ".\\node_modules\\.bin\\vitest.cmd run"
        } finally {
            Set-Location $repoRoot
        }
    }))
    $summary.Add((Invoke-Step -Name "frontend_build" -Command {
        Set-Location frontend-solid
        try {
            cmd /c ".\\node_modules\\.bin\\vite.cmd build 2>&1"
        } finally {
            Set-Location $repoRoot
        }
    }))
}

if (-not $SkipPlaywright) {
    $summary.Add((Invoke-Step -Name "frontend_playwright_uat" -Command {
        Set-Location frontend-solid
        try {
            cmd /c ".\\node_modules\\.bin\\playwright.cmd test --project=chromium 2>&1"
        } finally {
            Set-Location $repoRoot
        }
    }))
}

if (-not $SkipLoad) {
    $summary.Add((Invoke-Step -Name "backend_stream_load" -Command {
        python -m pytest backend/tests/integration/test_chat_stream_load.py -q
    }))
}

$summaryPath = Join-Path $outputDir "summary.json"
$summary | ConvertTo-Json -Depth 5 | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "`nUAT local finalizado." -ForegroundColor Green
Write-Host "Evidencias salvas em: $outputDir" -ForegroundColor Green
