# Plano de Correção e Diagnóstico de Imports

**Missão:** Eliminar `ModuleNotFoundError: No module named 'app'` e padronizar imports para `backend.*`.

## Diagnóstico Realizado

1. **Estrutura de Pacotes:**
   - O diretório `backend/` é o pacote raiz.
   - Subdiretórios como `app`, `api`, `services`, `application` já possuem `__init__.py`.
   - O uvicorn é chamado via `backend.main:app`.

2. **Detecção de Conflitos:**
   - Arquivos dentro de `backend/app/...` usam `from app...` o que causa o erro quando executados via namespace `backend`.
   - Existem scripts legados em `backend/tests` que tentam reforçar o PATH manualmente.

## Decisão de Arquitetura

- **Padrão Único:** Todos os imports internos devem ser relativos ao pacote `backend`.
  - Correto: `from backend.app.core.settings import settings`
  - Incorreto: `from app.core.settings import settings`

## Plano de Ação

1. **Mapeamento:** Identificar todos os arquivos que usam `from app`, `import app`, `from api`, `from services` etc.
2. **Substituição:** Aplicar regex massiva para prefixar com `backend.`.
3. **Saneamento:** Remover referências a `sys.path.append` que tentam "ajudar" o import legacy.
4. **Scripts Globais:** Atualizar `main.py` e scripts de execução nativa.

## Verificação

- Script `scripts/verify_imports.py` para varredura estática e dinâmica (importlib).

---
*Assinado: Equipe de Engenharia BI (Antigravity)*
