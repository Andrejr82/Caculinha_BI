param(
    [switch]$RunLoad,
    [switch]$SkipFrontendBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "=== ChatBI Fase 8 - Checklist Integrado de Pre-Producao ===" -ForegroundColor Cyan

Write-Host "`n1) Backend: contrato, memoria, multimodalidade, automacao e observabilidade" -ForegroundColor Yellow
python -m pytest `
  backend/tests/integration/test_chat_endpoint.py `
  backend/tests/integration/test_chat_stream_load.py `
  backend/tests/integration/test_chat_history_endpoint.py `
  backend/tests/integration/test_memory_endpoint.py `
  backend/tests/integration/test_ingest_endpoint.py `
  backend/tests/test_chat_service_memory_rag.py `
  backend/tests/test_chat_service_document_rag.py `
  backend/tests/test_chat_service_phase3_output.py `
  backend/tests/test_chat_service_observability.py `
  backend/tests/test_chat_automation_service.py `
  backend/tests/test_chat_capabilities.py `
  backend/tests/test_content_safety.py `
  backend/tests/test_admin_dashboard_chat_slo.py `
  backend/tests/llmops/test_domain_eval_gate.py `
  backend/tests/llmops/test_operational_precision_gate.py `
  backend/tests/llmops/test_capability_targets.py -q

Write-Host "`n2) Frontend: typecheck e build" -ForegroundColor Yellow
& ".\\frontend-solid\\node_modules\\.bin\\tsc.cmd" --noEmit -p frontend-solid/tsconfig.json

if (-not $SkipFrontendBuild) {
    Push-Location frontend-solid
    try {
        & ".\\node_modules\\.bin\\vite.cmd" build
    } finally {
        Pop-Location
    }
} else {
    Write-Host "   Build do frontend pulado (--SkipFrontendBuild)." -ForegroundColor DarkYellow
}

Write-Host "`n3) Canary e rollback drill" -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File scripts/chatbi_canary_rollback_drill.ps1

if ($RunLoad) {
    Write-Host "`n4) Carga homologatoria" -ForegroundColor Yellow
    $previous = $env:RUN_LOAD_TESTS
    $env:RUN_LOAD_TESTS = "1"
    try {
        python -m pytest backend/tests/integration/test_chat_stream_load.py backend/tests/load/test_chat_stream_homologation.py -q
    } finally {
        $env:RUN_LOAD_TESTS = $previous
    }
} else {
    Write-Host "`n4) Carga homologatoria pulada. Use -RunLoad para executar." -ForegroundColor DarkYellow
}

Write-Host "`nChecklist integrado concluido." -ForegroundColor Green
