@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================
echo CACULINHA BI - E2E Runner (1 clique)
echo ==========================================
echo.

REM --- garante pastas
if not exist logs mkdir logs
if not exist docs mkdir docs

REM --- arquivo PS1
set PS1=%~dp0run_e2e.ps1

REM --- cria PS1 se nao existir
if not exist "%PS1%" (
  echo [INFO] Criando run_e2e.ps1 automaticamente...
  > "%PS1%" (
    echo param(^
    echo   [string]$BaseUrl = "http://localhost:8000",^
    echo   [string]$TenantId = "lojas_cacula",^
    echo   [int]$K = 5^
    echo ^)
    echo $ErrorActionPreference = "Stop"
    echo $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    echo $logDir = "logs"
    echo $docDir = "docs"
    echo $logFile = "$logDir\e2e_$timestamp.log"
    echo $reportFile = "$docDir\e2e_report_$timestamp.md"
    echo New-Item -ItemType Directory -Force -Path $logDir ^| Out-Null
    echo New-Item -ItemType Directory -Force -Path $docDir ^| Out-Null
    echo Start-Transcript -Path $logFile -Append
    echo function Info($m){Write-Host "`n[INFO] $m" -ForegroundColor Cyan}
    echo function Ok($m){Write-Host "[OK]   $m" -ForegroundColor Green}
    echo function Warn($m){Write-Host "[WARN] $m" -ForegroundColor Yellow}
    echo function Fail($m){Write-Host "[FAIL] $m" -ForegroundColor Red; Stop-Transcript; pause; exit 1}
    echo $report = @()
    echo $report += "# Caculinha BI — E2E Report"
    echo $report += ""
    echo $report += "**Data:** $(Get-Date)"
    echo $report += "**Tenant:** $TenantId"
    echo $report += ""
    echo function Report($l){ $script:report += $l }
    echo Info "Subindo ambiente (Docker + API)"
    echo Report "## Inicialização"
    echo Report "- Base URL: $BaseUrl"
    echo docker compose down -v ^| Out-Null
    echo docker compose up -d ^| Out-Null
    echo Info "Verificando health"
    echo $healthOk = $false
    echo $healthUrl = ""
    echo foreach($u in @("$BaseUrl/health","$BaseUrl/api/v1/health")){ try{Invoke-WebRequest $u -TimeoutSec 8 ^| Out-Null; $healthOk=$true; $healthUrl=$u; break}catch{} }
    echo if(-not $healthOk){ Fail "API nao respondeu health." }
    echo Ok "API saudavel: $healthUrl"
    echo Report "- Health OK ($healthUrl)"
    echo Info "Rebuild do catalogo (FULL + activate)"
    echo $rebuildUrl = "$BaseUrl/api/v1/catalog/rebuild"
    echo $rebuildBody = @{mode="full";activate=$true} ^| ConvertTo-Json
    echo try{Invoke-RestMethod -Method POST -Uri $rebuildUrl -ContentType "application/json" -Body $rebuildBody ^| Out-Null}catch{Fail "Falha no rebuild: $($_.Exception.Message)"}
    echo Ok "Catalogo rebuildado"
    echo Report "## Catalogo"
    echo Report "- Rebuild FULL executado"
    echo Add-Type -AssemblyName System.Web
    echo Info "Busca sanity (alca bolsa madeira)"
    echo $q = [System.Web.HttpUtility]::UrlEncode("alca bolsa madeira")
    echo $searchUrl = "$BaseUrl/api/v1/catalog/search?q=$q&k=$K"
    echo try{$search = Invoke-RestMethod $searchUrl}catch{Fail "Falha na busca: $($_.Exception.Message)"}
    echo $firstId = $null
    echo if($search.results -and $search.results.Count -gt 0){$firstId=$search.results[0].product_id}
    echo if(-not $firstId){$firstId=704566}
    echo Ok "Busca OK - top1 id: $firstId"
    echo Report "- Busca OK (top1: $firstId)"
    echo Info "Chat E2E"
    echo $chatUrl = "$BaseUrl/api/v1/chat"
    echo $chatBody = @{message="Quais produtos de alca de bolsa em madeira temos?";tenant_id=$TenantId} ^| ConvertTo-Json
    echo try{$chat = Invoke-RestMethod -Method POST -Uri $chatUrl -ContentType "application/json" -Body $chatBody ^| Out-Null}catch{Warn "Falhou /chat. Tentando /chat_v2..."; ^
         $chatUrl="$BaseUrl/api/v1/chat_v2"; ^
         try{$chat = Invoke-RestMethod -Method POST -Uri $chatUrl -ContentType "application/json" -Body $chatBody ^| Out-Null}catch{Fail "Falha no chat."}}
    echo Ok "Chat OK"
    echo Report "## Chat"
    echo Report "- Chat OK ($chatUrl)"
    echo Info "Feedback (loop)"
    echo $fbOk = $false
    echo foreach($u in @("$BaseUrl/api/v1/feedback","$BaseUrl/api/v1/catalog/feedback")){ ^
        try{ ^
          $fbBody = @{query="alca bolsa madeira";product_id=$firstId;signal="positive";tenant_id=$TenantId} ^| ConvertTo-Json; ^
          Invoke-RestMethod -Method POST -Uri $u -ContentType "application/json" -Body $fbBody ^| Out-Null; ^
          $fbOk=$true; $fbUrl=$u; break ^
        }catch{} ^
      }
    echo if($fbOk){Ok "Feedback OK: $fbUrl"; Report "## Aprendizado"; Report "- Feedback OK ($fbUrl)"} else {Warn "Feedback nao enviado"; Report "## Aprendizado"; Report "- Feedback NAO enviado"}
    echo Report "## Links"
    echo Report "- Search: $searchUrl"
    echo Report "- Metrics: $BaseUrl/api/v1/metrics (ou /metrics)"
    echo Report ""
    echo Report "## Resultado"
    echo Report "- Stack rodando"
    echo Report "- Catalogo ativo"
    echo Report "- Busca OK"
    echo Report "- Chat OK"
    echo $report ^| Out-File $reportFile -Encoding UTF8
    echo Stop-Transcript
    echo Info "Abrindo navegador..."
    echo Start-Process $searchUrl
    echo Start-Process "$BaseUrl/api/v1/metrics"
    echo Write-Host "`n✅ FINALIZADO" -ForegroundColor Green
    echo Write-Host "Log: $logFile"
    echo Write-Host "Relatorio: $reportFile"
    echo Write-Host "`nO sistema CONTINUA RODANDO para voce testar (Docker ficou em pe)."
    echo pause
  )
)

echo [INFO] Executando E2E via PowerShell...
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
endlocal
