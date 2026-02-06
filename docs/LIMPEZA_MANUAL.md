# 🧹 Guia de Limpeza Manual

## ⚠️ Arquivos Bloqueados

Durante a limpeza automatizada, vários arquivos não puderam ser removidos/movidos devido a **permissão negada**.

**Causa:** Arquivos abertos em editores (VS Code, etc) ou processos rodando (backend).

---

## 📋 CHECKLIST DE LIMPEZA MANUAL

### Passo 1: Preparação

```bash
# 1. Fechar TODOS os editores (VS Code, etc)
# 2. Parar o backend se estiver rodando (Ctrl+C)
# 3. Fechar terminais extras
```

### Passo 2: Executar Script de Limpeza

```bash
cd d:\Dev\Agente_BI\BI_Solution
python scripts/cleanup_project.py
```

**Resultado Esperado:** Todos os arquivos removidos/movidos com sucesso.

---

## 🗑️ REMOÇÃO MANUAL (Se Script Falhar)

### Arquivos para Remover

```bash
cd backend

# Logs
del *.log

# Outputs
del *_output.txt
del success*.txt
del deep_knowledge_test_output*.txt

# Temporários
del auth_flow_result.txt
del diagnostico*.txt
del eoq_test.txt
del forecast_test.txt
del groups_test.txt
del groups_output.txt
del suppliers_test.txt
del out.txt
del resultado_testes.txt
del test_db_results.txt
del login_test_result.txt
del import_trace.txt
del startup_log.txt
del error_log.txt
del warnings_log*.txt
del table_structure.txt
del columns_list.txt
```

### Arquivos para Mover

```bash
cd backend

# Criar pasta de archive
mkdir -p tests\archive\legacy
mkdir -p scripts\debug_archive

# Mover testes obsoletos
move test_*.py tests\archive\legacy\

# Mover scripts de debug
move debug_*.py scripts\debug_archive\
```

---

## ✅ VALIDAÇÃO

Após limpeza manual:

```bash
# 1. Verificar imports
cd backend
python -c "from app.core.agents import CaculinhaBIAgent; print('✅ OK')"

# 2. Executar testes
python -m pytest tests/test_flexible_query_limites.py -v

# 3. Verificar startup
python main.py
# (Ctrl+C após ver "Application startup complete")
```

---

## 📊 ARQUIVOS AFETADOS (Lista Completa)

### Logs (9 arquivos)
- `debug_gemini.log`
- `std_err_fix.log`
- `std_err_new.log`
- `std_out_fix.log`
- `std_out_new.log`
- `test_results.log`
- `verification.log`
- `verification_2.log`
- `verification_3.log`

### Outputs (8 arquivos)
- `debug_output.txt`
- `deep_knowledge_test_output.txt`
- `groups_output.txt`
- `test_debug_output.txt`
- `test_improved_output.txt`
- `test_llm_raw_output.txt`
- `test_output.txt`
- `test_varejo_output.txt`

### Success (5 arquivos)
- `success.txt`
- `success_final.txt`
- `success_v2.txt`
- `success_v3.txt`
- `success_v4.txt`

### Deep Knowledge (9 arquivos)
- `deep_knowledge_test_output.txt`
- `deep_knowledge_test_output_2.txt`
- `deep_knowledge_test_output_3.txt`
- ... (até 9)

### Testes Obsoletos (17+ arquivos)
- `test_advanced_features.py`
- `test_deep_knowledge.py`
- `test_full_auth_flow.py`
- `test_insights_complete.py`
- `test_insights_debug.py`
- `test_insights_detailed.py`
- `test_llm_fixed.py`
- `test_llm_improvements.py`
- `test_llm_only.py`
- `test_llm_raw.py`
- `test_login_endpoint.py`
- `test_loop_detection.py`
- `test_metrics_first.py`
- `test_prompt_improvements.py`
- `test_segment_filter.py`
- `test_supplier_query.py`
- `test_v3_validation.py`

### Scripts de Debug (5 arquivos)
- `debug_data_casting.py`
- `debug_imports.py`
- `debug_init.py`
- `debug_schema.py`
- `debug_user_auth.py`

---

## 🎯 IMPACTO ESPERADO

**Antes:**
- 127 arquivos no backend root
- ~1MB de logs temporários
- Estrutura desorganizada

**Depois:**
- ~20 arquivos no backend root
- 0 logs temporários
- Estrutura limpa e organizada

**Melhoria:** -84% de arquivos desnecessários

---

## ⚠️ IMPORTANTE

- ✅ `.gitignore` já atualizado (futuros logs não serão commitados)
- ✅ Estrutura de archive criada
- ✅ READMEs documentados
- ⏳ Arquivos bloqueados precisam limpeza manual

**Não afeta funcionalidade do sistema!**
