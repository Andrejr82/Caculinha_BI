# Prevenção de Regressões — Plano de Endurecimento

**Projeto:** Caculinha BI Enterprise AI Platform  
**Data:** 2026-02-07  
**Agente:** Security Auditor

---

## 1. Padrões Proibidos

### Arquivos que NUNCA devem entrar no repositório

| Padrão | Motivo |
|--------|--------|
| `repo_dump*` | Dumps de repositório |
| `backup*` | Arquivos de backup |
| `*_backup*` | Sufixo de backup |
| `*.bak`, `*.old`, `*.orig` | Extensões de backup |
| `*.log` | Logs operacionais |
| `*.dump` | Dumps de dados |
| `*.zip`, `*.rar`, `*.7z` | Arquivos compactados |
| `legacy*`, `deprecated*` | Código morto |
| `migrated*` | Artefatos de migração |
| `*_output.txt`, `*_results.txt` | Outputs de teste |

---

## 2. Pre-Commit Hook (Recomendado)

### Instalação

```bash
pip install pre-commit
```

### Arquivo `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: block-large-files
        name: Block Large Files (>50MB)
        entry: python tools/check_file_size.py
        language: python
        pass_filenames: true
        
      - id: block-forbidden-patterns
        name: Block Forbidden Patterns
        entry: python tools/check_forbidden_patterns.py
        language: python
        pass_filenames: true
        
      - id: block-forbidden-extensions
        name: Block Forbidden Extensions
        entry: bash -c 'for f in "$@"; do case "$f" in *.bak|*.old|*.orig|*.dump|*.zip|*.rar|*.7z) echo "BLOCKED: $f"; exit 1;; esac; done' --
        language: system
        pass_filenames: true
```

---

## 3. CI Gate (Recomendado)

### GitHub Actions Workflow

```yaml
# .github/workflows/cleanup-gate.yml
name: Cleanup Gate

on: [push, pull_request]

jobs:
  validate-repo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Run Deep Inventory
        run: python tools/deep_inventory.py .
      
      - name: Check for Forbidden Patterns
        run: python tools/suspect_patterns_scan.py .
      
      - name: Validate No Suspects
        run: |
          COUNT=$(grep -c "| \`" docs/suspects.md || echo 0)
          if [ "$COUNT" -gt 0 ]; then
            echo "❌ BLOCKED: $COUNT suspicious files detected"
            cat docs/suspects.md
            exit 1
          fi
          echo "✅ No suspicious files"
```

---

## 4. Scripts de Validação Disponíveis

| Script | Propósito | Quando Usar |
|--------|-----------|-------------|
| `tools/deep_inventory.py` | Inventário completo | Antes de releases |
| `tools/suspect_patterns_scan.py` | Detecta padrões proibidos | Em CI/PR |
| `tools/git_untracked_scan.py` | Lista arquivos soltos | Antes de commit |
| `tools/quarantine_apply.py` | Aplica quarentena | Limpeza manual |
| `tools/remove_confirmed.py` | Remoção definitiva | Pós-validação |

---

## 5. Regras de Revisão de PR

### Checklist de Aprovação

- [ ] Nenhum arquivo `*.log` adicionado
- [ ] Nenhum arquivo `*.bak`, `*.old`, `*.orig` adicionado
- [ ] Nenhum arquivo > 50MB
- [ ] Nenhum padrão `backup*`, `legacy*`, `deprecated*`
- [ ] Testes passando (24/24)
- [ ] Nenhum dump de dados versionado

---

## 6. Monitoramento Contínuo

### Comando semanal recomendado

```bash
python tools/deep_inventory.py .
python tools/suspect_patterns_scan.py .
```

Se `docs/suspects.md` listar arquivos, investigue e remova.

---

## 7. Checklist de Aceite Final

| Item | Status |
|------|--------|
| Baseline documentado | ✅ `docs/cleanup_baseline.md` |
| Inventário profundo | ✅ `docs/inventory_full.*` |
| Matriz de classificação | ✅ `docs/classification_matrix.md` |
| Quarentena aplicada | ✅ `docs/quarantine_validation.md` |
| Remoção definitiva | ✅ `docs/removal_log.md` |
| .gitignore atualizado | ✅ `docs/gitignore_update.md` |
| Gates finais verdes | ✅ `docs/final_validation.md` |
| Plano de prevenção | ✅ **Este documento** |

---

**HIGIENIZAÇÃO COMPLETA — REPOSITÓRIO LIMPO**
