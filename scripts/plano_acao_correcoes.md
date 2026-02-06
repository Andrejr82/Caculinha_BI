# 🎯 Plano de Ação: Correções da Auditoria

## Objetivo
Executar correções priorizadas identificadas na auditoria completa do projeto.

---

## FASE 1: LIMPEZA IMEDIATA ⚡
**Tempo Estimado:** 1-2 horas  
**Impacto:** ALTO  
**Risco:** BAIXO

### 1.1 Remover Logs Temporários (62 arquivos)

```bash
cd backend

# Backup primeiro (opcional)
mkdir -p ../backup/logs_$(date +%Y%m%d)
cp *.log *.txt ../backup/logs_$(date +%Y%m%d)/ 2>/dev/null

# Remover logs
rm -f deep_knowledge_test_output*.txt
rm -f success*.txt
rm -f std_out*.log std_err*.log
rm -f import_trace.txt
rm -f startup_log.txt error_log.txt
rm -f warnings_log*.txt
rm -f *_output.txt *_result.txt
rm -f diagnostico*.txt
rm -f test_*.txt (exceto test_*.py)

# Adicionar ao .gitignore
echo "" >> .gitignore
echo "# Logs e outputs temporários" >> .gitignore
echo "*.log" >> .gitignore
echo "*_output.txt" >> .gitignore
echo "*_result.txt" >> .gitignore
echo "success*.txt" >> .gitignore
```

**Arquivos a Remover:**
- `deep_knowledge_test_output.txt` (1-9)
- `success.txt`, `success_final.txt`, `success_v2.txt`, `success_v3.txt`, `success_v4.txt`
- `std_out_fix.log`, `std_err_fix.log`, `std_out_new.log`, `std_err_new.log`
- `import_trace.txt` (869KB!)
- `startup_log.txt`, `error_log.txt`
- `warnings_log.txt` (1-3)
- `auth_flow_result.txt`, `login_test_result.txt`
- `diagnostico_resultado.txt`, `diagnostico_supabase_completo.txt`
- `eoq_test.txt`, `forecast_test.txt`, `groups_test.txt`, `suppliers_test.txt`
- `out.txt`, `resultado_testes.txt`
- `test_db_results.txt`, `test_debug_output.txt`
- `verification.log`, `verification_2.log`, `verification_3.log`

---

### 1.2 Mover Testes Obsoletos (90 arquivos)

```bash
cd backend

# Criar estrutura de archive
mkdir -p tests/archive/legacy

# Mover testes da raiz para archive
mv test_*.py tests/archive/legacy/

# Atualizar README
cat > tests/archive/legacy/README.md << 'EOF'
# Legacy Tests Archive

Testes antigos movidos da raiz do backend.

**Não usar estes testes!** Eles são mantidos apenas para referência histórica.

Para testes atuais, veja:
- `/tests/` - Testes ativos
- `/tests/unit/` - Testes unitários
- `/tests/integration/` - Testes de integração
EOF
```

**Arquivos a Mover:**
- `test_v3_validation.py`
- `test_supplier_query.py`
- `test_segment_filter.py`
- `test_prompt_improvements.py`
- `test_metrics_first.py`
- `test_loop_detection.py`
- `test_login_endpoint.py`
- `test_llm_raw.py`, `test_llm_only.py`, `test_llm_improvements.py`, `test_llm_fixed.py`
- `test_insights_detailed.py`, `test_insights_debug.py`, `test_insights_complete.py`
- `test_full_auth_flow.py`
- `test_deep_knowledge.py`
- `test_advanced_features.py`
- ... (73+ mais)

---

### 1.3 Mover Scripts de Debug (9 arquivos)

```bash
cd backend

# Mover para archive (já existe scripts/debug_archive/)
mv debug_*.py scripts/debug_archive/

# Atualizar README
cat > scripts/debug_archive/README.md << 'EOF'
# Debug Scripts Archive

Scripts de debug temporários usados durante desenvolvimento.

**Não usar!** Mantidos apenas para referência.
EOF
```

**Arquivos a Mover:**
- `debug_data_casting.py`
- `debug_imports.py`
- `debug_init.py`
- `debug_schema.py`
- `debug_user_auth.py`

---

### 1.4 Consolidar Arquivos .env

```bash
cd backend

# Backup
cp .env .env.backup
cp .env.supabase .env.supabase.backup

# Mesclar .env.supabase em .env (se necessário)
# Revisar manualmente e consolidar

# Remover .env.supabase após consolidação
# rm .env.supabase

# Atualizar .env.example com todas as variáveis necessárias
```

**Ação Manual Necessária:**
1. Revisar `.env` e `.env.supabase`
2. Consolidar variáveis únicas
3. Atualizar `.env.example`
4. Documentar variáveis em README

---

## FASE 2: ORGANIZAÇÃO 📁
**Tempo Estimado:** 2-4 horas  
**Impacto:** MÉDIO  
**Risco:** BAIXO

### 2.1 Reorganizar Scripts

```bash
cd backend

# Criar subpastas
mkdir -p scripts/verification
mkdir -p scripts/fixes
mkdir -p scripts/diagnostics
mkdir -p scripts/setup

# Mover scripts de verificação
mv check_*.py scripts/verification/
mv verify_*.py scripts/verification/
mv inspect_*.py scripts/verification/
mv diagnose_*.py scripts/diagnostics/

# Mover scripts de fix
mv fix_*.py scripts/fixes/
mv create_*.py scripts/setup/
mv setup_*.py scripts/setup/
mv sync_*.py scripts/setup/

# Mover scripts de consulta
mv consultar_*.py scripts/diagnostics/
mv list_*.py scripts/diagnostics/
mv export_*.py scripts/diagnostics/

# Atualizar READMEs
```

