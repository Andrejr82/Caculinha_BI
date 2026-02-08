# PLAN: Backend Stabilization Cycle

Este plano detalha o ciclo completo de estabilização do backend da plataforma Caculinha BI, focando em portabilidade nativa (Windows), reprodutibilidade de dependências e limpeza de dívida técnica arquitetural.

## Problema

1. **Dependências Implícitas:** O backend utiliza bibliotecas como `Whoosh` que não estão declaradas no `requirements.txt`, causando quebras em tempo de execução.
2. **Ambiente Não-Determinístico:** A falta de um lockfile (`requirements.txt` gerado por `pip-tools`) torna o ambiente vunerável a mudanças em sub-dependências.
3. **Dualidade Arquitetural:** Existe uma estrutura espelhada e redundante entre `backend/app/...` e pacotes na raiz de `backend/` (ex: `backend/api` vs `backend/app/api`).
4. **Artefatos Legados:** Presença de scripts de diagnóstico e arquivos órfãos que poluem o repositório.

## Mudanças Propostas

### 1. Estabilização de Dependências (Fase 2 & 3)

#### [NEW] [requirements.in](file:///C:/Projetos_BI/BI_Solution/backend/requirements.in)
- Declarar dependências diretas de alto nível.
- Incluir `Whoosh`, `pip-tools` e `structlog`.

#### [MODIFY] [requirements.txt](file:///C:/Projetos_BI/BI_Solution/backend/requirements.txt)
- Gerar via `pip-compile`.
- Fixar TODAS as versões recursivamente.

### 2. Sincronização de Ambiente (Fase 3)

#### [NEW] [bootstrap_backend.ps1](file:///C:/Projetos_BI/BI_Solution/scripts/bootstrap_backend.ps1)
#### [NEW] [bootstrap_backend.bat](file:///C:/Projetos_BI/BI_Solution/scripts/bootstrap_backend.bat)
- Automação de setup: `python -m venv .venv`, `pip install pip-tools`, `pip-sync`.
- Garantir que o ambiente local seja IDÊNTICO ao definido no lockfile.

### 3. Consolidação Arquitetural (Fase 3)

#### [MODIFY] [main.py](file:///C:/Projetos_BI/BI_Solution/backend/main.py)
- Ajustar imports para priorizar os pacotes na raiz de `backend/` onde houver duplicidade.
- Preparar a remoção do diretório `backend/app` movendo os componentes de observabilidade e config que ainda residem lá.

### 4. Limpeza de Legados (Fase 3 - APÓS SUCESSO)

#### [DELETE] [backend/app](file:///C:/Projetos_BI/BI_Solution/backend/app) (SANEAMENTO GRADUAL)
- Mover `config/settings.py` e `core/observability` para a raiz do `backend/`.
- Remover o diretório `app/` redundante.

#### [DELETE] [Scripts de Diagnóstico](file:///C:/Projetos_BI/BI_Solution/backend/)
- Remover arquivos como `check_columns.py`, `diagnose_cols.py`, etc., movendo-os para `docs/archive` se forem importantes.

## Plano de Verificação

### Automated Tests
- Criar `scripts/verify_dependencies.py` para validar imports em tempo de execução.
- Rodar `pip check` via script de bootstrap.

### Manual Verification
- Executar `python -m uvicorn backend.main:app` e validar o log de boot "Application startup complete".
- Acessar `/health` e garantir resposta `200 OK`.

## Atribuição de Agentes
- @[.agent/agents/project-planner.md]: Planejamento e acompanhamento.
- @[.agent/agents/backend-specialist.md]: Estabilização de dependências e refatoração de imports.
- @[.agent/agents/debugger.md]: Diagnóstico de quebras de runtime e validação final.
