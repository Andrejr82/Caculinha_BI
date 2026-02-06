$ErrorActionPreference = "Stop"

function Test-PortAvailability {
    param($Port)
    $con = (Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet)
    return $con
}

Write-Host ">>> INICIANDO TESTE AUTOMATIZADO DO RUN.BAT <<<" -ForegroundColor Cyan

# 1. Limpeza Prévia
Write-Host "1. Limpando processos antigos..."
try {
    Stop-Process -Name "python" -ErrorAction SilentlyContinue -Force
    Stop-Process -Name "node" -ErrorAction SilentlyContinue -Force
} catch {}
Start-Sleep -Seconds 2

if (Test-PortAvailability 8000) { Write-Error "Porta 8000 ainda ocupada!"; exit 1 }
if (Test-PortAvailability 3000) { Write-Error "Porta 3000 ainda ocupada!"; exit 1 }

# 2. Iniciar run.bat em Background
Write-Host "2. Iniciando run.bat (Background Job)..."

# Usamos Start-Process com PassThru para ter o objeto do processo, mas run.bat lança filhos.
# Redirecionamos output para arquivo para debug se falhar
$job = Start-Process -FilePath "cmd.exe" -ArgumentList "/c run.bat > test_run_output.log 2>&1" -PassThru -NoNewWindow

if (-not $job) {
    Write-Error "Falha ao iniciar run.bat"
    exit 1
}

Write-Host "   Job iniciado (PID: $($job.Id)). Aguardando 45 segundos para startup..."
# O backend demora um pouco para criar o venv se for a primeira vez, e o frontend compila.
# Vou dar um tempo generoso.
Start-Sleep -Seconds 45

# 3. Verificações
Write-Host "3. Verificando servicos..."

$backendOK = $false
$frontendOK = $false

# Teste Backend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCESSO] Backend respondendo (Health Check OK)" -ForegroundColor Green
        $backendOK = $true
    } else {
        Write-Host "[FALHA] Backend respondeu com status $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "[FALHA] Backend nao respondeu: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste Frontend
try {
    # O frontend pode retornar 200 (OK)
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCESSO] Frontend respondendo (HTTP 200)" -ForegroundColor Green
        $frontendOK = $true
    } else {
        Write-Host "[FALHA] Frontend respondeu com status $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "[FALHA] Frontend nao respondeu: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Cleanup
Write-Host "4. Encerrando teste e limpando processos..."
Stop-Process -Id $job.Id -ErrorAction SilentlyContinue -Force
# run.bat lança python e node filhos, precisamos matar explicitamente
Stop-Process -Name "python" -ErrorAction SilentlyContinue -Force
Stop-Process -Name "node" -ErrorAction SilentlyContinue -Force

# 5. Relatório Final
if ($backendOK -and $frontendOK) {
    Write-Host ">>> TESTE CONCLUIDO COM SUCESSO! <<<" -ForegroundColor Green
    exit 0
} else {
    Write-Host ">>> LOG DE SAIDA (Últimas 20 linhas) <<<" -ForegroundColor Yellow
    Get-Content .\test_run_output.log -Tail 20
    Write-Host ">>> TESTE FALHOU <<<" -ForegroundColor Red
    exit 1
}
