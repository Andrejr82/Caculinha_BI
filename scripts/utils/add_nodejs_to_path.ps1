# ========================================
#   ADICIONAR NODE.JS AO PATH PERMANENTEMENTE
#   Execute como Administrador
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ADICIONAR NODE.JS AO PATH DO SISTEMA" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verificar se estamos como admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ Este script precisa ser executado como ADMINISTRADOR!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Como fazer:" -ForegroundColor Yellow
    Write-Host "1. Pressione Win + X" -ForegroundColor White
    Write-Host "2. Selecione 'Windows PowerShell (Admin)'" -ForegroundColor White
    Write-Host "3. Execute novamente: .\add_nodejs_to_path.ps1" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "✅ Executando como Administrador`n" -ForegroundColor Green

# Verificar se Node.js está instalado
$nodeInstallPath = "C:\Program Files\nodejs"
if (-not (Test-Path $nodeInstallPath)) {
    Write-Host "❌ Node.js não encontrado em $nodeInstallPath" -ForegroundColor Red
    Write-Host "Por favor, instale Node.js primeiro de https://nodejs.org/" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Node.js encontrado em $nodeInstallPath`n" -ForegroundColor Green

# Obter PATH atual
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

# Verificar se Node.js já está no PATH
if ($currentPath -like "*nodejs*") {
    Write-Host "ℹ️  Node.js já está no PATH do sistema!" -ForegroundColor Cyan
    Write-Host "Nenhuma ação necessária." -ForegroundColor Gray
    pause
    exit 0
}

# Adicionar Node.js ao PATH
Write-Host "Adicionando Node.js ao PATH do sistema..." -ForegroundColor Gray
$newPath = $currentPath + ";C:\Program Files\nodejs"
[Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")

Write-Host "✅ Node.js adicionado ao PATH com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Feche TODOS os terminais PowerShell abertos" -ForegroundColor White
Write-Host "2. Abra um novo PowerShell (não precisa de admin)" -ForegroundColor White
Write-Host "3. Execute: .\start_system.ps1" -ForegroundColor White
Write-Host ""

Write-Host "Pressione Enter para fechar este script..." -ForegroundColor Gray
pause
