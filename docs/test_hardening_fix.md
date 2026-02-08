# Test Hardening Fix — Relatório de Correção

**Projeto:** Caculinha BI Enterprise AI Platform  
**Data:** 2026-02-07

---

## FASE 1: Correção da Coleta do Pytest

### Problema

O pytest estava coletando scripts em `backend/scripts/` que têm nomes `test_*.py` mas não são testes unitários — são scripts manuais de diagnóstico/verificação.

**Scripts incorretamente coletados:**
- `backend/scripts/test_product_analysis_fix.py`
- `backend/scripts/test_anti_repetition.py`
- `backend/scripts/test_continuous_learning.py`
- ... (11 arquivos total)

### Solução Aplicada: SOLUÇÃO A (pytest.ini na raiz)

Criado `pytest.ini` na raiz do repositório com:

```ini
[pytest]
testpaths = backend/tests

norecursedirs = 
    backend/scripts
    legacy_quarantine
    frontend-solid
    node_modules
    .git
    .venv
    docs
    tools
    .agent
```

### Resultado

```
============== 24 passed in 3.61s ==============
```

| Métrica | Valor |
|---------|-------|
| Testes coletados | 24 |
| Testes passados | 24 |
| Scripts excluídos | ✅ |

---

## FASE 2: Tool Input Normalization

*(Pendente — aguardando aprovação)*

### Problema Identificado

A tool `consultar_dados_flexivel` aceita apenas strings no schema Pydantic, mas o código interno pode chamar com `dict`, `list` ou `int`.

### Solução Proposta

Implementar normalização de inputs:
- `filtros: Union[str, dict]`
- `colunas: Union[str, list[str]]` 
- `limite: Union[str, int]`

---

## FASE 3: Testes de Regressão

*(Pendente — aguardando aprovação)*

---

## Checklist

- [x] pytest.ini criado na raiz
- [x] backend/scripts não é coletado
- [ ] consultar_dados_flexivel aceita dict/list/int
- [ ] Testes de regressão criados
- [x] pytest passa (24/24)

---

**FASE 1 COMPLETA — GATES VERDES**
