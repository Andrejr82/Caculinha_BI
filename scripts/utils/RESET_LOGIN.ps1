#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reset do localStorage para limpar tokens e força novo login
    
.DESCRIPTION
    Remove tokens do localStorage para que a aplicação pita para login novamente
#>

Write-Host "🔄 Limpando localStorage..." -ForegroundColor Cyan

# Abrir o console do navegador e executar isso manualmente:
Write-Host ""
Write-Host "Siga estes passos no navegador:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Abra o Developer Tools (F12 ou Ctrl+Shift+I)"
Write-Host "2. Vá para a aba 'Console'"
Write-Host "3. Cole este comando:"
Write-Host ""
Write-Host "localStorage.clear(); sessionStorage.clear(); location.reload();" -ForegroundColor Green
Write-Host ""
Write-Host "4. Pressione Enter"
Write-Host ""
Write-Host "Isso irá:"
Write-Host "  ✅ Limpar todos os tokens salvos"
Write-Host "  ✅ Limpar a sessão"
Write-Host "  ✅ Recarregar a página"
Write-Host "  ✅ Força login novamente"
Write-Host ""
Write-Host "Após recarregar, você deverá ver a tela de login!" -ForegroundColor Green
