# ========================================
#   AGENT BI - BACKEND ONLY LAUNCHER
#   Sem Node.js (apenas Python/FastAPI)
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AGENT BI - BACKEND ONLY (Python)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verificar Python
Write-Host "[1/3] Verificando Python..." -ForegroundColor Gray
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python não encontrado!" -ForegroundColor Red
    Write-Host "Por favor, instale Python de https://python.org/" -ForegroundColor Yellow
    Write-Host "Certifique-se de marcar 'Add Python to PATH' durante a instalação" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "[OK] Python encontrado" -ForegroundColor Green

# Verificar venv
Write-Host "`n[2/3] Ativando ambiente virtual..." -ForegroundColor Gray
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvPath)) {
    Write-Host "[WARN] Ambiente virtual não encontrado. Criando..." -ForegroundColor Yellow
    python -m venv .venv
}

# Ativar venv
& $venvPath

# Instalar/atualizar dependências
Write-Host "[OK] Ambiente virtual ativado" -ForegroundColor Green

Write-Host "`n[3/3] Iniciando Backend (FastAPI)..." -ForegroundColor Gray
Write-Host "Aguarde..." -ForegroundColor Gray

# Navegar para backend e rodar
cd backend
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Backend rodando em: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Documentação (Swagger): http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Iniciar servidor FastAPI
python main.py

Write-Host "`nBackend finalizado." -ForegroundColor Yellow
