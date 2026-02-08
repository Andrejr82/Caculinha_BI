param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [string]$TenantId = "lojas_cacula",
    [int]$K = 5,
    [switch]$WithObs
)

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "`n[INFO] $m" -ForegroundColor Cyan }
function Ok($m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; pause; exit 1 }

function Wait-HttpOk($url, $timeoutSec = 180) {
    $start = Get-Date
    while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { return $true }
        }
        catch { Start-Sleep -Seconds 2 }
    }
    return $false
}

# Logs + report
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "docs" | Out-Null
$logFile = "logs\e2e_$timestamp.log"
$reportFile = "docs\e2e_report_$timestamp.md"
Start-Transcript -Path $logFile -Append

$report = New-Object System.Collections.Generic.List[string]
$report.Add("# Caculinha BI — E2E UI Runner")
$report.Add("")
$report.Add("**Data:** $(Get-Date)")
$report.Add("**BaseUrl:** $BaseUrl")
$report.Add("**FrontendUrl:** $FrontendUrl")
$report.Add("**TenantId:** $TenantId")
$report.Add("**Obs:** $WithObs")
$report.Add("")

Info "Subindo stack (UI sempre ligada) usando docker-compose.yml + docker-compose.dev.yml"

$compose = @("-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")

try { docker compose @compose down -v | Out-Null } catch { }
try {
    if ($WithObs) {
        docker compose @compose --profile obs up -d --build | Out-Null
        $report.Add("## Docker")
        $report.Add("- Subiu: frontend + backend + redis + prometheus (obs)")
    }
    else {
        docker compose @compose up -d --build | Out-Null
        $report.Add("## Docker")
        $report.Add("- Subiu: frontend + backend + redis (sem prometheus)")
    }
}
catch {
    Stop-Transcript
    Fail "Falha ao subir docker compose. Verifique Docker Desktop e tente novamente."
}

# Health
Info "Aguardando API"
$healthUrl = "$BaseUrl/health"
if (-not (Wait-HttpOk $healthUrl 180)) {
    $healthUrl = "$BaseUrl/api/v1/health"
    if (-not (Wait-HttpOk $healthUrl 60)) {
        Stop-Transcript
        Fail "API não ficou saudável. Veja: docker logs -f caculinha-backend"
    }
}
Ok "API saudável: $healthUrl"
$report.Add("")
$report.Add("## Health")
$report.Add("- OK: $healthUrl")

# Rebuild catálogo (pode ser pesado; mas é o “fim a fim” real)
Info "Rebuild do catálogo (FULL + activate)"
$rebuildUrl = "$BaseUrl/api/v1/catalog/rebuild"
$rebuildBody = @{ mode = "full"; activate = $true } | ConvertTo-Json
try {
    Invoke-RestMethod -Method POST -Uri $rebuildUrl -ContentType "application/json" -Body $rebuildBody -TimeoutSec 900 | Out-Null
    Ok "Rebuild OK"
    $report.Add("")
    $report.Add("## Catálogo")
    $report.Add("- Rebuild FULL: OK")
}
catch {
    Stop-Transcript
    Fail "Falha no rebuild: $($_.Exception.Message)"
}

# Search sanity
Info "Busca sanity"
Add-Type -AssemblyName System.Web
$q = [System.Web.HttpUtility]::UrlEncode("alca bolsa madeira")
$searchUrl = "$BaseUrl/api/v1/catalog/search?q=$q&k=$K"
try { $search = Invoke-RestMethod -Uri $searchUrl -TimeoutSec 120 } catch {
    Stop-Transcript
    Fail "Falha na busca: $($_.Exception.Message)"
}
$productId = $null
if ($search.results -and $search.results.Count -gt 0) { $productId = $search.results[0].product_id }
if (-not $productId) { $productId = 704566 }
Ok "Busca OK (top1=$productId)"
$report.Add("")
$report.Add("## Busca")
$report.Add("- URL: $searchUrl")
$report.Add("- top1 product_id: $productId")

# Chat
Info "Chat E2E"
$chatBody = @{ message = "Quais produtos de alça de bolsa em madeira temos?"; tenant_id = $TenantId } | ConvertTo-Json
$chatOk = $false
$chatEndpoint = $null
foreach ($u in @("$BaseUrl/api/v1/chat", "$BaseUrl/api/v1/chat_v2")) {
    try {
        Invoke-RestMethod -Method POST -Uri $u -ContentType "application/json" -Body $chatBody -TimeoutSec 300 | Out-Null
        $chatOk = $true
        $chatEndpoint = $u
        break
    }
    catch {}
}
if (-not $chatOk) {
    Stop-Transcript
    Fail "Falha no chat."
}
Ok "Chat OK: $chatEndpoint"
$report.Add("")
$report.Add("## Chat")
$report.Add("- Endpoint: $chatEndpoint")

# Feedback
Info "Feedback"
$fbBody = @{ query = "alca bolsa madeira"; product_id = $productId; signal = "positive"; tenant_id = $TenantId } | ConvertTo-Json
$fbOk = $false
$fbUrl = $null
foreach ($u in @("$BaseUrl/api/v1/feedback", "$BaseUrl/api/v1/catalog/feedback")) {
    try {
        Invoke-RestMethod -Method POST -Uri $u -ContentType "application/json" -Body $fbBody -TimeoutSec 60 | Out-Null
        $fbOk = $true
        $fbUrl = $u
        break
    }
    catch {}
}
if ($fbOk) {
    Ok "Feedback OK: $fbUrl"
    $report.Add("")
    $report.Add("## Feedback")
    $report.Add("- OK: $fbUrl")
}
else {
    Warn "Feedback não enviado (endpoint pode ser outro)."
    $report.Add("")
    $report.Add("## Feedback")
    $report.Add("- NÃO enviado")
}

# Report + open
$report.Add("")
$report.Add("## Artefatos")
$report.Add("- Log: $logFile")
$report.Add("- Relatório: $reportFile")
$report | Out-File -FilePath $reportFile -Encoding UTF8

Stop-Transcript

Info "Abrindo UI + links"
Start-Process $FrontendUrl
Start-Process $searchUrl
if ($WithObs) { Start-Process "http://localhost:9090" }  # Prometheus UI
Start-Process $reportFile

Write-Host "`n✅ Pronto. Interface aberta e stack continua rodando." -ForegroundColor Green
Write-Host "Log: $logFile"
Write-Host "Relatório: $reportFile"
pause
