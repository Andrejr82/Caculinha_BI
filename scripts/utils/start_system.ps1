# ========================================
#   AGENT BI - INICIALIZAR COM NODE.JS
#   Adiciona Node.js ao PATH e inicia sistema
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AGENT BI - INICIANDO SISTEMA COMPLETO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Adicionar Node.js ao PATH (para esta sessão)
$env:Path += ";C:\Program Files\nodejs"

# Função para exibir status
function Write-Status {
    param([string]$Step, [string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "OK"    { "Green" }
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        default { "White" }
    }
    Write-Host "[$Step] " -NoNewline -ForegroundColor Gray
    Write-Host $Message -ForegroundColor $color
}

# 1. Verificar Node.js
Write-Status "1/6" "Verificando Node.js..."
$nodeVersion = node --version 2>$null
if ($nodeVersion) {
    Write-Status "OK" "Node.js $nodeVersion encontrado" "OK"
} else {
    Write-Status "ERROR" "Node.js não encontrado!" "ERROR"
    Write-Host "Tente fechar e reabrir o PowerShell como Administrador" -ForegroundColor Yellow
    pause
    exit 1
}

# 2. Verificar npm
Write-Status "2/6" "Verificando npm..."
$npmVersion = npm --version 2>$null
if ($npmVersion) {
    Write-Status "OK" "npm $npmVersion encontrado" "OK"
} else {
    Write-Status "ERROR" "npm não encontrado!" "ERROR"
    pause
    exit 1
}

# 3. Verificar Python
Write-Status "3/6" "Verificando Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Status "ERROR" "Python não encontrado!" "ERROR"
    pause
    exit 1
}
$pythonVersion = python --version
Write-Status "OK" "$pythonVersion encontrado" "OK"

# 4. Limpar processos antigos
Write-Status "4/6" "Limpando processos antigos..."
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Status "OK" "Processos antigos removidos" "OK"

# 5. Instalar dependências frontend
Write-Status "5/6" "Instalando dependências (npm install)..."
cd frontend-solid
npm install --legacy-peer-deps 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Status "OK" "Dependências frontend instaladas" "OK"
} else {
    Write-Status "WARN" "npm install completou com avisos" "WARN"
}

# 6. Iniciar servidores
Write-Status "6/6" "Iniciando servidores..."
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SERVIDORES INICIANDO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🌐 Frontend (Vite):   http://localhost:5173" -ForegroundColor Green
Write-Host "  🔌 Backend (FastAPI): http://localhost:8000" -ForegroundColor Green
Write-Host "  📚 API Docs:          http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "  Credenciais Admin:" -ForegroundColor Yellow
Write-Host "    Username: admin" -ForegroundColor White
Write-Host "    Password: Admin@2024" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Iniciar frontend em background
Write-Host "Iniciando frontend (npm run dev)..." -ForegroundColor Gray
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "$(pwd)"

# Aguardar um pouco
Start-Sleep -Seconds 3

# Ir para backend
cd ../backend

# Iniciar backend (em foreground)
Write-Host "Iniciando backend (python main.py)..." -ForegroundColor Gray
Write-Host ""

python main.py
