# Matriz de Classificação — Descomissionamento Controlado

**Projeto:** Caculinha BI Enterprise AI Platform  
**Data:** 2026-02-07  
**Agente:** Project Planner

---

## Legenda de Classificação

| Status | Descrição | Ação |
|--------|-----------|------|
| **KEEP_CORE** | Parte da nova arquitetura | Não mexer |
| **KEEP_SUPPORT** | Docs úteis, scripts atuais | Não mexer |
| **MOVE_TO_LEGACY** | Docs históricos não essenciais | Mover para `docs/legacy/` |
| **QUARANTINE** | Dúvida ou dependência indireta | Mover para `legacy_quarantine/` |
| **REMOVE** | Comprovadamente inútil | Remover |

---

## 1. BACKEND — Logs (20 arquivos)

| Arquivo | Classificação | Motivo | Risco |
|---------|---------------|--------|-------|
| `backend/logs/api/api.log` | **REMOVE** | Log operacional 3.4MB | Nenhum |
| `backend/logs/app/app.log` | **REMOVE** | Log operacional 1.6MB | Nenhum |
| `backend/logs/audit/audit.log` | **REMOVE** | Log de auditoria antigo | Nenhum |
| `backend/logs/chat/chat.log` | **REMOVE** | Log de chat vazio | Nenhum |
| `backend/logs/errors/*.log` | **REMOVE** | Logs de erro antigos | Nenhum |
| `backend/logs/security/*.log` | **REMOVE** | Logs de segurança antigos | Nenhum |
| `backend/logs/agent.log` | **REMOVE** | Log de agente | Nenhum |
| `backend/*.log` (raiz) | **REMOVE** | Logs diversos (startup, debug, etc) | Nenhum |

**Validação:** `pytest backend/tests/` não depende de logs.

---

## 2. BACKEND — Scripts Debug (10 arquivos)

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `backend/scripts/debug_archive/*` | **REMOVE** | Scripts debug arquivados (8 arquivos) |

**Validação:** Pasta `debug_archive` não é importada.

---

## 3. BACKEND — Testes Legados (50+ arquivos)

| Pasta | Classificação | Motivo |
|-------|---------------|--------|
| `backend/tests/archive/` | **QUARANTINE** | Testes antigos, podem ter valor documental |
| `backend/tests/archive/legacy/` | **QUARANTINE** | Testes muito antigos |

**Validação:** `pytest backend/tests/test_agents.py test_adapters.py` = 24 passed (não depende de archive)

---

## 4. BACKEND — Testes Ativos (MANTER)

| Pasta | Classificação | Motivo |
|-------|---------------|--------|
| `backend/tests/test_agents.py` | **KEEP_CORE** | Testes atuais |
| `backend/tests/test_adapters.py` | **KEEP_CORE** | Testes atuais |
| `backend/tests/conftest.py` | **KEEP_CORE** | Configuração pytest |
| `backend/tests/integration/` | **KEEP_SUPPORT** | Testes de integração |
| `backend/tests/unit/` | **KEEP_SUPPORT** | Testes unitários |
| `backend/tests/e2e/` | **KEEP_SUPPORT** | Testes E2E |

---

## 5. BACKEND — Sessions e Data Legado

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `backend/app/data/sessions/legacy.json` | **REMOVE** | Session legada |
| `backend/app/core/agents/DEPRECATED_README.md` | **MOVE_TO_LEGACY** | Doc deprecated |

---

## 6. DOCS — Classificação

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `docs/DEBUG_REPORT.md` | **MOVE_TO_LEGACY** | Relatório debug antigo |
| `docs/DEBUG_RESPOSTA_VAZIA.md` | **MOVE_TO_LEGACY** | Relatório debug antigo |
| `docs/archive/test_results.txt` | **REMOVE** | Resultados de teste antigos |

---

## 7. .AGENT — Antigravity Kit (MANTER)

| Pasta | Classificação | Motivo |
|-------|---------------|--------|
| `.agent/skills/*` | **KEEP_CORE** | Skills ativas |
| `.agent/agents/*` | **KEEP_CORE** | Agentes ativos |
| `.agent/tests/*` | **KEEP_SUPPORT** | Testes do kit |

> ⚠️ Os arquivos `test_fase*.py` são parte do Antigravity Kit, NÃO remover.

---

## 8. ARQUIVOS NÃO TRACKEADOS (Novos)

| Arquivo | Classificação | Motivo |
|---------|---------------|--------|
| `docs/allowed_structure.txt` | **KEEP_SUPPORT** | Estrutura oficial |
| `docs/cleanup_baseline.md` | **KEEP_SUPPORT** | Baseline limpeza |
| `docs/final_cleanup_report.md` | **KEEP_SUPPORT** | Relatório anterior |
| `docs/inventory_*.md` | **KEEP_SUPPORT** | Inventários |
| `docs/orphans.txt` | **KEEP_SUPPORT** | Lista órfãos |
| `docs/purge_log_*.txt` | **KEEP_SUPPORT** | Logs de purge |
| `docs/security_review_orphans.md` | **KEEP_SUPPORT** | Review segurança |
| `tools/*.py` | **KEEP_SUPPORT** | Scripts atuais |

---

## 9. ARQUIVOS DELETADOS (183 — Confirmar)

Os 183 arquivos marcados com `D` no git status já foram removidos na limpeza anterior. Confirmar commit.

---

## Resumo Quantitativo

| Classificação | Quantidade |
|---------------|------------|
| **KEEP_CORE** | ~50 |
| **KEEP_SUPPORT** | ~30 |
| **MOVE_TO_LEGACY** | 4 |
| **QUARANTINE** | ~40 (testes archive) |
| **REMOVE** | ~30 (logs + debug scripts) |
| **JÁ DELETADOS** | 183 |

---

## Plano de Execução (FASE 3)

1. Criar `docs/legacy/` e mover docs históricos
2. Criar `legacy_quarantine/` e mover `backend/tests/archive/`
3. Remover logs e scripts debug
4. Executar gates de validação
5. Commit das alterações

---

**FASE 2 COMPLETA — AGUARDANDO APROVAÇÃO PARA FASE 3**
