# ==================================================
# Caculinha BI - RUN NATIVE ALL (Optimized)
# Backend + Frontend (Windows)
# ==================================================

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; Pause; exit 1 }

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BOOTSTRAP_SCRIPT = "$ROOT\scripts\bootstrap_backend.ps1"
$FRONTEND_DIR = "$ROOT\frontend-solid"
$VENV = "$ROOT\.venv"

# -------------------------------
# 1. Backend Bootstrap (Delegate)
# -------------------------------
Info "Delegando setup do backend para bootstrap_backend.ps1..."
if (Test-Path $BOOTSTRAP_SCRIPT) {
    & $BOOTSTRAP_SCRIPT
    if ($LASTEXITCODE -ne 0) { Fail "Bootstrap do backend falhou!" }
}
else {
    Fail "Script de bootstrap não encontrado em: $BOOTSTRAP_SCRIPT"
}

# -------------------------------
# 2. Environment Variables
# -------------------------------
# NOTA: Não definimos variáveis hardcoded aqui. 
# O sistema deve confiar exclusivamente no arquivo '.env'.
# Se precisar de overrides, faça no .env ou na sessão do terminal antes de chamar este script.
Info "Usando configuração do arquivo .env (se existir)"

# -------------------------------
# 3. Backend Startup
# -------------------------------
Info "Iniciando Backend (FastAPI)..."
$BackendCmd = "cd '$ROOT'; .\.venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd -WindowStyle Normal
Ok "Processo do Backend iniciado."

# -------------------------------
# 4. Frontend Startup
# -------------------------------
Info "Verificando Frontend em $FRONTEND_DIR..."
if (Test-Path $FRONTEND_DIR) {
    $NodeModules = "$FRONTEND_DIR\node_modules"
    $InstallCmd = ""
    
    if (!(Test-Path $NodeModules)) {
        Warn "node_modules não encontrado. Executando 'npm install' (isso pode demorar)..."
        $InstallCmd = "npm install;"
    }
    else {
        Ok "node_modules encontrado. Pulando 'npm install' (Modo Rápido)."
    }

    Info "Iniciando Frontend (SolidJS)..."
    # Combinando comandos para garantir execução sequencial no novo terminal
    $FrontendCmd = "cd '$FRONTEND_DIR'; $InstallCmd npm run dev"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd -WindowStyle Normal
    Ok "Processo do Frontend iniciado."
}
else {
    Warn "Diretório do frontend não encontrado. Pulando etapa."
}

# -------------------------------
# 5. Wait for Services & Browser
# -------------------------------
Info "Aguardando serviços ficarem online..."

function Test-Port($port) {
    $tcp = New-Object Net.Sockets.TcpClient
    try {
        $tcp.Connect("localhost", $port)
        $tcp.Close()
        return $true
    }
    catch {
        return $false
    }
}

$Retries = 30
$BackendReady = $false
$FrontendReady = $false

# Loop de espera (Polling)
for ($i = 0; $i -lt $Retries; $i++) {
    if (-not $BackendReady) {
        if (Test-Port 8000) { 
            $BackendReady = $true; Ok "Backend está online na porta 8000!" 
        }
    }
    if (-not $FrontendReady) {
        if (Test-Port 3000) { 
            $FrontendReady = $true; Ok "Frontend está online na porta 3000!" 
        }
    }

    if ($BackendReady -and $FrontendReady) { break }
    
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 1
}

if ($BackendReady -and $FrontendReady) {
    Info "Abrindo navegador..."
    Start-Process "http://localhost:3000"
    Ok "Sistema totalmente operacional! 🚀"
}
else {
    Warn "Tempo limite esgotado. O navegador não foi aberto automaticamente."
    Warn "Verifique as janelas do Backend/Frontend para erros."
}

Pause
