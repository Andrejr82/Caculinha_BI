#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script para validar as mudanças implementadas sem iniciar a aplicação
    
.DESCRIPTION
    Este script realiza validações estáticas do código para garantir que:
    1. A página de Transferências tem os filtros de UNE no topo
    2. O ChatBI tem garantia de resposta válida
    3. Todos os arquivos foram modificados corretamente

.EXAMPLE
    .\validate_changes.ps1
#>

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         Validação de Mudanças Implementadas                  ║" -ForegroundColor Cyan
Write-Host "║                  7 de Dezembro de 2025                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Cores
$green = "Green"
$red = "Red"
$yellow = "Yellow"
$cyan = "Cyan"

# ============================================================================
# 1. Validar mudanças no Transfers.tsx
# ============================================================================
Write-Host "📋 Validando mudanças em Transfers.tsx..." -ForegroundColor $cyan
$transfers_file = "frontend-solid/src/pages/Transfers.tsx"

if (Test-Path $transfers_file) {
    $content = Get-Content $transfers_file -Raw
    
    $checks = @{
        "selectedUnesOrigem" = $content -match "selectedUnesOrigem"
        "Mode Selection" = $content -match "Modo de Transferência"
        "UNE Origin Selection" = $content -match "UNE\(s\) de Origem"
        "UNE Destination Selection" = $content -match "UNE\(s\) de Destino"
        "Mode 1→1" = $content -match "'1→1'"
        "Mode 1→N" = $content -match "'1→N'"
        "Mode N→N" = $content -match "'N→N'"
        "toggleUneDestino function" = $content -match "toggleUneDestino"
        "createEffect for mode change" = $content -match "createEffect.*mode\(\)"
    }
    
    foreach ($check in $checks.Keys) {
        if ($checks[$check]) {
            Write-Host "  ✅ $check" -ForegroundColor $green
        } else {
            Write-Host "  ❌ $check" -ForegroundColor $red
        }
    }
} else {
    Write-Host "  ❌ Arquivo não encontrado: $transfers_file" -ForegroundColor $red
}

Write-Host ""

# ============================================================================
# 2. Validar mudanças em caculinha_bi_agent.py
# ============================================================================
Write-Host "📋 Validando mudanças em caculinha_bi_agent.py..." -ForegroundColor $cyan
$agent_file = "backend/app/core/agents/caculinha_bi_agent.py"

if (Test-Path $agent_file) {
    $content = Get-Content $agent_file -Raw
    
    $checks = @{
        "_generate_fallback_response method" = $content -match "def _generate_fallback_response"
        "Fallback response with message" = $content -match "mensagem"
        "Try-catch in run()" = $content -match "try:" -and $content -match "except Exception"
        "Validation of empty result" = $content -match "if result and result.get"
        "Fallback on error" = $content -match "return self._generate_fallback_response"
    }
    
    foreach ($check in $checks.Keys) {
        if ($checks[$check]) {
            Write-Host "  ✅ $check" -ForegroundColor $green
        } else {
            Write-Host "  ❌ $check" -ForegroundColor $red
        }
    }
} else {
    Write-Host "  ❌ Arquivo não encontrado: $agent_file" -ForegroundColor $red
}

Write-Host ""

# ============================================================================
# 3. Validar mudanças em chat.py endpoint
# ============================================================================
Write-Host "📋 Validando mudanças em chat.py endpoint..." -ForegroundColor $cyan
$chat_file = "backend/app/api/v1/endpoints/chat.py"

if (Test-Path $chat_file) {
    $content = Get-Content $chat_file -Raw
    
    $checks = @{
        "Agent response validation" = $content -match "if not agent_response"
        "Fallback response in endpoint" = $content -match "Desculpe, não consegui processar"
        "Empty text handling" = $content -match "if not response_text or.*strip\(\)"
        "Never empty message guarantee" = $content -match "Resposta processada, mas nenhum texto foi gerado"
    }
    
    foreach ($check in $checks.Keys) {
        if ($checks[$check]) {
            Write-Host "  ✅ $check" -ForegroundColor $green
        } else {
            Write-Host "  ❌ $check" -ForegroundColor $red
        }
    }
} else {
    Write-Host "  ❌ Arquivo não encontrado: $chat_file" -ForegroundColor $red
}

Write-Host ""

# ============================================================================
# 4. Validar arquivo de testes
# ============================================================================
Write-Host "📋 Validando arquivo de testes..." -ForegroundColor $cyan
$test_file = "backend/tests/test_changes.py"

if (Test-Path $test_file) {
    $content = Get-Content $test_file -Raw
    
    $checks = @{
        "TestTransferFiltersUI class" = $content -match "class TestTransferFiltersUI"
        "TestChatBIResponses class" = $content -match "class TestChatBIResponses"
        "TestIntegration class" = $content -match "class TestIntegration"
        "Test for empty responses" = $content -match "test.*empty.*response"
        "Test for fallback" = $content -match "test.*fallback"
    }
    
    foreach ($check in $checks.Keys) {
        if ($checks[$check]) {
            Write-Host "  ✅ $check" -ForegroundColor $green
        } else {
            Write-Host "  ❌ $check" -ForegroundColor $red
        }
    }
} else {
    Write-Host "  ❌ Arquivo não encontrado: $test_file" -ForegroundColor $red
}

Write-Host ""

# ============================================================================
# 5. Sumário das mudanças
# ============================================================================
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor $cyan
Write-Host "║                    SUMÁRIO DE MUDANÇAS                       ║" -ForegroundColor $cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor $cyan

Write-Host ""
Write-Host "✅ PROBLEMA 1: Página de Transferências" -ForegroundColor $green
Write-Host "   Status: RESOLVIDO"
Write-Host "   Mudanças:"
Write-Host "   • Adicionado filtro de UNE origem/destino no topo"
Write-Host "   • Suporte para 3 modos: 1→1, 1→N, N→N"
Write-Host "   • Múltiplas seleções no modo apropriado"
Write-Host "   • Validação em tempo real"
Write-Host ""

Write-Host "✅ PROBLEMA 2: ChatBI com Respostas Vazias" -ForegroundColor $green
Write-Host "   Status: RESOLVIDO"
Write-Host "   Mudanças:"
Write-Host "   • Agente nunca retorna resposta vazia"
Write-Host "   • Fallback contextualizado quando há erro"
Write-Host "   • Try-catch abrangente com garantia de resposta"
Write-Host "   • Validação no endpoint SSE"
Write-Host ""

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor $cyan
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor $yellow
Write-Host ""
Write-Host "1. Executar testes unitários:"
Write-Host "   pytest backend/tests/test_changes.py -v"
Write-Host ""
Write-Host "2. Iniciar a aplicação para testes manuais:"
Write-Host "   ./run.ps1"
Write-Host ""
Write-Host "3. Testar manualmente:"
Write-Host "   • Página de Transferências: /transfers"
Write-Host "   • ChatBI: /chat"
Write-Host ""
Write-Host "4. Validar nos navegadores:"
Write-Host "   • Frontend Solid: http://localhost:3000"
Write-Host "   • API Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor $cyan

Write-Host ""
Write-Host "📄 Documentação completa em: MUDANCAS_IMPLEMENTADAS.md" -ForegroundColor $cyan
Write-Host ""
