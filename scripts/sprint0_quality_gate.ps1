param(
    [ValidateSet("report", "gate")]
    [string]$Mode = "report",
    [switch]$AllowDirtyWorkspace
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Check {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Details
    )
    $status = if ($Ok) { "PASS" } else { "FAIL" }
    [PSCustomObject]@{
        check   = $Name
        status  = $status
        details = $Details
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$results = @()

# 1) Git availability
$gitAvailable = $false
try {
    git rev-parse --is-inside-work-tree | Out-Null
    $gitAvailable = $true
} catch {
    $gitAvailable = $false
}
$results += Write-Check "git_repository" $gitAvailable "Repositório Git acessível."

# 2) Dirty workspace ratio
$tracked = @()
$dirty = @()
if ($gitAvailable) {
    $tracked = git ls-files
    $dirty = git status --porcelain
}
$trackedCount = @($tracked).Count
$dirtyCount = @($dirty).Count
$dirtyOk = ($dirtyCount -eq 0) -or [bool]$AllowDirtyWorkspace
$dirtyDetail = "Arquivos rastreados: $trackedCount | Mudanças pendentes: $dirtyCount | AllowDirtyWorkspace=$([bool]$AllowDirtyWorkspace)"
$results += Write-Check "workspace_clean" $dirtyOk $dirtyDetail

# 3) Mandatory files
$mustExist = @(
    "README.md",
    "backend/app/api/v1/endpoints/playground.py",
    "frontend-solid/src/pages/Playground.tsx",
    ".github/workflows/ci.yml",
    "scripts/chatbi_canary_rollback_drill.ps1",
    "docs/CHATBI_SPRINT6_GO_LIVE_RUNBOOK.md",
    "docs/CHATBI_PLAYBOOK_TREINAMENTO_DASHBOARD.md",
    "backend/tests/llmops/test_domain_eval_gate.py",
    "backend/tests/llmops/test_capability_targets.py"
)
foreach ($path in $mustExist) {
    $exists = Test-Path -Path $path
    $results += Write-Check "file_exists:$path" $exists "Verificação de presença de arquivo crítico."
}

# 4b) ADR coverage for decision traceability
$adrRequired = @(
    "docs/adr/ADR-001-fallback-local-playground.md",
    "docs/adr/ADR-002-router-rules-first.md",
    "docs/adr/ADR-003-risk-guardrails-playground.md",
    "docs/adr/ADR-004-rbac-capability-scoping.md",
    "docs/adr/ADR-005-dashboard-chat-first.md"
)
foreach ($adrPath in $adrRequired) {
    $exists = Test-Path -Path $adrPath
    $results += Write-Check "adr_exists:$adrPath" $exists "Rastreabilidade arquitetural obrigatória."
}

# 5) CI quality gate signal
$ciPath = ".github/workflows/ci.yml"
$ciOk = $false
$ciDetail = "Arquivo ausente."
if (Test-Path $ciPath) {
    $content = Get-Content $ciPath -Raw
    $continueOnErrorCount = ([regex]::Matches($content, "continue-on-error:\s*true")).Count
    $hasRepoGate = $content -match "sprint0_quality_gate\.ps1\s+-Mode\s+gate"
    $hasDomainGate = $content -match "test_domain_eval_gate\.py"
    $hasCapabilityGate = $content -match "test_capability_targets\.py"
    $ciOk = ($continueOnErrorCount -eq 0) -and $hasRepoGate -and $hasDomainGate -and $hasCapabilityGate
    $ciDetail = "continue-on-error=true: $continueOnErrorCount | repo_gate: $hasRepoGate | domain_gate: $hasDomainGate | capability_gate: $hasCapabilityGate"
}
$results += Write-Check "ci_blocking_quality_gate" $ciOk $ciDetail

# 6) Test config existence
$pytestExists = Test-Path "pytest.ini"
$results += Write-Check "pytest_config" $pytestExists "pytest.ini presente."

$npmPkgExists = Test-Path "frontend-solid/package.json"
$results += Write-Check "frontend_package_json" $npmPkgExists "package.json do frontend presente."

$allPassed = @($results | Where-Object { $_.status -eq "FAIL" }).Count -eq 0

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportDir = "docs"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}
$reportPath = Join-Path $reportDir "sprint0_quality_gate_$timestamp.json"
$results | ConvertTo-Json -Depth 4 | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Quality gate mode: $Mode"
Write-Host "Report: $reportPath"
Write-Host ""
$results | Format-Table -AutoSize | Out-String | Write-Host

if ($Mode -eq "gate") {
    if (-not $allPassed) {
        Write-Error "Quality gate FAIL. Corrija os itens antes de avançar."
    }
    Write-Host "Quality gate PASS."
}