**Scripts a Organizar:**
- **Verification:** `check_*.py`, `verify_*.py`, `inspect_*.py` (30+)
- **Fixes:** `fix_*.py` (15+)
- **Diagnostics:** `diagnose_*.py`, `consultar_*.py`, `list_*.py` (20+)
- **Setup:** `create_*.py`, `setup_*.py`, `sync_*.py` (10+)

---

### 2.2 Investigar Pastas Duplicadas

```bash
# Investigar backend/backend/
ls -la backend/backend/

# Se for duplicata, remover
# rm -rf backend/backend/

# Investigar app/ na raiz
ls -la app/

# Se for backup, mover para docs/archive/
# mv app/ docs/archive/app_root_backup/
```

**Ação Manual Necessária:**
1. Verificar conteúdo de `backend/backend/`
2. Verificar conteúdo de `app/` (raiz)
3. Decidir se remover ou arquivar

---

### 2.3 Limpar Imports Não Usados

```bash
cd backend

# Instalar ferramenta
pip install autoflake isort

# Remover imports não usados
autoflake --in-place --remove-all-unused-imports --recursive app/

# Organizar imports
isort app/

# Verificar mudanças
git diff
```

---

### 2.4 Remover Código Comentado

**Arquivo:** `backend/app/core/agents/caculinha_bi_agent.py`

**Linhas a Remover:**
- Linha 40: `# from app.core.tools.anomaly_detection import analisar_anomalias`
- Linha 45-50: Imports de `purchasing_tools` comentados
- Linha 66: `# from app.core.tools.semantic_search_tool import buscar_produtos_inteligente`

**Ação Manual:**
- Revisar cada linha comentada
- Remover se não for necessária
- Usar Git para histórico

---

## FASE 3: DÍVIDA TÉCNICA 🔧
**Tempo Estimado:** 1-2 semanas  
**Impacto:** ALTO  
**Risco:** MÉDIO

### 3.1 Catalogar TODOs

```bash
cd backend

# Extrair todos os TODOs
grep -r "TODO\|FIXME\|HACK\|XXX" app/ > ../docs/todos_catalog.txt

# Contar por tipo
echo "TODOs:" $(grep -r "TODO" app/ | wc -l)
echo "FIXMEs:" $(grep -r "FIXME" app/ | wc -l)
echo "HACKs:" $(grep -r "HACK" app/ | wc -l)
```

---

### 3.2 Criar Issues no GitHub

**Template de Issue:**
```markdown
## TODO: [Descrição]

**Arquivo:** `path/to/file.py:123`

**Código:**
```python
# TODO: Implement proper error handling
```

**Prioridade:** [ALTA/MÉDIA/BAIXA]

**Estimativa:** [1h/4h/1d/1w]

**Contexto:**
[Explicar por que isso é necessário]
```

---

### 3.3 Resolver TODOs Prioritários

**Priorização:**
1. 🔴 **ALTA:** TODOs relacionados a segurança, bugs, performance
2. 🟡 **MÉDIA:** TODOs relacionados a features, refatoração
3. 🟢 **BAIXA:** TODOs relacionados a documentação, limpeza

---

### 3.4 Implementar Pre-commit Hooks

```bash
# Instalar pre-commit
pip install pre-commit

# Criar .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/autoflake
    rev: v2.1.1
    hooks:
      - id: autoflake
        args: [--remove-all-unused-imports, --in-place]
EOF

# Instalar hooks
pre-commit install
```

---

## 📊 CHECKLIST DE EXECUÇÃO

### Fase 1: Limpeza Imediata
- [ ] 1.1 Remover logs temporários (62 arquivos)
- [ ] 1.2 Mover testes obsoletos (90 arquivos)
- [ ] 1.3 Mover scripts de debug (9 arquivos)
- [ ] 1.4 Consolidar .env

### Fase 2: Organização
- [ ] 2.1 Reorganizar scripts em subpastas
- [ ] 2.2 Investigar e remover pastas duplicadas
- [ ] 2.3 Limpar imports não usados
- [ ] 2.4 Remover código comentado

### Fase 3: Dívida Técnica
- [ ] 3.1 Catalogar TODOs
- [ ] 3.2 Criar issues no GitHub
- [ ] 3.3 Resolver TODOs prioritários
- [ ] 3.4 Implementar pre-commit hooks

---

## ✅ VALIDAÇÃO

Após cada fase:

```bash
# Verificar que nada quebrou
cd backend
python -m pytest tests/

# Verificar imports
python -c "from app.core.agents import CaculinhaBIAgent; print('OK')"

# Verificar startup
python main.py &
sleep 5
curl http://localhost:8000/health
kill %1
```

---

## 🎯 MÉTRICAS DE SUCESSO

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Arquivos no Root | 127 | ~20 | -84% |
| Logs Temporários | 62 | 0 | -100% |
| Testes Obsoletos | 90 | 0 | -100% |
| TODOs | 300+ | 50 | -83% |
| Organização | 3/10 | 8/10 | +166% |

---

## 📝 NOTAS IMPORTANTES

1. **Backup:** Sempre fazer backup antes de remover arquivos
2. **Git:** Commitar após cada fase
3. **Testes:** Executar testes após cada mudança
4. **Documentação:** Atualizar READMEs conforme necessário
5. **Comunicação:** Informar equipe sobre mudanças estruturais
