param(
    [switch]$NoOpenBrowser,
    [switch]$UseConfiguredServices,
    [int]$FrontendReadyTimeoutMinutes = 120,
    [switch]$VerboseStartup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$StartupLogDir = Join-Path $RepoRoot "runtime_logs\startup"
$BackendPidFile = Join-Path $StartupLogDir "backend.pid"
$FrontendPidFile = Join-Path $StartupLogDir "frontend.pid"
$BackendOutLog = Join-Path $StartupLogDir "backend.out.log"
$BackendErrLog = Join-Path $StartupLogDir "backend.err.log"
$FrontendOutLog = Join-Path $StartupLogDir "frontend.out.log"
$FrontendErrLog = Join-Path $StartupLogDir "frontend.err.log"

function Write-Step {
    param([string]$Message)
    Write-Host $Message
}

function Write-VerboseStep {
    param([string]$Message)

    if ($VerboseStartup) {
        Write-Host $Message
    }
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Resolve-PythonPath {
    $venvPython = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-VerboseStep "[DEBUG] Python do backend encontrado em: $venvPython"
        return $venvPython
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        throw "Python nao encontrado. Instale Python 3.11+ e tente novamente."
    }

    Write-Step "[INFO] Criando ambiente virtual do backend em backend\.venv..."
    & $pythonCmd.Source -m venv (Join-Path $RepoRoot "backend\.venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar o ambiente virtual do backend."
    }

    if (-not (Test-Path $venvPython)) {
        throw "Python do backend nao encontrado apos a criacao do ambiente virtual."
    }

    Write-VerboseStep "[DEBUG] Python do backend criado em: $venvPython"
    return $venvPython
}

function Resolve-BunPath {
    $bunCmd = Get-Command bun -ErrorAction SilentlyContinue
    if ($bunCmd) {
        Write-VerboseStep "[DEBUG] Bun encontrado em: $($bunCmd.Source)"
        return $bunCmd.Source
    }

    $candidatePaths = @(
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\Oven-sh.Bun_Microsoft.Winget.Source_8wekyb3d8bbwe\bun-windows-x64\bun.exe"),
        (Join-Path $env:USERPROFILE ".bun\bin\bun.exe")
    )

    foreach ($candidate in $candidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            Write-VerboseStep "[DEBUG] Bun encontrado em caminho alternativo: $candidate"
            return $candidate
        }
    }

    throw "Bun nao encontrado. Instale Bun 1.2+ e tente novamente."
}

function Ensure-BackendDependencies {
    param([string]$PythonPath)

    # BUG FIX: usar 2>&1 e capturar saida corretamente para nao engolir LASTEXITCODE
    $checkOutput = & $PythonPath -c "import fastapi, uvicorn" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-VerboseStep "[DEBUG] Dependencias do backend (fastapi, uvicorn) ja estao instaladas."
        return
    }

    Write-Step "[INFO] Instalando dependencias do backend (fastapi ou uvicorn ausentes)..."
    & $PythonPath -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao atualizar o pip do backend."
    }

    $reqFile = Join-Path $RepoRoot "backend\requirements.txt"
    if (-not (Test-Path $reqFile)) {
        throw "Arquivo backend\requirements.txt nao encontrado em: $reqFile"
    }

    & $PythonPath -m pip install -r $reqFile
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar dependencias do backend."
    }
}

function Ensure-FrontendDependencies {
    param([string]$BunPath)

    $frontendRoot = Join-Path $RepoRoot "frontend-solid"
    $nodeModules = Join-Path $frontendRoot "node_modules"
    $packageJson = Join-Path $frontendRoot "package.json"
    $bunLock = Join-Path $frontendRoot "bun.lock"
    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue

    $needsInstall = -not (Test-Path $nodeModules)
    if (-not $needsInstall) {
        $nodeModulesTime = (Get-Item $nodeModules).LastWriteTimeUtc
        if ((Test-Path $packageJson) -and ((Get-Item $packageJson).LastWriteTimeUtc -gt $nodeModulesTime)) {
            $needsInstall = $true
        }
        if ((Test-Path $bunLock) -and ((Get-Item $bunLock).LastWriteTimeUtc -gt $nodeModulesTime)) {
            $needsInstall = $true
        }
    }

    if (-not $needsInstall) {
        Write-VerboseStep "[DEBUG] Dependencias do frontend ja estao atualizadas."
        return
    }

    Write-Step "[INFO] Instalando dependencias do frontend..."
    Push-Location $frontendRoot
    try {
        & $BunPath install
        if ($LASTEXITCODE -eq 0) {
            return
        }

        if (-not $npmCmd) {
            throw "Falha ao instalar dependencias com Bun e npm nao esta disponivel."
        }

        Write-Step "[WARN] Bun install falhou. Tentando npm install..."
        & $npmCmd.Source install --no-package-lock
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar dependencias do frontend."
        }
    }
    finally {
        Pop-Location
    }
}

