param(
    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$quarantineRoot = Join-Path $repoRoot "legacy_quarantine/cleanup-2026-04-02"

$items = @(
    "frontend-solid/package-lock.json",
    "backend/api",
    "backend/scripts/backend/data/parquet/admmat.parquet",
    "backend/scripts/data/parquet/admmat.parquet",
    "backend/scripts/maintenance/analyze_parquet.py",
    "backend/scripts/maintenance/analyze_store_1685.py",
    "backend/scripts/maintenance/audit_parquet_columns.py",
    "backend/scripts/maintenance/benchmark_duckdb_vs_polars.py",
    "backend/scripts/maintenance/benchmark_llm.py",
    "backend/scripts/maintenance/check_admin.py",
    "backend/scripts/maintenance/check_product_721754.py",
    "backend/scripts/maintenance/check_segments.py",
    "backend/scripts/maintenance/check_specific_users.py",
    "backend/scripts/maintenance/check_supabase_users.py",
    "backend/scripts/maintenance/clean_corrupted_cache.py",
    "backend/scripts/maintenance/consultar_dados.py",
    "backend/scripts/maintenance/create_admin_supabase.py",
    "backend/scripts/maintenance/create_dummy_parquet.py",
    "backend/scripts/maintenance/create_parquet_users.py",
    "backend/scripts/maintenance/create_restricted_users_supabase.py",
    "backend/scripts/maintenance/create_users.py",
    "backend/scripts/maintenance/diagnostico_auth.py",
    "backend/scripts/maintenance/diagnostico_login_supabase.py",
    "backend/scripts/maintenance/export_columns.py",
    "backend/scripts/maintenance/fix_admin_complete.py",
    "backend/scripts/maintenance/fix_admin_password.py",
    "backend/scripts/maintenance/fix_admin_role.py",
    "backend/scripts/maintenance/fix_admin_segments.py",
    "backend/scripts/maintenance/fix_supabase_admin.py",
    "backend/scripts/maintenance/fix_supabase_admin_clean.py",
    "backend/scripts/maintenance/inspect_parquet.py",
    "backend/scripts/maintenance/inspect_parquet_columns.py",
    "backend/scripts/maintenance/list_columns.py",
    "backend/scripts/maintenance/list_segments.py",
    "backend/scripts/maintenance/purge_all_caches.py",
    "backend/scripts/maintenance/quick_test_seasonality.py",
    "backend/scripts/maintenance/run_chat_prompt_smoke.py",
    "backend/scripts/maintenance/setup_admin_rest.py",
    "backend/scripts/maintenance/setup_supabase_admin.py",
    "backend/scripts/maintenance/sync_supabase_profiles.py",
    "backend/scripts/maintenance/test_anti_repetition.py",
    "backend/scripts/maintenance/test_continuous_learning.py",
    "backend/scripts/maintenance/test_db_connection_headless.py",
    "backend/scripts/maintenance/test_graph_fix.py",
    "backend/scripts/maintenance/test_integration.py",
    "backend/scripts/maintenance/test_login.py",
    "backend/scripts/maintenance/test_oxford_query.py",
    "backend/scripts/maintenance/test_product_analysis_fix.py",
    "backend/scripts/maintenance/test_produto_721754.py",
    "backend/scripts/maintenance/test_seasonality_integration.py",
    "backend/scripts/maintenance/test_windows_auth.py",
    "backend/scripts/maintenance/validate_linha_verde.py",
    "backend/scripts/maintenance/validate_modernization.py",
    "backend/scripts/maintenance/validate_schema_knowledge.py",
    "backend/scripts/maintenance/verify_metrics.py",
    "backend/scripts/maintenance/verify_oxford_chamex.py",
    "backend/scripts/maintenance/verify_parquet_data.py",
    "backend/scripts/maintenance/verify_system_fixes.py",
    "docs/historico",
    "docs/mockups",
    "docs/APRESENTACAO_EXECUTIVA_CACULINHA_BI.html",
    "docs/CHAT_FRONTEND_ROBUSTNESS.md",
    "docs/CHAT_IMPLEMENTATION_CHECKLIST.md",
    "docs/CHAT_TESTING_STACK.md",
    "docs/CHAT_UPDATE_REVIEW_2026.md",
    "docs/CHATBI_AGENT_CAPABILITY_PLAN.md",
    "docs/CHATBI_FASE3_RUNBOOK_CANARY_ROLLBACK.md",
    "docs/CHATBI_FASE8_CHECKLIST_PRE_PRODUCAO.md",
    "docs/CHATBI_GO_LIVE_EXECUCAO_TEMPLATE.md",
    "docs/CHATBI_GO_LIVE_MATRIZ.md",
    "docs/CHATBI_SPRINT6_GO_LIVE_RUNBOOK.md",
    "docs/CHATBI_UAT_CENARIOS_NEGOCIO.md",
    "docs/CHATBI_UAT_EXECUCAO_HOMOLOG_TEMPLATE.md",
    "docs/HOMOLOGACAO_EMPRESA_CHECKLIST.md",
    "docs/monitoramento-dashboard-repaginacao-plan.md",
    "chatbi-55a787a8-7457-4e62-8348-2e04529c722c.md",
    "csv_basket_realista_baseado_no_parquet_12000_linhas.csv",
    "START_BACKEND_DEV.bat"
)

foreach ($item in $items) {
    $source = Join-Path $quarantineRoot $item
    $destination = Join-Path $repoRoot $item

    if (-not (Test-Path $source)) {
        Write-Host "SKIP source missing: $item"
        continue
    }

    $destinationParent = Split-Path -Parent $destination
    if ($destinationParent -and -not (Test-Path $destinationParent)) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }

    if ((Test-Path $destination) -and -not $Overwrite) {
        Write-Host "SKIP destination exists: $item (use -Overwrite to force)"
        continue
    }

    Move-Item -LiteralPath $source -Destination $destination -Force
    Write-Host "RESTORED $item"
}

Write-Host ""
Write-Host "Restauracao concluida."
Write-Host "Itens regeneraveis removidos na limpeza original continuam dependendo de recriacao manual:"
Write-Host "- .venv -> python -m venv .venv"
Write-Host "- frontend-solid/node_modules -> bun install"
Write-Host "- frontend-solid/dist -> bun run build"
Write-Host "- playwright-report/test-results/logs/caches -> recriados por testes/build/runtime"
