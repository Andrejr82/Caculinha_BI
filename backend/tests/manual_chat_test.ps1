#!/usr/bin/env pwsh
# Teste Manual - Validação de Resposta do Chat
# Testa se o LLM está usando prompt v4 corretamente

Write-Host "`n============================================" -ForegroundColor Blue
Write-Host "TESTE MANUAL - CHAT API" -ForegroundColor Blue
Write-Host "============================================`n" -ForegroundColor Blue

$url = "http://localhost:8000/api/v1/chat/stream"
$body = @{
    message = "Analise vendas do produto 25 em todas as lojas"
    session_id = "manual_test_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
} | ConvertTo-Json

Write-Host "Enviando query: 'Analise vendas do produto 25 em todas as lojas'" -ForegroundColor Yellow
Write-Host "Aguardando resposta...`n" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $url -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
    
    $fullResponse = $response.Content
    
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "RESPOSTA RECEBIDA:" -ForegroundColor Green
    Write-Host "============================================`n" -ForegroundColor Green
    
    Write-Host $fullResponse
    
    Write-Host "`n============================================" -ForegroundColor Blue
    Write-Host "VALIDAÇÃO:" -ForegroundColor Blue
    Write-Host "============================================`n" -ForegroundColor Blue
    
    # Verificar violações
    $violations = @()
    
    if ($fullResponse -match "prever_demanda_sazonal") {
        $violations += "❌ Menciona 'prever_demanda_sazonal'"
    } else {
        Write-Host "✅ Não menciona 'prever_demanda_sazonal'" -ForegroundColor Green
    }
    
    if ($fullResponse -match "calcular_eoq") {
        $violations += "❌ Menciona 'calcular_eoq'"
    } else {
        Write-Host "✅ Não menciona 'calcular_eoq'" -ForegroundColor Green
    }
    
    if ($fullResponse -match "produto_codigo=") {
        $violations += "❌ Menciona 'produto_codigo='"
    } else {
        Write-Host "✅ Não menciona 'produto_codigo='" -ForegroundColor Green
    }
    
    if ($fullResponse -match "é crucial utilizar a ferramenta") {
        $violations += "❌ Menciona 'é crucial utilizar a ferramenta'"
    } else {
        Write-Host "✅ Não menciona 'é crucial utilizar a ferramenta'" -ForegroundColor Green
    }
    
    $count25 = ([regex]::Matches($fullResponse, "produto 25", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)).Count
    if ($count25 -gt 2) {
        $violations += "❌ Repete 'produto 25' $count25 vezes (máximo 2)"
    } else {
        Write-Host "✅ Menciona 'produto 25' apenas $count25 vezes" -ForegroundColor Green
    }
    
    Write-Host "`n============================================" -ForegroundColor Blue
    if ($violations.Count -eq 0) {
        Write-Host "🎉 TESTE PASSOU - Todas validações OK!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ TESTE FALHOU - Violações encontradas:" -ForegroundColor Red
        foreach ($v in $violations) {
            Write-Host "  $v" -ForegroundColor Red
        }
    }
    Write-Host "============================================`n" -ForegroundColor Blue
    
} catch {
    Write-Host "❌ ERRO: $_" -ForegroundColor Red
    exit 1
}