function Ensure-ProjectFiles {
    $backendEnv = Join-Path $RepoRoot "backend\.env"
    $backendEnvExample = Join-Path $RepoRoot "backend\.env.example"
    if (-not (Test-Path $backendEnv)) {
        if (-not (Test-Path $backendEnvExample)) {
            throw "backend\.env e backend\.env.example nao foram encontrados."
        }

        Write-Step "[WARN] backend\.env nao encontrado. Criando a partir de backend\.env.example..."
        Copy-Item $backendEnvExample $backendEnv -Force
    }

    $parquetPath = Join-Path $RepoRoot "backend\data\parquet\admmat.parquet"
    if (-not (Test-Path $parquetPath)) {
        throw "Base parquet principal nao encontrada em backend\data\parquet\admmat.parquet"
    }

    Write-VerboseStep "[DEBUG] Arquivos obrigatorios localizados:"
    Write-VerboseStep "[DEBUG] backend\.env = $backendEnv"
    Write-VerboseStep "[DEBUG] parquet       = $parquetPath"
}

function Set-LocalSafeServiceOverrides {
    if ($UseConfiguredServices) {
        Write-Step "[INFO] Respeitando servicos configurados no backend\.env."
        return
    }

    $env:CHAT_STATE_BACKEND = "sqlite"
    $env:USE_SQL_SERVER = "false"
    $env:REDIS_ENABLED = "false"
    $env:REDIS_REQUIRED = "false"
    Write-Step "[INFO] Modo local seguro ativo: SQLite habilitado; SQL Server e Redis desabilitados."
}

function Stop-TrackedProcess {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return
    }

    $rawPid = (Get-Content $PidFile -Raw).Trim()
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

    if (-not $rawPid) {
        return
    }

    $numericPid = 0
    if (-not [int]::TryParse($rawPid, [ref]$numericPid)) {
        return
    }

    $proc = Get-Process -Id $numericPid -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Step "[INFO] Encerrando processo rastreado $($proc.ProcessName) (PID $numericPid)..."
        Stop-Process -Id $numericPid -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ProcessIfRunning {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$Label
    )

    if (-not $Process) {
        return
    }

    $active = Get-Process -Id $Process.Id -ErrorAction SilentlyContinue
    if ($active) {
        Write-Step "[INFO] Encerrando $Label (PID $($Process.Id)) apos falha na inicializacao..."
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    }
}

function Stop-PortListeners {
    param([int]$Port)

    Write-Step "[CHECK] Verificando porta $Port..."

    # BUG FIX: aspas quebradas no cmd/findstr substituidas por Get-NetTCPConnection (nativo PS)
    # Fallback para netstat se Get-NetTCPConnection nao estiver disponivel (PS 2.0)
    $listeningPids = @()
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($connections) {
            $listeningPids = @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
        }
    }
    catch {
        # Fallback: netstat com aspas corrigidas
        $netstatOutput = & cmd /c "netstat -ano" 2>$null
        foreach ($line in $netstatOutput) {
            if ($line -match ":$Port\s+.*LISTENING\s+(\d+)") {
                $pidValue = [int]$Matches[1]
                if ($pidValue -gt 0) {
                    $listeningPids += $pidValue
                }
            }
        }
        $listeningPids = @($listeningPids | Select-Object -Unique)
    }

    if (-not $listeningPids) {
        Write-Step "[OK] Porta $Port ja esta livre."
        return $false
    }

    $stoppedAny = $false
    foreach ($pidValue in $listeningPids) {
        if ($pidValue -le 0) { continue }
        $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        $procLabel = if ($proc) { "$($proc.ProcessName) (PID $pidValue)" } else { "PID $pidValue" }
        Write-Step "[INFO] Porta $Port ocupada por $procLabel. Encerrando arvore do processo..."
        & taskkill /PID $pidValue /T /F 2>$null | Out-Null
        $stoppedAny = $true
    }

    $deadline = (Get-Date).AddSeconds(8)
    while ((Get-Date) -lt $deadline) {
        $stillListening = $false
        try {
            $remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
            $stillListening = ($null -ne $remaining)
        }
        catch {
            $netstatCheck = & cmd /c "netstat -ano" 2>$null
            $stillListening = ($netstatCheck | Where-Object { $_ -match ":$Port\s+.*LISTENING" }).Count -gt 0
        }

        if (-not $stillListening) {
            Write-Step "[OK] Porta $Port liberada."
            return $stoppedAny
        }

        Start-Sleep -Milliseconds 400
    }

    Write-Step "[WARN] Porta $Port ainda aparece ocupada apos a tentativa de encerramento."
    return $stoppedAny
}

