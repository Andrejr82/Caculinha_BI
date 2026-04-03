# Caculinha BI Agent Platform

Plataforma de BI conversacional para varejo com backend FastAPI, frontend SolidJS e agentes com ferramentas de analise, grafico e pesquisa concorrencial.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Atualizado em: 2026-04-03

## Convenções de dependências

- Backend: fonte canônica em `backend/requirements.in`, com lock em `backend/requirements.txt`.
- Frontend: Bun como gerenciador padrão, com lock oficial em `frontend-solid/bun.lock`.
- `frontend-solid/package-lock.json` não faz mais parte do fluxo padrão.

## Estado do saneamento e Segurança

- 🛡️ **Hardening de Segurança (03 de Abril de 2026):** Todas as credenciais de banco de dados (`UID`/`PWD`) foram removidas do código-fonte (scripts operacionais e endpoints). O sistema agora exige obrigatoriamente a configuração das variáveis `DB_ALT_*` ou `PYODBC_CONNECTION_STRING` no ambiente.
- O repositório passou por saneamento estrutural em 28 de março de 2026.
- O plano executado está em `docs/PLANO_SANEAMENTO_2026-03-28.md`.
- A auditoria inicial foi preservada em quarentena restaurável em `legacy_quarantine/cleanup-2026-04-02/docs/historico/AUDITORIA_PROFUNDA_PROJETO_2026-03-27.md`.

## O que o sistema faz

- Chat BI com SSE e progresso de execucao por etapa.
- Consulta de dados operacionais (principalmente `admmat.parquet`) com RLS por segmento.
- Geracao de visualizacoes (Plotly) e tabelas.
- Pesquisa concorrencial multi-provedor com quality gate de evidencia.
- Controle de acesso por JWT, tenant, role e escopo de ferramentas.
- API v1 e camada de compatibilidade v2.

## Arquitetura real

### Fluxo de requisicao

1. `backend/main.py` inicializa FastAPI, routers e lifecycle.
2. Middlewares (ordem de entrada efetiva):
   - `ObservabilityMiddleware`
   - `RateLimitMiddleware`
   - `TenantMiddleware`
   - `AuthMiddleware`
3. Endpoints v1 (`/api/v1/...`) e alias v2 (`/api/v2/...`).

### Fluxo do ChatBI (SSE)

1. Frontend solicita token efemero em `POST /api/v1/chat/stream-token`.
2. Frontend abre `EventSource` em `GET /api/v1/chat/stream`.
3. Backend autentica token, restaura contexto de usuario e executa `ChatServiceV3`.
4. O servico delega para `CaculinhaBIAgent`, que escolhe ferramentas por role.
5. Backend envia eventos SSE (`tool_progress`, `text`, `chart`, `final`).
6. Resposta final e historico ficam associados ao `session_id`.

### Camada de dados

- Fonte principal: `backend/data/parquet/admmat.parquet`.
- SQL Server: opcional (`USE_SQL_SERVER=true`).
- Fallback tecnico para persistencia de app: SQLite em `backend/app/data/agentbi.db`.
- RLS por segmento aplicado no acesso ao parquet (`NOMESEGMENTO`) com base no contexto do usuario.

### Market Basket Analysis

- Endpoint dedicado: `POST /api/v1/analytics/basket-analysis`
- Alias v2: `POST /api/v2/analytics/basket-analysis`
- Perguntas de chat como `produtos comprados juntos`, `cross-sell` e `basket analysis` agora passam por um servico analitico proprio.
- O caminho antigo de basket por anexo/manual continua ativo no chat para payloads e arquivos enviados pelo usuario.

Comportamento conservador:

- `real_transactional`: so quando o validador comprova transaction key real e cobertura minima suficiente.
- `subset_transactional_supported`: subset controlado com chave transacional apenas hipotetica ou parcial.
- `unsupported`: retorno padrao quando a base local nao atende aos criterios minimos.

Importante:

- A base principal `admmat.parquet` continua tratada como snapshot analitico.
- A coluna `NOTA` e tratada como hipotese controlada, nunca como verdade global de cesta sem validacao.
- Quando o modo for `unsupported`, o sistema explica claramente o que falta no dado.

Exemplo de request:

