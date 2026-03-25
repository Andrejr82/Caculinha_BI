Param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== ChatBI Fase 3 Checklist Executavel ===" -ForegroundColor Cyan

Write-Host "`n1) Regressao LLMOps (dataset versionado)" -ForegroundColor Yellow
python backend/scripts/run_llmops_regression.py
python backend/scripts/run_operational_precision_eval.py

if (-not $SkipTests) {
    Write-Host "`n2) Testes de contrato Fase 3" -ForegroundColor Yellow
    python -m pytest `
      backend/tests/test_phase3_llmops_regression.py `
      backend/tests/llmops/test_operational_precision_gate.py `
      backend/tests/test_chat_service_phase3_output.py -q
} else {
    Write-Host "`n2) Testes pulados (--SkipTests)." -ForegroundColor DarkYellow
}

Write-Host "`n3) Validacao de configuracao Canary ChatBI" -ForegroundColor Yellow
Write-Host "   - CHAT_CANARY_ENABLED" -ForegroundColor Gray
Write-Host "   - CHAT_CANARY_ALLOWED_ROLES" -ForegroundColor Gray
Write-Host "   - CHAT_CANARY_ALLOWED_USERS" -ForegroundColor Gray

Write-Host "`nChecklist Fase 3 concluido." -ForegroundColor Green
