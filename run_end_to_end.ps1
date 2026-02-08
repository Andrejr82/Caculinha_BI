param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$TenantId = "lojas_cacula",
  [int]$K = 5
)

$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "`n[INFO] $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

function Invoke-Json($method, $url, $bodyObj = $null) {
  $headers = @{ "Content-Type" = "application/json" }
  $body = $null
  if ($null -ne $bodyObj) { $body = ($bodyObj | ConvertTo-Json -Depth 12) }

  try {
    if ($null -ne $body) {
      return Invoke-RestMethod -Method $method -Uri $url -Headers $headers -Body $body -TimeoutSec 300
    } else {
      return Invoke-RestMethod -Method $method -Uri $url -Headers $headers -TimeoutSec 300
    }
  } catch {
    throw $_
  }
}

function Wait-HttpOk($url, $timeoutSec = 120) {
  $start = Get-Date
  while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
    try {
      $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { return $true }
    } catch { Start-Sleep -Seconds 2 }
  }
  return $false
}

# --- Pre-checks
Info "Validando pré-requisitos"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail "Docker não encontrado no PATH." }
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue) -and -not (docker compose version 2>$null)) {
  Warn "docker-compose não encontrado como comando. Vou tentar 'docker compose'."
}

# --- Docker down/up
Info "Derrubando stack (docker compose down -v)"
try {
  docker compose down -v | Out-Host
} catch {
  try { docker-compose down -v | Out-Host } catch { Warn "Falhou derrubar stack (pode não estar rodando). Continuando..." }
}

Info "Subindo stack (docker compose up -d)"
try {
  docker compose up -d | Out-Host
} catch {
  docker-compose up -d | Out-Host
}

# --- Health
Info "Aguardando API ficar saudável"
$healthUrl = "$BaseUrl/health"
if (-not (Wait-HttpOk $healthUrl 180)) {
  Warn "Health não respondeu em 180s. Tentando rotas alternativas..."
  $alt = "$BaseUrl/api/v1/health"
  if (-not (Wait-HttpOk $alt 60)) {
    Fail "API não ficou saudável. Verifique logs: docker logs <seu_container_backend>"
  } else {
    $healthUrl = $alt
  }
}
Ok "API saudável: $healthUrl"

# --- Metrics
Info "Verificando endpoint de métricas"
$metricsUrl = "$BaseUrl/api/v1/metrics"
if (-not (Wait-HttpOk $metricsUrl 60)) {
  Warn "Não achei /api/v1/metrics. Tentando /metrics..."
  $metricsUrl = "$BaseUrl/metrics"
  if (-not (Wait-HttpOk $metricsUrl 30)) {
    Warn "Sem endpoint de métricas acessível agora. Continuando mesmo assim."
  } else {
    Ok "Métricas OK: $metricsUrl"
  }
} else {
  Ok "Métricas OK: $metricsUrl"
}

# --- Catalog rebuild
Info "Rebuild do Catálogo (FULL + activate=true)"
$rebuildUrl = "$BaseUrl/api/v1/catalog/rebuild"
$rebuildBody = @{
  mode = "full"
  activate = $true
}
try {
  $rebuildResp = Invoke-Json "POST" $rebuildUrl $rebuildBody
  Ok "Rebuild disparado com sucesso."
  $rebuildResp | ConvertTo-Json -Depth 8 | Out-Host
} catch {
  Fail "Falha no rebuild do catálogo em $rebuildUrl. Erro: $($_.Exception.Message)"
}

# --- Catalog search sanity
Info "Teste de busca no catálogo (sanity check)"
$searchQ = [System.Web.HttpUtility]::UrlEncode("alca bolsa madeira")
$searchUrl = "$BaseUrl/api/v1/catalog/search?q=$searchQ&k=$K"
try {
  $searchResp = Invoke-Json "GET" $searchUrl
  Ok "Busca OK."
  $searchResp | ConvertTo-Json -Depth 10 | Out-Host
} catch {
  Fail "Falha na busca do catálogo. URL: $searchUrl. Erro: $($_.Exception.Message)"
}

# --- Chat E2E
Info "Teste end-to-end do Chat (com catálogo + insight)"
# tenta /api/v1/chat e fallback /api/v1/chat_v2
$chatUrlCandidates = @(
  "$BaseUrl/api/v1/chat",
  "$BaseUrl/api/v1/chat_v2"
)

$chatBody = @{
  message   = "Quais produtos de alça de bolsa em madeira temos e quais parecem mais relevantes para compras?"
  tenant_id = $TenantId
}

$chatOk = $false
$chatResp = $null

foreach ($u in $chatUrlCandidates) {
  try {
    $chatResp = Invoke-Json "POST" $u $chatBody
    Ok "Chat OK em: $u"
    $chatOk = $true
    break
  } catch {
    Warn "Falhou chat em $u. Tentando próximo endpoint..."
  }
}

if (-not $chatOk) { Fail "Falha no Chat em todos endpoints testados: $($chatUrlCandidates -join ', ')" }

$chatResp | ConvertTo-Json -Depth 12 | Out-Host

# --- Feedback
Info "Enviando feedback (loop de aprendizado)"
# tenta achar um product_id nos resultados da busca
$productId = $null
try {
  if ($searchResp.results -and $searchResp.results.Count -gt 0) {
    $productId = $searchResp.results[0].product_id
  } elseif ($searchResp.items -and $searchResp.items.Count -gt 0) {
    $productId = $searchResp.items[0].product_id
  }
} catch { }

if (-not $productId) {
  Warn "Não consegui extrair product_id da resposta de busca. Vou usar um id exemplo (704566). Ajuste se necessário."
  $productId = 704566
}

$feedbackUrlCandidates = @(
  "$BaseUrl/api/v1/feedback",
  "$BaseUrl/api/v1/catalog/feedback"
)

$feedbackBody = @{
  query      = "alca bolsa madeira"
  product_id = $productId
  signal     = "positive"
  tenant_id  = $TenantId
}

$fbOk = $false
foreach ($u in $feedbackUrlCandidates) {
  try {
    $fbResp = Invoke-Json "POST" $u $feedbackBody
    Ok "Feedback OK em: $u"
    $fbOk = $true
    $fbResp | ConvertTo-Json -Depth 8 | Out-Host
    break
  } catch {
    Warn "Falhou feedback em $u. Tentando próximo..."
  }
}
if (-not $fbOk) { Warn "Não consegui enviar feedback em nenhum endpoint conhecido. Se o feedback existir com outro path, ajuste no script." }

# --- Final summary
Info "RESUMO FINAL"
Ok "Stack rodando via Docker."
Ok "Health OK."
if (Wait-HttpOk $metricsUrl 2) { Ok "Métricas OK: $metricsUrl" } else { Warn "Métricas não verificadas." }
Ok "Catálogo rebuild executado."
Ok "Busca catálogo OK."
Ok "Chat E2E OK."
if ($fbOk) { Ok "Feedback enviado." } else { Warn "Feedback não enviado (ajuste endpoint se necessário)." }

Write-Host "`n✅ E2E concluído. Próximo passo: abrir métricas e validar impacto em tempo real." -ForegroundColor Green
Write-Host "   Metrics: $metricsUrl"
Write-Host "   Search:  $searchUrl"