```json
{
  "start_date": null,
  "end_date": null,
  "une": null,
  "segment": null,
  "category": null,
  "target_product": null,
  "min_support": 0.01,
  "min_confidence": 0.2,
  "min_lift": 1.0,
  "max_rules": 20
}
```

Exemplo de validacao local:

```bash
python -m pytest backend/tests/unit/test_basket_analysis_service.py backend/tests/unit/test_chat_service_dataset_basket.py backend/tests/integration/test_basket_analysis_endpoint.py -q
```

Documentacao complementar: `docs/BASKET_ANALYSIS.md`

### Seguranca e governanca

- JWT em `Authorization: Bearer`.
- Token efemero de stream para nao expor JWT completo em URL SSE.
- Multi-tenant por `X-Tenant-ID`, `request.state` ou subdominio.
- Escopo de ferramentas por role (`admin`, `analyst`, `viewer`, `guest`).
- Sanitizacao de resposta no chat para reduzir vazamento de termos tecnicos internos.

## Quick start

### Pre-requisitos

- Python 3.11+
- Bun 1.2+
- `backend/.env` valido (copie de `backend/.env.example`)
- Arquivo de dados `backend/data/parquet/admmat.parquet`

### Windows (recomendado)

```bat
START_SYSTEM_V2026.bat
```

O script:

- valida Python e Bun
- cria `backend/.env` a partir de `backend/.env.example` se faltar
- verifica parquet principal
- libera portas 8000/3000
- inicia backend e frontend em janelas separadas

Onde o frontend espera o backend:

- Arquivo: `START_SYSTEM_V2026.bat`
- Linha-chave: chamada `python scripts/wait_for_backend.py`
- Regra: o frontend so inicia depois que esse script retorna sucesso.

Onde ajustar host/porta/timeout dessa espera:

- Arquivo: `scripts/wait_for_backend.py`
- Variaveis para leigo:
  - `BACKEND_HOST`
  - `BACKEND_PORT`
  - `HEALTH_PATH`
  - `DEFAULT_TIMEOUT_SECONDS`

### Execucao manual

Backend:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
$env:WATCHFILES_FORCE_POLLING='true'
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend --reload-include *.py --reload-include .env
```

Frontend:

```powershell
cd frontend-solid
bun install
bun run dev -- --host 127.0.0.1 --port 3000
```

### Docker (backend)

```powershell
docker compose up --build backend
```

## Configuracao de ambiente (`backend/.env`)

Base recomendada: `backend/.env.example`.

Variaveis criticas:

| Variavel | Uso |
|---|---|
| `SECRET_KEY` | obrigatoria, minimo 32 caracteres |
| `LLM_PROVIDER` | `groq`, `grq` ou `mock` (`google`/`gemini` sao aliases legados normalizados para `groq`) |
| `LLM_FALLBACK_PROVIDERS` | cadeia de fallback do runtime (`groq` ou `mock`) |
| `USE_SQL_SERVER` | ativa SQL Server (senao usa fallback local/parquet) |
| `PARQUET_DATA_PATH` | caminho da base principal |
| `RAG_EMBEDDING_MODEL` | modelo vetorial local para retrieval (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` por padrao) |
| `RAG_EMBEDDING_CACHE_DIR` | cache local do modelo de embeddings |
| `RAG_EMBEDDING_LOCAL_FILES_ONLY` | evita download no runtime e exige modelo previamente cacheado |
| `RAG_EMBEDDING_PRELOAD_ON_STARTUP` | tenta validar/precarregar o modelo no boot da API |
| `USE_SUPABASE_AUTH` | liga/desliga fluxo de auth Supabase |
| `RATE_LIMIT_PER_MINUTE` | limite global de requests |

Variaveis de pesquisa concorrencial:

| Variavel | Uso |
|---|---|
| `COMPETITIVE_INTEL_ENABLED` | habilita pesquisa externa |
| `COMPETITIVE_PROVIDER_PRIORITY` | ordem de provedores |
| `COMPETITIVE_HTTP_TIMEOUT_SEC` | timeout por chamada |
| `COMPETITIVE_TOTAL_TIMEOUT_SEC` | timeout total da rodada |
| `COMPETITIVE_MAX_RESULTS` | maximo de itens consolidados |
| `COMPETITIVE_DOMAIN_WHITELIST` | dominios permitidos |
| `COMPETITIVE_MANUAL_FILE` | base manual (CSV/JSON importado) |
| `SERPAPI_API_KEY` | opcional para Google Shopping |

