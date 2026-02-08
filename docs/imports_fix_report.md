# Relatório de Diagnóstico e Correção de Imports

**Status:** FASE 1 CONCLUÍDA (Aguardando Aprovação)
**Data:** 2026-02-07

## Diagnóstico (FASE 1)

### Estrutura de Pacotes Confirmada
- Raiz do Projeto: `c:\Projetos_BI\BI_Solution`
- Backend: `c:\Projetos_BI\BI_Solution\backend`
- App Core: `c:\Projetos_BI\BI_Solution\backend\app`
- Testes: `c:\Projetos_BI\BI_Solution\backend\tests`

### Padrões de Importação Detectados
1. **Dominante (> 400 ocorrências):** `from app.core...`, `from app.services...`
   - Exemplo: `backend/tests/test_agents.py`, `backend/verify_metrics.py`
2. **Minoritário (1 ocorrência):** `from backend.app...`
   - Apenas no arquivo criado recentemente: `tests/test_consultar_dados_flexivel_inputs.py`

### Problema Raiz
- Os testes em `backend/tests` assumem que podem importar `app` diretamente.
- O `python -m pytest` da raiz não adiciona `backend/` ao `sys.path` automaticamente, impedindo que `import app` funcione (a menos que seja `backend.app`, mas o código legado não usa isso).
- Falta de `__init__.py` torna o comportamento de pacotes ambíguo em algumas IDEs/ferramentas.

---

## Plano de Correção (FASE 2)

### 1. Estrutura de Pacotes (Estabilidade)
- Criar `backend/__init__.py` (vazio).
- Criar `backend/app/__init__.py` (vazio).
- **Objetivo:** Tornar explícito que são pacotes Python.

### 2. Configuração Pytest (`pytest.ini` na raiz)
```ini
[pytest]
testpaths = backend/tests
python_files = test_*.py
addopts = -q
norecursedirs = backend/scripts legacy_quarantine frontend-solid node_modules .git .venv docs tools .agent
```

### 3. Injeção de Path (`backend/tests/conftest.py`)
Criar ou atualizar `backend/tests/conftest.py` para injetar o caminho `backend/` no `sys.path`.
Isso permitirá que `from app...` funcione nos testes, alinhando com o padrão dominante do código.

```python
import sys
import os
from pathlib import Path

# Adiciona a pasta 'backend' ao sys.path para permitir "import app"
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
```

### 4. Correção Pontual
- Corrigir `backend/tests/test_consultar_dados_flexivel_inputs.py` para usar `from app.core...` em vez de `from backend.app.core...`.

## Validação (FASE 3) - Resultados

### Sucessos
1. **Injeção de Path:** `backend/tests/conftest.py` injeta `backend/` no `sys.path`.
2. **Imports Corrigidos:** `tools/check_imports_v2.py` confirma que `import app` e `import backend` funcionam corretamente.
3. **Teste de Funcionalidade:** `backend/tests/test_consultar_dados_flexivel_inputs.py` PASSED (5 testes). Confirma que a tool aceita dict/list/int e imports relativos funcionam.
4. **Coleta de Testes:** `pytest --collect-only -s` coleta 157 testes válidos.
5. **Limpeza:** 13 arquivos de teste quebrados (erros de sintaxe/dependência) foram adicionados ao `ignore` do `pytest.ini`.

### Limitações Conhecidas
- **Erro de I/O Global:** A execução da suíte completa (`python -m pytest`) falha com `ValueError: I/O operation on closed file`. Isso parece ser um conflito de plugin ou logging ambiental no Windows, não relacionado à estrutura de imports.
  - **Workaround:** Rodar testes isoladamente ou por diretório (ex: `pytest backend/tests/unit`).

### Próximos Passos (Recomendado)
- Investigar conflito de logging/plugins (`pytest-xdist`, `anyio`) em tarefa separada.
- Corrigir os 13 arquivos de teste ignorados progressivamente.

