param(
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "=== ChatBI Sprint 6 - Canary/Rollback Drill ===" -ForegroundColor Cyan

if (-not $SkipTests) {
    Write-Host "`n1) Validacao automatica de gate de canary e dominio" -ForegroundColor Yellow
    python -m pytest `
      backend/tests/test_chat_canary_gate.py `
      backend/tests/test_playground_mode.py `
      backend/tests/llmops/test_domain_eval_gate.py -q
} else {
    Write-Host "`n1) Testes pulados (--SkipTests)." -ForegroundColor DarkYellow
}

Write-Host "`n2) Ativacao de canary (piloto)" -ForegroundColor Yellow
Write-Host "   - CHAT_CANARY_ENABLED=true" -ForegroundColor Gray
Write-Host "   - CHAT_CANARY_ALLOWED_ROLES=admin" -ForegroundColor Gray
Write-Host "   - CHAT_CANARY_ALLOWED_USERS=usuario.teste" -ForegroundColor Gray

Write-Host "`n3) Evidencia operacional minima" -ForegroundColor Yellow
Write-Host "   - Usuario fora do canary recebe 403 em /api/v1/chat/stream-token" -ForegroundColor Gray
Write-Host "   - Usuario no canary acessa /api/v1/chat/stream-token com 200" -ForegroundColor Gray
Write-Host "   - /api/v1/admin/dashboard/chat-slo sem degradacao de SLO apos 24h" -ForegroundColor Gray

Write-Host "`n4) Rollback imediato (drill)" -ForegroundColor Yellow
Write-Host "   - CHAT_CANARY_ENABLED=false (liberacao total) OU ajustar allowlist." -ForegroundColor Gray
Write-Host "   - Reimplantar ultima tag estavel se houver regressao funcional." -ForegroundColor Gray
Write-Host "   - Reexecutar: scripts/chatbi_phase3_checklist.ps1" -ForegroundColor Gray

Write-Host "`nDrill concluido." -ForegroundColor Green