### Embeddings locais do ChatBI

O runtime principal agora usa embeddings locais desacoplados do provider generativo.

Default atual:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- escolhido por ser mais adequado a consultas em portugues do que `all-MiniLM-L6-v2`, mantendo custo operacional razoavel em CPU

Recomendacao de producao:

```powershell
backend/.venv/Scripts/python backend/scripts/maintenance/preload_embedding_model.py --allow-download
```

Depois disso, mantenha em `backend/.env`:

```env
RAG_EMBEDDING_LOCAL_FILES_ONLY=true
RAG_EMBEDDING_PRELOAD_ON_STARTUP=true
```

Assim o backend nao depende de download no primeiro request e o retrieval semantico fica previsivel.
Com o cache local preenchido, o loader agora resolve o snapshot local do Hugging Face e sobe offline de forma determinística no startup.

## API principal

Base:

- `GET /`
- `GET /ping`
- `GET /health`
- `GET /docs`

Auth:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

ChatBI:

- `POST /api/v1/chat/stream-token`
- `GET /api/v1/chat/stream`
- `GET /api/v1/chat/llm/status`
- `POST /api/v1/chat/feedback`

Pesquisa concorrencial (admin):

- `GET /api/v1/competitive/csv-template`
- `POST /api/v1/competitive/import-csv`

Compatibilidade:

- `/api/v2/...` reaproveita routers de `/api/v1/...`.

## Pesquisa concorrencial: comportamento esperado

Ordem padrao de provedores (configuravel):

1. `playwright`
2. `crawler`
3. `websearch`
4. `social`
5. `mercadolivre`
6. `serpapi`
7. `bellart`
8. `manual`

Quality gate por item:

- exige produto e preco validos
- para fonte externa, exige URL + dominio permitido
- descarta evidencias sem confianca minima

Fallback de negocio:

- se nao houver evidencia suficiente, retorna mensagem orientativa de negocio
- evita resposta com dump tecnico de sistema
- pode retornar referencia operacional local para nao quebrar fluxo decisorio

## Frontend

- Stack: SolidJS + Vite + TanStack Query.
- Chat em `frontend-solid/src/pages/Chat.tsx` usando SSE.
- Rotas protegidas por autenticacao e role em `frontend-solid/src/index.tsx`.

## Testes

Backend:

```powershell
pytest backend/tests -q
```

Observacao: `pytest.ini` ignora varias suites por padrao (legacy/e2e/load/unit/integration especificas).

Frontend:

```powershell
cd frontend-solid
bun install --frozen-lockfile
bun run test
bun run test:e2e
```

## Estrutura do repositorio

```text
backend/
  main.py
  app/
    api/
      middleware/
      v1/
      v2/
    config/
    core/
    services/
  data/
frontend-solid/
docs/
scripts/
START_SYSTEM_V2026.bat
docker-compose.yml
```

## Riscos e componentes legados

- `backend/app/api/v1/endpoints/auth_alt.py` contem endpoint alternativo com conexao pyodbc e credenciais hardcoded.
- Esse endpoint deve ficar desabilitado fora de ambiente controlado.
- O projeto ainda possui coexistencia de fluxos novos e legados; valide rotas e provider LLM antes de ir para producao.

## Documentacao complementar

- `docs/SYSTEM_OVERVIEW.md`
- `docs/ONBOARDING_7_DIAS.md`
- `docs/CHATBI_PESQUISA_CONCORRENCIAL.md`
- `docs/CHATBI_IMPLEMENTACAO_FASES.md`
- `docs/PLAYGROUND_BI_RUNBOOK.md`
- `docs/CHATBI_PRECISION_PLAYBOOK.md`
- `docs/CHATBI_TOOL_CONTRACTS.md`
- `docs/CHATBI_TEST_CASES.md`
- `docs/CHATBI_CONTEXT7_RUNBOOK.md`
- `docs/adr/ADR-001-fallback-local-playground.md`
- `docs/adr/ADR-002-router-rules-first.md`
- `docs/adr/ADR-003-risk-guardrails-playground.md`

## Licenca

MIT. Consulte `LICENSE`.
