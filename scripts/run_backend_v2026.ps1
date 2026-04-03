param(
    [string]$RepoRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent $ScriptDir
}

$pythonPath = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    throw "Python do backend nao encontrado em $pythonPath"
}

$env:PYTHONPATH = $RepoRoot
$env:RAG_EMBEDDING_LOCAL_FILES_ONLY = "true"
$env:RAG_EMBEDDING_PRELOAD_ON_STARTUP = "true"

Set-Location $RepoRoot
& $pythonPath -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
exit $LASTEXITCODE