function Remove-LogFiles {
    param([string[]]$Paths)

    foreach ($path in $Paths) {
        if (Test-Path $path) {
            Remove-Item $path -Force -ErrorAction SilentlyContinue
        }
    }
}

function Show-StartupConfiguration {
    $frontendTimeoutSeconds = [Math]::Max(60, ($FrontendReadyTimeoutMinutes * 60))
    Write-VerboseStep "[DEBUG] Configuracao de inicializacao:"
    Write-VerboseStep "[DEBUG] RepoRoot                = $RepoRoot"
    Write-VerboseStep "[DEBUG] StartupLogDir          = $StartupLogDir"
    Write-VerboseStep "[DEBUG] BackendOutLog          = $BackendOutLog"
    Write-VerboseStep "[DEBUG] BackendErrLog          = $BackendErrLog"
    Write-VerboseStep "[DEBUG] FrontendOutLog         = $FrontendOutLog"
    Write-VerboseStep "[DEBUG] FrontendErrLog         = $FrontendErrLog"
    Write-VerboseStep "[DEBUG] UseConfiguredServices  = $UseConfiguredServices"
    Write-VerboseStep "[DEBUG] NoOpenBrowser          = $NoOpenBrowser"
    Write-VerboseStep "[DEBUG] Frontend timeout (sec) = $frontendTimeoutSeconds"
}

function Show-LogTail {
    param(
        [string]$Title,
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Write-Step "--- $Title ---"
    Get-Content $Path -Tail 60
}

function Start-LoggedProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$StdOutPath,
        [string]$StdErrPath
    )

    return Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $StdOutPath `
        -RedirectStandardError $StdErrPath `
        -WindowStyle Hidden `
        -PassThru
}

function Start-FrontendProcess {
    param(
        [string]$BunPath,
        [string]$FrontendRoot,
        [string]$StdOutPath,
        [string]$StdErrPath
    )

    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    $attempts = @(
        @{
            FilePath = $BunPath
            Arguments = @("run", "dev:inline")
            Label = "bun run dev:inline"
        }
    )

    if ($npmCmd) {
        $attempts += @{
            FilePath = $npmCmd.Source
            Arguments = @("run", "dev:inline")
            Label = "npm run dev:inline"
        }
    }

    foreach ($attempt in $attempts) {
        Write-Step "[INFO] Tentando frontend com $($attempt.Label)..."
        $proc = Start-LoggedProcess `
            -FilePath $attempt.FilePath `
            -Arguments $attempt.Arguments `
            -WorkingDirectory $FrontendRoot `
            -StdOutPath $StdOutPath `
            -StdErrPath $StdErrPath

        # BUG FIX: aguardar mais tempo e verificar realmente se o processo esta vivo
        # 3 segundos era insuficiente; agora aguarda ate 10s checando a cada 500ms
        $checkDeadline = (Get-Date).AddSeconds(10)
        $processAlive = $false
        while ((Get-Date) -lt $checkDeadline) {
            if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                $processAlive = $true
                break
            }
            Start-Sleep -Milliseconds 500
        }

        if ($processAlive) {
            Write-VerboseStep "[DEBUG] Processo frontend ($($attempt.Label)) iniciado com PID $($proc.Id)."
            return $proc
        }

        Write-Step "[WARN] Estrategia '$($attempt.Label)' falhou. Verificando log de erro..."
        if (Test-Path $StdErrPath) {
            $errContent = Get-Content $StdErrPath -Tail 10 -ErrorAction SilentlyContinue
            if ($errContent) {
                Write-Step "[WARN] Ultimas linhas do erro do frontend:"
                $errContent | ForEach-Object { Write-Step "       $_" }
            }
        }
    }

    throw "Nenhuma estrategia conseguiu iniciar o frontend."
}

