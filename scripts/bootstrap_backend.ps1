# ==================================================
# Caculinha BI - Bootstrap Backend (PowerShell)
# ==================================================

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; exit 1 }

$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BACKEND_DIR = "$ROOT\backend"
$VENV = "$ROOT\.venv"
$REQ = "$BACKEND_DIR\requirements.txt"

Info "Iniciando bootstrap do backend em $BACKEND_DIR"

# 1. Verificar virtualenv
if (!(Test-Path $VENV)) {
    Info "Criando virtualenv (.venv) em $VENV..."
    python -m venv $VENV
    Ok "Virtualenv criado."
} else {
    Ok "Virtualenv detectado."
}

# 2. Ativar e Sincronizar
Info "Ativando ambiente e sincronizando dependências..."
& "$VENV\Scripts\Activate.ps1"

python -m pip install --upgrade pip
pip install pip-tools

if (!(Test-Path $REQ)) {
    Fail "Arquivo $REQ não encontrado. Execute pip-compile primeiro."
}

Info "Executando pip-sync..."
python -m piptools sync $REQ

Info "Executando pip check..."
pip check
if ($LASTEXITCODE -ne 0) {
    Fail "Inconsistência de dependências detectada pelo pip check!"
}

Ok "Ambiente sincronizado com sucesso."
