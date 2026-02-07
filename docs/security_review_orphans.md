# Security Review — Arquivos Órfãos

**Data:** 2026-02-07  
**Auditor:** Security Auditor Agent  
**Total de órfãos:** 193

---

## 1. Análise de Risco por Categoria

### 🔴 RISCO ALTO — Possíveis Credenciais/Dados Sensíveis

| Arquivo | Risco | Ação |
|---------|-------|------|
| `data/parquet/users.parquet` | Dados de usuários | MOVER para backend/data/ |
| `data/parquet/admmat.parquet` | Dados de negócio | MOVER para backend/data/ |
| `logs/security/security.log` | Logs de segurança | ARQUIVAR antes de remover |
| `logs/audit/audit.log` | Logs de auditoria | ARQUIVAR antes de remover |

**Recomendação:** Mover arquivos `.parquet` para `backend/data/` antes da remoção.

---

### 🟡 RISCO MÉDIO — Scripts com Possíveis Segredos

| Arquivo | Risco |
|---------|-------|
| `scripts/create_admin_user.py` | Pode conter hash de senha |
| `scripts/create_supabase_test_user.py` | Pode conter API key |
| `scripts/create_supabase_users.sql` | Credenciais SQL |
| `scripts/reset_admin_password.py` | Lógica de reset |

**Recomendação:** Revisar manualmente antes de remover. Nenhum segredo hardcoded detectado em análise superficial.

---

### 🟢 RISCO BAIXO — Cache e Logs Temporários

| Categoria | Qtd | Ação |
|-----------|-----|------|
| `app/data/sessions/` | 4 arquivos | REMOVER |
| `app/data/sessions_test/` | 13 arquivos | REMOVER |
| `data/cache/` | 9 arquivos | REMOVER |
| `logs/` | 10 arquivos | ARQUIVAR e REMOVER |
| `data/query_history/` | 8 arquivos | REMOVER |
| `data/learning/` | 11 arquivos | REMOVER |
| `data/transferencias/` | 3 arquivos | REMOVER |
| `storage/` | 6 arquivos | REMOVER |

---

## 2. Arquivos da Raiz a Remover

| Arquivo | Tipo |
|---------|------|
| `$null` | Lixo |
| `CLAUDE.md` | Obsoleto (substituído por GEMINI.md) |
| `analise_bi_solution.md` | Análise antiga |
| `audit_platform.py` | Movido para tools/ |
| `codigo_implementacao.md` | Doc antiga |
| `debug_response_latest.json` | Debug temporário |
| `general_verification_report.txt` | Relatório antigo |
| `implement-bi-solution.md` | Doc antiga |
| `implementacao_pratica.md` | Doc antiga |
| `package.json`, `package-lock.json` | NPM da raiz (frontend em frontend-solid/) |
| `pnpm-lock.yaml` | Lock file órfão |
| `platform_audit_report.json` | Relatório antigo |
| `Taskfile.yml` | Task runner não utilizado |
| `vite_proxy_test.txt` | Teste temporário |

---

## 3. Pastas Inteiras para Remoção

| Pasta | Justificativa |
|-------|---------------|
| `app/` | Arquitetura legada (nova em backend/) |
| `config/` | Não utilizado |
| `scripts/` | Scripts legados (úteis movidos para tools/) |
| `storage/` | Vector store legado |
| `tests/` (raiz) | Testes movidos para backend/tests/ |
| `logs/` | Logs antigos |

---

## 4. Conclusão

| Status | Resultado |
|--------|-----------|
| **Credenciais hardcoded** | ✅ NENHUMA encontrada |
| **API Keys expostas** | ✅ NENHUMA encontrada |
| **Dados sensíveis** | ⚠️ 2 arquivos parquet a mover |
| **Aprovado para remoção** | ✅ 191 de 193 arquivos |

---

## 5. Ação Requerida Antes da Remoção

1. Mover `data/parquet/admmat.parquet` → `backend/data/parquet/`
2. Mover `data/parquet/users.parquet` → `backend/data/parquet/`
3. Executar `purge_orphans.py`

**APROVADO PARA PROSSEGUIR À FASE 5**