function Wait-ForHttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds,
        [string]$Label,
        [int]$ProcessId
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $startTime = Get-Date
    $lastLog = $startTime
    $logIntervalSeconds = 15

    while ((Get-Date) -lt $deadline) {
        $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if (-not $proc) {
            throw "$Label encerrou antes de responder em $Url"
        }

        # BUG FIX: usar -ErrorAction SilentlyContinue no try para suprimir erros vermelhos
        # do Invoke-WebRequest no console do Windows enquanto o servico ainda nao subiu
        try {
            $oldPref = $ErrorActionPreference
            $ErrorActionPreference = "SilentlyContinue"
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
            $ErrorActionPreference = $oldPref
            if ($response -and ($response.StatusCode -ge 200) -and ($response.StatusCode -lt 400)) {
                $elapsed = [int]((Get-Date) - $startTime).TotalSeconds
                Write-Step "[OK] $Label pronto em ${elapsed}s."
                return
            }
        }
        catch {
            $ErrorActionPreference = $oldPref
        }

        # Log de progresso periodico para nao parecer travado
        $now = Get-Date
        if (($now - $lastLog).TotalSeconds -ge $logIntervalSeconds) {
            $elapsed = [int]($now - $startTime).TotalSeconds
            $remaining = [int]($deadline - $now).TotalSeconds
            Write-Step "[INFO] Aguardando $Label... (${elapsed}s decorridos, ${remaining}s restantes)"
            $lastLog = $now
        }

        Start-Sleep -Seconds 2
    }

    throw "Timeout aguardando $Label em $Url apos ${TimeoutSeconds}s"
}

$backendProc = $null
$frontendProc = $null

