# Checklist de Entrada em Homologacao

## Objetivo

Validar o `Caculinha_BI` no ambiente da empresa com o menor numero de ambiguidades possivel.
Nesta primeira homologacao, a arquitetura alvo e:

- `Parquet/DuckDB` como fonte analitica principal do negocio
- `SQL Server` apenas para estado transacional do chat
- `Redis` opcional e postergado para uma fase posterior
- anexos como contexto auxiliar, nunca como substituto automatico da base local

## Preenchimento de ambiente

- [ ] Copiar o template `backend/.env.homologacao.example` para o `.env` do servidor e preencher os placeholders reais
- [ ] Confirmar `ENVIRONMENT=staging`
- [ ] Confirmar `CHAT_STATE_BACKEND=sqlserver`
- [ ] Confirmar `CHAT_STATE_SQLITE_FALLBACK_ENABLED=false`
- [ ] Confirmar `DATABASE_URL` do ambiente da empresa apenas para o estado do chat
- [ ] Confirmar `PYODBC_CONNECTION_STRING` do ambiente da empresa apenas para o estado do chat, se o runtime usar ODBC
- [ ] Confirmar `PARQUET_DATA_PATH` apontando para o arquivo corporativo principal
- [ ] Confirmar `PARQUET_FILE_PATH` apontando para o mesmo arquivo ou alias equivalente
- [ ] Confirmar `REDIS_ENABLED=false` e `REDIS_REQUIRED=false` nesta primeira homologacao
- [ ] Confirmar `BACKEND_CORS_ORIGINS`
- [ ] Confirmar `SECRET_KEY`
- [ ] Confirmar `JWT_SECRET`
- [ ] Confirmar `GROQ_API_KEY`
- [ ] Confirmar modelo Groq default de homologacao
- [ ] Se houver canario de modelo, registrar qual sera testado

## Modelo Groq recomendado

### Baseline estavel

- [ ] Manter `GROQ_MODEL_NAME=llama-3.3-70b-versatile`
- [ ] Manter `INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile`
- [ ] Manter `CODE_GENERATION_MODEL=llama-3.3-70b-versatile` se nao houver experimento

### Canario recomendado

- [ ] Testar `GROQ_MODEL_NAME=openai/gpt-oss-120b`
- [ ] Manter `INTENT_CLASSIFICATION_MODEL=llama-3.3-70b-versatile`
- [ ] Opcionalmente testar `CODE_GENERATION_MODEL=openai/gpt-oss-120b`
- [ ] Comparar qualidade da resposta
- [ ] Comparar latencia percebida
- [ ] Comparar estabilidade do fluxo completo
- [ ] So trocar o default se o canario for melhor sem regressao

## Infra local do servidor

- [ ] Confirmar instalacao do `ODBC Driver 18 for SQL Server`
- [ ] Confirmar conectividade com `SQL Server`
- [ ] Confirmar acesso ao arquivo parquet principal
- [ ] Confirmar permissao de escrita em `data/runtime`
- [ ] Confirmar que `Redis` segue desabilitado sem impedir o startup da aplicacao

## Comandos de verificacao inicial

### SQL Server via `sqlcmd`

- [ ] Executar:

```powershell
sqlcmd -S localhost,1433 -U SEU_USUARIO -P SUA_SENHA -d SEU_BANCO -Q "SELECT @@SERVERNAME, DB_NAME()"
```

### Verificacao do Parquet

- [ ] Confirmar no servidor:

```powershell
Test-Path "CAMINHO_DO_PARQUET"
Get-Item "CAMINHO_DO_PARQUET" | Select-Object FullName, Length, LastWriteTime
```

### Backend

- [ ] Executar:

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

- [ ] Confirmar que o startup nao falhou
- [ ] Confirmar no log que `chat_state_backend` esta em `sqlserver` ou `sqlserver_pytds`
- [ ] Confirmar no log que o `analytics_source` e `parquet`

## Endpoints obrigatorios

### Health

- [ ] Testar:

```powershell
curl http://localhost:8000/health
```

- [ ] Esperado:
  - `status=healthy` ou `degraded`, mas sem falha de startup
  - check de banco ativo
  - `analytics_source=parquet`
  - `chat_state_backend=sqlserver`
  - `checks.redis.status=disabled` nesta primeira homologacao

### Diagnostics

- [ ] Testar:

```powershell
curl -H "Authorization: Bearer SEU_TOKEN_ADMIN" http://localhost:8000/api/v1/diagnostics/config
curl -H "Authorization: Bearer SEU_TOKEN_ADMIN" http://localhost:8000/api/v1/diagnostics/db-status
curl -X POST -H "Authorization: Bearer SEU_TOKEN_ADMIN" http://localhost:8000/api/v1/diagnostics/test-connection
```

- [ ] Confirmar:
  - `database_server` correto
  - `database_name` correto
  - `chat_state_backend=sqlserver`
  - `db-status.parquet.analytics_source=parquet`
  - `db-status.parquet.path` correto
  - `db-status.redis.status=disabled`
  - `test-connection.success=true`

