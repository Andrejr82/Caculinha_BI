# ========================================
#   AGENT BI - POWERSHELL LAUNCHER
#   Versão moderna com melhor gestão de processos
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AGENT BI - INICIANDO SISTEMA" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Função para exibir mensagem de status
function Write-Status {
    param(
        [string]$Step,
        [string]$Message,
        [string]$Status = "INFO"
    )

    $color = switch ($Status) {
        "OK"    { "Green" }
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        default { "White" }
    }

    Write-Host "[$Step] " -NoNewline -ForegroundColor Gray
    Write-Host $Message -ForegroundColor $color
}

# Verificar Node.js
Write-Status "1/6" "Verificando Node.js..."
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Status "ERROR" "Node.js não encontrado!" "ERROR"
    Write-Host "Por favor, instale Node.js de https://nodejs.org/" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Status "OK" "Node.js encontrado" "OK"

# Verificar Python
Write-Status "2/6" "Verificando Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Status "ERROR" "Python não encontrado!" "ERROR"
    Write-Host "Por favor, instale Python de https://python.org/" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Status "OK" "Python encontrado" "OK"

# Limpar processos antigos
Write-Status "3/6" "Limpando processos antigos..."
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Status "OK" "Processos limpos" "OK"

# Limpar cache Python
Write-Status "4/6" "Limpando cache Python..."
Get-ChildItem -Path "backend" -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "backend" -File -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Status "OK" "Cache limpo" "OK"

# Instalar dependências
Write-Status "5/6" "Verificando dependências..."
if (-not (Test-Path "node_modules\concurrently")) {
    Write-Status "INFO" "Instalando concurrently..." "WARN"
    npm install --silent
}
Write-Status "OK" "Dependências verificadas" "OK"

# Limpar portas
Write-Status "6/6" "Limpando portas 8000 e 3000..."
node scripts/clean-port.js
Write-Status "OK" "Portas limpas" "OK"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SISTEMA INICIANDO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Backend:  " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:8000" -ForegroundColor Blue
Write-Host "Frontend: " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:3000" -ForegroundColor Green
Write-Host "API Docs: " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:8000/docs" -ForegroundColor Magenta

Write-Host "`nCredenciais:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Senha:    Admin@2024" -ForegroundColor White

Write-Host "`n========================================`n" -ForegroundColor Cyan

Write-Host "[INFO] Backend e Frontend no mesmo terminal" -ForegroundColor Cyan
Write-Host "[INFO] Logs coloridos:" -ForegroundColor Cyan
Write-Host "       - BACKEND  (azul)" -ForegroundColor Blue
Write-Host "       - FRONTEND (verde)" -ForegroundColor Green

Write-Host "`n[DICA] Pressione Ctrl+C para encerrar`n" -ForegroundColor Yellow

# Aguardar e abrir navegador
Start-Sleep -Seconds 8
Start-Process "http://localhost:3000"

# Iniciar com concurrently
npm run dev