try {
    Ensure-Directory -Path $StartupLogDir
    Stop-TrackedProcess -PidFile $BackendPidFile
    Stop-TrackedProcess -PidFile $FrontendPidFile

    Write-Step ""
    Write-Step "[START] Iniciando ecossistema Caculinha BI..."
    Write-Step ""
    Write-Step "[CHECK] Validando requisitos..."

    $pythonPath = Resolve-PythonPath
    $bunPath = Resolve-BunPath
    Show-StartupConfiguration
    Write-VerboseStep "[DEBUG] PythonPath             = $pythonPath"
    Write-VerboseStep "[DEBUG] BunPath                = $bunPath"

    Write-Step "[CHECK] Validando dependencias do backend..."
    Ensure-BackendDependencies -PythonPath $pythonPath

    Write-Step "[CHECK] Validando arquivos de configuracao e dados..."
    Ensure-ProjectFiles

    Write-Step "[CHECK] Validando dependencias do frontend..."
    Ensure-FrontendDependencies -BunPath $bunPath

    Set-LocalSafeServiceOverrides

    Write-Step "[CHECK] Liberando portas 8000 e 3000, se necessario..."
    [void](Stop-PortListeners -Port 8000)
    [void](Stop-PortListeners -Port 3000)

    Remove-LogFiles -Paths @($BackendOutLog, $BackendErrLog, $FrontendOutLog, $FrontendErrLog)

    $env:PYTHONPATH = $RepoRoot

    Write-Step "[BACKEND] Iniciando API FastAPI em 8000..."
    $backendProc = Start-LoggedProcess `
        -FilePath $pythonPath `
        -Arguments @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $RepoRoot `
        -StdOutPath $BackendOutLog `
        -StdErrPath $BackendErrLog
    $backendProc.Id | Set-Content $BackendPidFile -Encoding ASCII
    Write-VerboseStep "[DEBUG] Backend PID            = $($backendProc.Id)"

    try {
        Wait-ForHttpReady -Url "http://127.0.0.1:8000/health" -TimeoutSeconds 180 -Label "Backend" -ProcessId $backendProc.Id
    }
    catch {
        Write-Step "[ERRO] Backend nao respondeu corretamente."
        Show-LogTail -Title "backend.out.log" -Path $BackendOutLog
        Show-LogTail -Title "backend.err.log" -Path $BackendErrLog
        throw
    }

    Write-Step "[FRONTEND] Iniciando SolidJS em 3000..."
    $frontendRoot = Join-Path $RepoRoot "frontend-solid"
    $frontendProc = Start-FrontendProcess `
        -BunPath $bunPath `
        -FrontendRoot $frontendRoot `
        -StdOutPath $FrontendOutLog `
        -StdErrPath $FrontendErrLog
    $frontendProc.Id | Set-Content $FrontendPidFile -Encoding ASCII
    Write-VerboseStep "[DEBUG] Frontend PID           = $($frontendProc.Id)"

    try {
        $frontendTimeoutSeconds = [Math]::Max(60, ($FrontendReadyTimeoutMinutes * 60))
        Write-Step "[INFO] Aguardando o frontend ficar pronto por ate $FrontendReadyTimeoutMinutes minuto(s)..."
        Wait-ForHttpReady -Url "http://127.0.0.1:3000" -TimeoutSeconds $frontendTimeoutSeconds -Label "Frontend" -ProcessId $frontendProc.Id
    }
    catch {
        Write-Step "[ERRO] Frontend nao respondeu corretamente."
        Show-LogTail -Title "frontend.out.log" -Path $FrontendOutLog
        Show-LogTail -Title "frontend.err.log" -Path $FrontendErrLog
        throw
    }

    Write-Step ""
    Write-Step "[STATUS] Sistema iniciado:"
    Write-Step "--------------------------------------"
    Write-Step "Backend : http://localhost:8000/docs"
    Write-Step "Frontend: http://localhost:3000"
    Write-Step "--------------------------------------"

    if (-not $NoOpenBrowser) {
        try {
            Start-Process "http://localhost:3000" -ErrorAction Stop
            Write-Step "[INFO] Abrindo frontend no navegador padrao..."
        }
        catch {
            Write-Step "[WARN] Nao foi possivel abrir o navegador automaticamente. Acesse manualmente: http://localhost:3000"
        }
    }

    Write-Step "[DONE] Backend e frontend iniciados com sucesso."
    if ($VerboseStartup) {
        Write-Step "[DEBUG] Logs de inicializacao:"
        Write-Step "[DEBUG] $BackendOutLog"
        Write-Step "[DEBUG] $BackendErrLog"
        Write-Step "[DEBUG] $FrontendOutLog"
        Write-Step "[DEBUG] $FrontendErrLog"
    }

    Write-Step ""
    Write-Step "========================================"
    Write-Step "  Pressione Ctrl+C para encerrar tudo  "
    Write-Step "========================================"
    Write-Step ""

    # Loop monitor: mantém o terminal aberto e vigia os processos
    $monitorInterval = 10  # segundos entre cada checagem
    $lastStatusLog = Get-Date

    try {
        while ($true) {
            Start-Sleep -Seconds $monitorInterval

            $backendAlive  = $null -ne (Get-Process -Id $backendProc.Id  -ErrorAction SilentlyContinue)
            $frontendAlive = $null -ne (Get-Process -Id $frontendProc.Id -ErrorAction SilentlyContinue)

            if (-not $backendAlive) {
                Write-Step ""
                Write-Step "[ALERTA] Backend (PID $($backendProc.Id)) encerrou inesperadamente!"
                Show-LogTail -Title "backend.err.log (ultimas linhas)" -Path $BackendErrLog
                Write-Step "[INFO] Encerrando frontend por seguranca..."
                Stop-ProcessIfRunning -Process $frontendProc -Label "frontend"
                exit 2
            }

            if (-not $frontendAlive) {
                Write-Step ""
                Write-Step "[ALERTA] Frontend (PID $($frontendProc.Id)) encerrou inesperadamente!"
                Show-LogTail -Title "frontend.err.log (ultimas linhas)" -Path $FrontendErrLog
                Write-Step "[INFO] Encerrando backend por seguranca..."
                Stop-ProcessIfRunning -Process $backendProc -Label "backend"
                exit 3
            }

            # Log de status periodico (a cada 5 minutos)
            if (((Get-Date) - $lastStatusLog).TotalMinutes -ge 5) {
                Write-Step "[MONITOR] Sistema rodando | Backend PID $($backendProc.Id) | Frontend PID $($frontendProc.Id)"
                $lastStatusLog = Get-Date
            }
        }
    }
    finally {
        # Bloco finally garante limpeza ao sair (Ctrl+C ou qualquer saida)
        Write-Step ""
        Write-Step "[INFO] Encerrando sistema..."
        Stop-ProcessIfRunning -Process $frontendProc -Label "frontend"
        Stop-ProcessIfRunning -Process $backendProc  -Label "backend"
        Remove-Item $FrontendPidFile -Force -ErrorAction SilentlyContinue
        Remove-Item $BackendPidFile  -Force -ErrorAction SilentlyContinue
        Write-Step "[DONE] Sistema encerrado."
    }
}
catch {
    Stop-ProcessIfRunning -Process $frontendProc -Label "frontend"
    Stop-ProcessIfRunning -Process $backendProc -Label "backend"
    Remove-Item $FrontendPidFile -Force -ErrorAction SilentlyContinue
    Remove-Item $BackendPidFile -Force -ErrorAction SilentlyContinue
    Write-Step ""
    Write-Step "[ERRO] $($_.Exception.Message)"
    exit 1
}
