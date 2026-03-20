param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$Token = "",
    [string]$OutputDir = "docs/release-evidence",
    [string]$PilotRole = "admin",
    [string]$PilotUsername = "usuario.teste",
    [string]$PilotEmail = "usuario.teste@example.com",
    [string]$PilotUserId = "usuario-teste",
    [switch]$RunChecklist,
    [switch]$SkipApiCalls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$targetDir = Join-Path $OutputDir $timestamp
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Payload
    )

    $json = $Payload | ConvertTo-Json -Depth 20
    Set-Content -Path $Path -Value $json -Encoding UTF8
}

function Invoke-OptionalApiGet {
    param(
        [string]$Name,
        [string]$Url
    )

    $result = [ordered]@{
        name = $Name
        url = $Url
        ok = $false
        status_code = $null
        captured_at = (Get-Date).ToString("s")
        payload = $null
        error = $null
    }

    if ([string]::IsNullOrWhiteSpace($Token)) {
        $result.error = "Token nao informado. Colete este endpoint manualmente ou passe -Token."
        return $result
    }

    try {
        $headers = @{
            Authorization = "Bearer $Token"
        }
        $response = Invoke-WebRequest -Uri $Url -Headers $headers -Method Get -ContentType "application/json"
        $result.ok = $true
        $result.status_code = [int]$response.StatusCode
        if ($response.Content) {
            try {
                $result.payload = $response.Content | ConvertFrom-Json -Depth 20
            } catch {
                $result.payload = $response.Content
            }
        }
    } catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        $result.status_code = $statusCode
        $result.error = $_.Exception.Message
    }

    return $result
}

Write-Host "=== ChatBI Release Evidence Pack ===" -ForegroundColor Cyan
Write-Host "Output: $targetDir" -ForegroundColor Gray

if ($RunChecklist) {
    $checklistLog = Join-Path $targetDir "pre_producao_checklist.log"
    Write-Host "`n1) Executando checklist integrado" -ForegroundColor Yellow
    $nativePreferenceVariable = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
    $previousNativePreference = if ($null -ne $nativePreferenceVariable) { $nativePreferenceVariable.Value } else { $null }
    try {
        $global:PSNativeCommandUseErrorActionPreference = $false
        $checklistOutput = cmd /c "powershell -ExecutionPolicy Bypass -File scripts/chatbi_pre_producao_checklist.ps1 2>&1"
        $checklistExitCode = $LASTEXITCODE
        $checklistOutput | Set-Content -Path $checklistLog -Encoding UTF8
        if ($checklistExitCode -ne 0) {
            throw "Checklist integrado retornou codigo $checklistExitCode"
        }
        Write-Host "   - Log salvo em $checklistLog" -ForegroundColor Gray
    } finally {
        if ($null -ne $previousNativePreference) {
            $global:PSNativeCommandUseErrorActionPreference = $previousNativePreference
        } else {
            Remove-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "`n1) Checklist integrado pulado. Use -RunChecklist para anexar o log." -ForegroundColor DarkYellow
}

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    base_url = $BaseUrl
    output_dir = (Resolve-Path $targetDir).Path
    checklist_included = [bool]$RunChecklist
    api_calls_skipped = [bool]$SkipApiCalls
    endpoints = @()
}

if (-not $SkipApiCalls) {
    Write-Host "`n2) Coletando endpoints operacionais" -ForegroundColor Yellow
    $encodedRole = [uri]::EscapeDataString($PilotRole)
    $encodedUsername = [uri]::EscapeDataString($PilotUsername)
    $encodedEmail = [uri]::EscapeDataString($PilotEmail)
    $encodedUserId = [uri]::EscapeDataString($PilotUserId)

    $requests = @(
        @{
            Name = "chat_slo"
            Url = "$BaseUrl/api/v1/admin/dashboard/chat-slo"
        },
        @{
            Name = "chat_capabilities_debug"
            Url = "$BaseUrl/api/v1/chat/capabilities?debug=true&role=$encodedRole&username=$encodedUsername&email=$encodedEmail&user_id=$encodedUserId"
        },
        @{
            Name = "chat_automation_history"
            Url = "$BaseUrl/api/v1/chat/automation/history"
        }
    )

    foreach ($request in $requests) {
        Write-Host "   - $($request.Name)" -ForegroundColor Gray
        $result = Invoke-OptionalApiGet -Name $request.Name -Url $request.Url
        $manifest.endpoints += $result
        Write-JsonFile -Path (Join-Path $targetDir "$($request.Name).json") -Payload $result
    }
} else {
    Write-Host "`n2) Coleta de endpoints pulada. Use sem -SkipApiCalls para anexar evidencias JSON." -ForegroundColor DarkYellow
}

$readmePath = Join-Path $targetDir "README.md"
$readme = @"
# ChatBI Release Evidence Pack

## Gerado em
- $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Base URL
- `$BaseUrl`

## Conteudo esperado
- `manifest.json`
- `pre_producao_checklist.log` (quando `-RunChecklist` for usado)
- `chat_slo.json`
- `chat_capabilities_debug.json`
- `chat_automation_history.json`

## Pendencias manuais
- Anexar evidencias de `403` fora do canary e `200` no piloto.
- Anexar UAT assinado.
- Registrar aprovacoes tecnica, negocio e operacao.
"@
Set-Content -Path $readmePath -Value $readme -Encoding UTF8

Write-JsonFile -Path (Join-Path $targetDir "manifest.json") -Payload $manifest

Write-Host "`nPacote de evidencias gerado." -ForegroundColor Green
Write-Host "Proximo passo: anexar UAT assinado e evidencias do canary real ao diretorio." -ForegroundColor Green
