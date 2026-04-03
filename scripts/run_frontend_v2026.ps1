param(
    [string]$RepoRoot,
    [string]$BunPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent $ScriptDir
}

if (-not $BunPath) {
    $bunCmd = Get-Command bun -ErrorAction SilentlyContinue
    if ($bunCmd) {
        $BunPath = $bunCmd.Source
    }
}

if (-not $BunPath) {
    $wingetBun = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\Oven-sh.Bun_Microsoft.Winget.Source_8wekyb3d8bbwe\bun-windows-x64\bun.exe"
    if (Test-Path $wingetBun) {
        $BunPath = $wingetBun
    }
}

if (-not $BunPath) {
    $profileBun = Join-Path $env:USERPROFILE ".bun\bin\bun.exe"
    if (Test-Path $profileBun) {
        $BunPath = $profileBun
    }
}

if (-not $BunPath) {
    throw "Bun nao encontrado."
}

$frontendRoot = Join-Path $RepoRoot "frontend-solid"
$npmPath = $null
$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npmCmd) {
    $npmPath = $npmCmd.Source
}

function Invoke-FrontendCommand {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments
    )

    Write-Output "[RUNNER] Tentando subir frontend com: $Label"
    Write-Output "[RUNNER] Comando: $FilePath $($Arguments -join ' ')"
    & $FilePath @Arguments
    return $LASTEXITCODE
}

Set-Location $frontendRoot

$attempts = @(
    @{
        Label = "bun run dev"
        FilePath = $BunPath
        Arguments = @("run", "dev", "--", "--host", "127.0.0.1", "--port", "3000")
    },
    @{
        Label = "bun x --bun vite"
        FilePath = $BunPath
        Arguments = @("x", "--bun", "vite", "--host", "127.0.0.1", "--port", "3000")
    }
)

if ($npmPath) {
    $attempts += @{
        Label = "npm run dev"
        FilePath = $npmPath
        Arguments = @("run", "dev", "--", "--host", "127.0.0.1", "--port", "3000")
    }
}

foreach ($attempt in $attempts) {
    $exitCode = Invoke-FrontendCommand -Label $attempt.Label -FilePath $attempt.FilePath -Arguments $attempt.Arguments
    if ($exitCode -eq 0) {
        exit 0
    }

    Write-Output "[RUNNER] Estrategia '$($attempt.Label)' falhou com codigo $exitCode."
}

throw "Todas as estrategias de inicializacao do frontend falharam."