## Testes funcionais minimos

### Chat

- [ ] Abrir o frontend
- [ ] Fazer uma pergunta simples
- [ ] Confirmar resposta do agente
- [ ] Confirmar persistencia do historico
- [ ] Reabrir a sessao e confirmar que o historico foi mantido

### Historico e memoria

- [ ] Validar `GET /api/v1/chat/history`
- [ ] Validar `GET /api/v1/memory`
- [ ] Validar `GET /api/v1/memory/{session_id}`

### Basket

- [ ] Perguntar algo como `quais produtos costumam ser comprados juntos`
- [ ] Confirmar que o sistema responde com basket analitico derivado do `.parquet` ou `unsupported` de forma honesta

### Anexos

- [ ] Anexar um CSV de basket
- [ ] Perguntar explicitamente sobre cesta no anexo
- [ ] Confirmar que o anexo foi usado
- [ ] No mesmo chat, pedir um grafico de vendas da base
- [ ] Confirmar que o anexo nao substituiu a base local

### Graficos

- [ ] Pedir um grafico de vendas por produto/loja
- [ ] Confirmar resposta com payload visual quando aplicavel

### Tabela, exportacao e dashboard

- [ ] Pedir uma tabela operacional
- [ ] Confirmar que a resposta traz `table_data` valido ou bloqueio semantico honesto
- [ ] Pedir uma exportacao
- [ ] Confirmar que a resposta traz artefato/export metadata ou bloqueio semantico honesto
- [ ] Pedir um dashboard
- [ ] Confirmar que a resposta traz `dashboard_spec` ou bloqueio semantico honesto

### Validacao de modelo Groq

- [ ] Rodar o fluxo baseline com `llama-3.3-70b-versatile`
- [ ] Rodar o mesmo fluxo com `openai/gpt-oss-120b`
- [ ] Comparar respostas para pergunta simples de chat
- [ ] Comparar respostas para grafico
- [ ] Comparar respostas para basket
- [ ] Comparar respostas com anexo presente
- [ ] Confirmar que nao houve piora de roteamento, formato ou timeout

## SQL Server

- [ ] Confirmar criacao das tabelas:
  - `chat_conversations`
  - `chat_messages`
  - `chat_feedbacks`
- [ ] Confirmar insercao de mensagens apos uso do chat
- [ ] Confirmar insercao de feedback em `chat_feedbacks`
- [ ] Confirmar que nao ha dependencia do `agentbi.db` no fluxo principal do chat

## Parquet

- [ ] Confirmar que consultas de negocio usam o arquivo configurado em `PARQUET_DATA_PATH`
- [ ] Confirmar que o arquivo `.parquet` e somente leitura para analytics
- [ ] Confirmar que sessoes, historico e feedback nao sao gravados em `.parquet`

## Redis

- [ ] Confirmar que `Redis` esta realmente desabilitado nesta primeira homologacao
- [ ] Confirmar que a aplicacao sobe com `REDIS_ENABLED=false`
- [ ] Confirmar que nao houve erro de startup por ausencia de `Redis`

## Testes automatizados recomendados

- [ ] Executar:

```powershell
python -m pytest backend/tests/integration/test_chat_endpoint.py backend/tests/integration/test_chat_history_endpoint.py backend/tests/integration/test_memory_endpoint.py backend/tests/integration/test_health_diagnostics_sqlserver_pytds.py backend/tests/test_chat_service_document_rag.py backend/tests/unit/test_chat_service_dataset_basket.py backend/tests/unit/test_basket_analysis_service.py backend/tests/integration/test_basket_analysis_endpoint.py backend/tests/test_runtime_infra_settings.py -q
```

- [ ] Confirmar suite verde
- [ ] Executar smoke tests de entrada:

```powershell
python -m pytest backend/tests/integration/test_homologation_smoke.py -q
```

- [ ] Confirmar smoke tests verdes

## Cenarios obrigatorios de aprovacao

- [ ] Usuario A nao enxerga historico do usuario B
- [ ] Anexo nao contamina perguntas gerais
- [ ] Pergunta de cesta com anexo funciona
- [ ] Pergunta de grafico com anexo continua usando a base local
- [ ] Pergunta de tabela/exportacao/dashboard nao retorna payload incoerente
- [ ] Feedback de resposta grava sem erro
- [ ] Reinicio do backend nao perde historico persistido no banco

## Aprovacao de entrada

- [ ] SQL Server validado
- [ ] Parquet validado
- [ ] Backend acessivel
- [ ] Frontend acessivel
- [ ] Chat funcional
- [ ] Historico funcional
- [ ] Basket funcional
- [ ] Graficos funcionais
- [ ] Anexos sob controle
- [ ] Testes principais verdes

## Resultado esperado

Se todos os itens acima estiverem marcados, o sistema esta apto para a homologacao funcional multiusuario na empresa.
